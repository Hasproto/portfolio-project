# ============================================================
#Providing Rich Functionality
# ============================================================

# --- IMPORTS ---
import httpx                                    # Library that makes the actual HTTP calls
import swcpy.swc_config as config               # Your config class from the last section
from .schemas import League, Team, Player, Performance  # Pydantic models, for validating returned data
from typing import List                         # Lets you write type hints like List[Player]
import backoff                                  # Third-party retry library (add 'backoff' to pyproject.toml deps!)
import logging                                  # Python's built-in logging system

# Create a logger named after this file ("swcpy.swc_client").
# This is what emits the debug/error messages throughout the class.
logger = logging.getLogger(__name__)


class SWCClient:
    """Interacts with the SportsWorldCentral API.

    This SDK class simplifies using the SWC Fantasy Football API.
    It supports all the API's functions and returns validated data types.

    Typical usage example:
        client = SWCClient()
        response = client.get_health_check()
    """

    # --- CLASS CONSTANTS: the API's endpoint paths ---
    # Stored as ALL_CAPS constants in one place. If a path ever changes,
    # you fix it here once instead of hunting through the whole file.
    HEALTH_CHECK_ENDPOINT = "/"
    LIST_LEAGUES_ENDPOINT = "/v0/leagues/"
    LIST_PLAYERS_ENDPOINT = "/v0/players/"
    LIST_PERFORMANCES_ENDPOINT = "/v0/performances/"
    LIST_TEAMS_ENDPOINT = "/v0/teams/"
    GET_COUNTS_ENDPOINT = "/v0/counts/"

    # The base web address where your bulk CSV/Parquet files live on GitHub.
    # >>> REPLACE [github ID] with your GitHub username: Hasproto <
    BULK_FILE_BASE_URL = (
        "https://raw.githubusercontent.com/Hasproto"
        + "/portfolio-project/main/bulk/"
    )

    def __init__(self, input_config: config.SWCConfig):
        """Constructor: reads all settings off the config object the user passed in."""

        # Log the bulk URL and the whole config (only shows if log level is DEBUG)
        logger.debug(f"Bulk file base URL: {self.BULK_FILE_BASE_URL}")
        logger.debug(f"Input config: {input_config}")

        # --- COPY SETTINGS FROM THE CONFIG ("hotel check-in form") ONTO THIS CLIENT ---
        self.swc_base_url = input_config.swc_base_url            # API web address
        self.backoff = input_config.swc_backoff                  # retry on/off?
        self.backoff_max_time = input_config.swc_backoff_max_time  # max seconds to keep retrying
        self.bulk_file_format = input_config.swc_bulk_file_format  # "csv" or "parquet"

        # --- LOOKUP TABLE: data type -> bulk filename (no extension yet) ---
        self.BULK_FILE_NAMES = {
            "players": "player_data",
            "leagues": "league_data",
            "performances": "performance_data",
            "teams": "team_data",
            "team_players": "team_player_data",
        }

        # --- TURN ON RETRY/BACKOFF (only if the user enabled it) ---
        # Wraps call_api with auto-retry: exponential wait + jitter,
        # only on network/HTTP errors, giving up after backoff_max_time seconds.
        #
        #
        # """
        # below there is a pattern called closure. similar to this example:
        # def outer(x):
        #     def inner(y):
        #         return x + y
        # return inner # returning a function that remember (point always to) x.

        # outer(3)(4)
        # same as
         
        # add = outer(3)
        # add(4)
        # You can add more. 3 is remembered by inner
        # add(5)
        #  and so on
               
        # """
        if self.backoff:
            self.call_api = backoff.on_exception(
                wait_gen=backoff.expo,                                  # wait 1s, 2s, 4s, 8s...
                exception=(httpx.RequestError, httpx.HTTPStatusError),  # retry only on these errors
                max_time=self.backoff_max_time,                        # stop after this many seconds
                jitter=backoff.random_jitter,                          # add randomness so retries don't cluster
            )(self.call_api)

        # --- ADD THE FILE EXTENSION TO EVERY FILENAME ---
        # Dictionary comprehension: keep each key, glue ".parquet" or ".csv" onto the value.
        if self.bulk_file_format.lower() == "parquet":
            self.BULK_FILE_NAMES = {
                key: value + ".parquet"
                for key, value in self.BULK_FILE_NAMES.items()
            }
        else:
            self.BULK_FILE_NAMES = {
                key: value + ".csv"
                for key, value in self.BULK_FILE_NAMES.items()
            }

        # Log the final filename dictionary (DEBUG level)
        logger.debug(f"Bulk file dictionary: {self.BULK_FILE_NAMES}")
    # ============================================================
    # Performing Logging
    # ============================================================

    def call_api(self,
        api_endpoint: str,          # which endpoint to hit, e.g. "/v0/players/"
        api_params: dict = None     # optional query filters, e.g. {"limit": 10}; defaults to none
    ) -> httpx.Response:            # type hint: this method returns an HTTP response object
        """Makes API call and logs errors."""

        # --- CLEAN UP THE PARAMETERS ---
        # If filters were passed, rebuild the dict keeping only the ones
        # that actually have a value. Drops any that came in as None,
        # so we don't send meaningless "?limit=None" to the API.
        if api_params:
            api_params = {
                key: val
                for key, val in api_params.items()
                if val is not None
            }

        # --- TRY THE CALL, HANDLE FAILURES ---
        try:
            # Context manager: opens an HTTP client, runs the call,
            # then cleans up the connection automatically (even on error).
            # httpx.Client also pools/reuses connections = more efficient.
            with httpx.Client(base_url=self.swc_base_url) as client:

                # DEBUG log: shows exactly what we're about to send
                # (only prints if the user set log level to DEBUG)
                logger.debug(
                    f"base_url: {self.swc_base_url}, "
                    f"api_endpoint: {api_endpoint}, "
                    f"api_params: {api_params}"
                )

                # The actual GET request
                response = client.get(api_endpoint, params=api_params)

                # DEBUG log: shows the data that came back
                logger.debug(f"Response JSON: {response.json()}")

                return response

        # --- FAILURE TYPE 1: server replied, but with a bad status code ---
        # (e.g. 404 Not Found, 500 Server Error). It HAS a status code.
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP status error occurred: "
                f"{e.response.status_code} {e.response.text}"
            )
            raise   # re-throw so the retry/backoff layer can catch it

        # --- FAILURE TYPE 2: request never reached the server ---
        # (network down, DNS fail, timeout). No status code exists.
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise   # re-throw so the retry/backoff layer can catch it






    # ============================================================
    # Hiding Your API’s Complicated Detai
    # ============================================================

    def get_health_check(self) -> httpx.Response:
        """Checks if the API is running and healthy.

        Use this to confirm the API is up before making bigger calls.

        Returns:
            An httpx.Response with the HTTP status and JSON from the API.
        """
        logger.debug("Entered health check")
        endpoint_url = self.HEALTH_CHECK_ENDPOINT   # the "/" constant defined earlier
        return self.call_api(endpoint_url)          # route through central call_api (gets logging + retry)

    def list_leagues(
        self,
        skip: int = 0,                          # pagination: how many to skip
        limit: int = 100,                       # pagination: max to return
        minimum_last_changed_date: str = None,  # delta query: only items changed since this date
        league_name: str = None,                # filter by league name
    ) -> List[League]:                          # returns a LIST of validated League objects
        """Returns a list of Leagues filtered by the given parameters.

        Calls the v0/leagues endpoint and returns League objects.

        Returns:
            A list of schemas.League objects, one per SWC fantasy league.
        """
        logger.debug("Entered list leagues")

        # Bundle the user's filters into one dictionary
        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "league_name": league_name,
        }

        # Send it through the central method (any None values get stripped inside call_api)
        response = self.call_api(self.LIST_LEAGUES_ENDPOINT, params)

        # Turn the raw JSON (a list of dicts) into a list of validated Pydantic League objects.
        # For each dict, League(**dict) unpacks its key-value pairs into the League constructor.
        # Pydantic validates here — bad data errors out at this line.
        return [League(**league) for league in response.json()]
    # ============================================================
    #  Supporting Bulk Downloads
    # ============================================================    
    def get_bulk_player_file(self) -> bytes:        # returns BYTES, not text — Parquet is binary
        """Returns a bulk file with player data."""
        logger.debug("Entered get bulk player file")

        # Build the full URL: base GitHub URL + the player filename (with .csv or .parquet already attached)
        player_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["players"]

        # NOTE: uses httpx.get() directly, NOT self.call_api().
        # follow_redirects=True handles GitHub's redirects when serving raw files.
        response = httpx.get(player_file_path, follow_redirects=True)

        # 200 = HTTP "OK". Only return the file contents if the download succeeded.
        if response.status_code == 200:
            logger.debug("File downloaded successfully")
            return response.content   # the raw binary contents of the file
        
        