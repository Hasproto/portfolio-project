# ============================================================
# swc_client.py — the SDK's main client
# Contains the SWCClient class: the "worker" users interact with.
# ============================================================

# --- IMPORTS ---
import httpx                                                  # makes the actual HTTP calls to your API
import swcpy.swc_config as config                             # your SWCConfig class (settings)
from .schemas import League, Team, Player, Performance, Counts  # Pydantic models used to validate API data
from typing import List                                       # lets you write return hints like List[Player]
import backoff                                                # retry-with-backoff library
import logging                                                # Python's built-in logging system

# Logger named after this file ("swcpy.swc_client"). Emits all the debug/error messages below.
logger = logging.getLogger(__name__)


class SWCClient:
    """Interacts with the SportsWorldCentral API.

    This SDK class simplifies using the SWC fantasy football API.
    It supports all the API's functions and returns validated data types.

    Typical usage example:
        client = SWCClient()
        response = client.get_health_check()
    """

    # --- CLASS CONSTANTS: the API's endpoint paths, kept in one place ---
    HEALTH_CHECK_ENDPOINT = "/"
    LIST_LEAGUES_ENDPOINT = "/v0/leagues/"
    LIST_PLAYERS_ENDPOINT = "/v0/players/"
    LIST_PERFORMANCES_ENDPOINT = "/v0/performances/"
    LIST_TEAMS_ENDPOINT = "/v0/teams/"
    GET_COUNTS_ENDPOINT = "/v0/counts/"

    # Base URL for the bulk data files hosted in your GitHub repo.
    # FIXED: replaced the [github ID] placeholder with your real username.
    BULK_FILE_BASE_URL = (
        "https://raw.githubusercontent.com/Hasproto"
        + "/portfolio-project/main/bulk/"
    )

    def __init__(self, input_config: config.SWCConfig):
        """Constructor: reads all settings off the config object the user passed in."""

        # DEBUG logs (only print if log level is DEBUG)
        logger.debug(f"Bulk file base URL: {self.BULK_FILE_BASE_URL}")
        logger.debug(f"Input config: {input_config}")

        # Copy each setting from the config ("hotel check-in form") onto this client
        self.swc_base_url = input_config.swc_base_url            # API web address
        self.backoff = input_config.swc_backoff                  # retry on/off?
        self.backoff_max_time = input_config.swc_backoff_max_time  # max seconds to keep retrying
        self.bulk_file_format = input_config.swc_bulk_file_format  # "csv" or "parquet"

        # Lookup table: data type -> bulk filename (no extension yet)
        self.BULK_FILE_NAMES = {
            "players": "player_data",
            "leagues": "league_data",
            "performances": "performance_data",
            "teams": "team_data",
            "team_players": "team_player_data",
        }

        # If retry is enabled, wrap call_api with auto-retry (exponential backoff + jitter).
        # This is a closure: on_exception(...) returns a function, which is then called on self.call_api.
        if self.backoff:
            self.call_api = backoff.on_exception(
                wait_gen=backoff.expo,                                  # wait 1s, 2s, 4s, 8s...
                exception=(httpx.RequestError, httpx.HTTPStatusError),  # retry only on these errors
                max_time=self.backoff_max_time,                        # give up after this many seconds
                jitter=backoff.random_jitter,                          # add randomness so retries don't cluster
            )(self.call_api)

        # Glue the right file extension onto every bulk filename (dictionary comprehension)
        if self.bulk_file_format.lower() == "parquet":
            self.BULK_FILE_NAMES = {
                key: value + ".parquet" for key, value in self.BULK_FILE_NAMES.items()
            }
        else:
            self.BULK_FILE_NAMES = {
                key: value + ".csv" for key, value in self.BULK_FILE_NAMES.items()
            }

        logger.debug(f"Bulk file dictionary: {self.BULK_FILE_NAMES}")

    # FIXED: re-indented the body to 8 spaces so it matches every other method.
    def call_api(
        self,
        api_endpoint: str,          # which endpoint to hit, e.g. "/v0/players/"
        api_params: dict = None,    # optional query filters, e.g. {"limit": 10}
    ) -> httpx.Response:            # returns the raw HTTP response object
        """The single central method every other method routes through.
        Adds logging + error handling in one place."""

        # Drop any filters whose value is None, so we don't send "?limit=None" to the API
        if api_params:
            api_params = {key: val for key, val in api_params.items() if val is not None}

        try:
            # Context manager: opens the client, runs the call, then cleans up the connection
            with httpx.Client(base_url=self.swc_base_url) as client:
                logger.debug(
                    f"base_url: {self.swc_base_url}, "
                    f"api_endpoint: {api_endpoint}, api_params: {api_params}"
                )
                response = client.get(api_endpoint, params=api_params)  # the actual GET request
                logger.debug(f"Response JSON: {response.json()}")
                return response

        # Server replied with a bad status code (e.g. 404, 500) — it has a status code
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP status error occurred: {e.response.status_code} {e.response.text}"
            )
            raise  # re-raise so the backoff layer can catch it

        # Request never reached the server (network down, timeout) — no status code
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise  # re-raise so the backoff layer can catch it

    # ============================================================
    # ENDPOINT METHODS — the friendly functions users actually call
    # ============================================================

    def get_health_check(self) -> httpx.Response:
        """Checks if the API is running and healthy.

        Returns:
            An httpx.Response with the HTTP status and JSON from the API.
        """
        logger.debug("Entered health check")
        endpoint_url = self.HEALTH_CHECK_ENDPOINT   # the "/" constant
        return self.call_api(endpoint_url)          # route through call_api

    def list_leagues(
        self,
        skip: int = 0,                          # pagination: how many to skip
        limit: int = 100,                       # pagination: max to return
        minimum_last_changed_date: str = None,  # delta query: only items changed since this date
        league_name: str = None,                # filter by league name
    ) -> List[League]:                          # returns a LIST of validated League objects
        """Returns a list of Leagues filtered by the given parameters."""
        logger.debug("Entered list leagues")

        # Bundle the filters into one dict (None values get stripped inside call_api)
        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "league_name": league_name,
        }

        response = self.call_api(self.LIST_LEAGUES_ENDPOINT, params)
        # Raw JSON is a list of dicts -> turn each dict into a validated League object
        return [League(**league) for league in response.json()]

    def get_league_by_id(self, league_id: int) -> League:
        """Returns a single League matching the given league_id."""
        logger.debug("Entered get league by ID")
        # Path parameter: the ID goes INTO the URL, e.g. "/v0/leagues/" + "5" -> "/v0/leagues/5"
        endpoint_url = f"{self.LIST_LEAGUES_ENDPOINT}{league_id}"
        response = self.call_api(endpoint_url)
        # FIXED: return the single object directly (was camelCase responseLeague)
        return League(**response.json())   # one dict -> one object, no list comprehension

    def get_counts(self) -> Counts:
        """Returns a Counts object with totals for each data type in the API."""
        logger.debug("Entered get counts")
        response = self.call_api(self.GET_COUNTS_ENDPOINT)
        # FIXED: return the single object directly (was camelCase responseCounts)
        return Counts(**response.json())

    def list_teams(
        self,
        skip: int = 0,
        limit: int = 100,
        minimum_last_changed_date: str = None,
        team_name: str = None,                  # filter by team name
        league_id: int = None,                  # filter by which league
    ) -> List[Team]:                            # FIXED: added the return type hint
        """Returns a list of Teams filtered by the given parameters."""
        logger.debug("Entered list teams")

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "team_name": team_name,
            "league_id": league_id,
        }
        response = self.call_api(self.LIST_TEAMS_ENDPOINT, params)
        return [Team(**team) for team in response.json()]

    def list_players(
        self,
        skip: int = 0,
        limit: int = 100,
        minimum_last_changed_date: str = None,
        first_name: str = None,                 # filter by player's first name
        last_name: str = None,                  # filter by player's last name
    ) -> List[Player]:                          # FIXED: added the return type hint
        """Returns a list of Players filtered by the given parameters."""
        logger.debug("Entered list players")

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
            "first_name": first_name,
            "last_name": last_name,
        }
        response = self.call_api(self.LIST_PLAYERS_ENDPOINT, params)
        return [Player(**player) for player in response.json()]

    def get_player_by_id(self, player_id: int) -> Player:   # FIXED: added the return type hint
        """Returns a single Player matching the given player_id."""
        logger.debug("Entered get player by ID")
        endpoint_url = f"{self.LIST_PLAYERS_ENDPOINT}{player_id}"
        response = self.call_api(endpoint_url)
        # FIXED: return the single object directly (was camelCase responsePlayer)
        return Player(**response.json())

    def list_performances(
        self,
        skip: int = 0,
        limit: int = 100,
        minimum_last_changed_date: str = None,
    ) -> List[Performance]:                     # FIXED: added the return type hint
        """Returns a list of Performances filtered by the given parameters."""
        logger.debug("Entered list performances")   # FIXED: message said "get performances"

        params = {
            "skip": skip,
            "limit": limit,
            "minimum_last_changed_date": minimum_last_changed_date,
        }
        response = self.call_api(self.LIST_PERFORMANCES_ENDPOINT, params)
        # FIXED: typo "peformance" -> "performance"
        return [Performance(**performance) for performance in response.json()]

    # ============================================================
    # BULK FILE METHODS — download whole datasets from GitHub
    # These use httpx.get() directly (not call_api) because they fetch
    # a raw file from GitHub, not a JSON response from your API.
    # ============================================================

    def get_bulk_player_file(self) -> bytes:    # returns BYTES (files are binary)
        """Returns a bulk file with player data."""
        logger.debug("Entered get bulk player file")
        player_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["players"]
        response = httpx.get(player_file_path, follow_redirects=True)  # follow GitHub's redirects
        if response.status_code == 200:         # 200 = OK
            logger.debug("File downloaded successfully")
            return response.content             # the raw file bytes

    def get_bulk_league_file(self) -> bytes:
        """Returns a bulk file with league data."""   # FIXED: was "CSV file" (could be parquet)
        logger.debug("Entered get bulk league file")
        league_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["leagues"]
        response = httpx.get(league_file_path, follow_redirects=True)
        if response.status_code == 200:
            logger.debug("File downloaded successfully")
            return response.content

    def get_bulk_performance_file(self) -> bytes:
        """Returns a bulk file with performance data."""   # FIXED: was "CSV file"
        logger.debug("Entered get bulk performance file")
        performance_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["performances"]
        response = httpx.get(performance_file_path, follow_redirects=True)
        if response.status_code == 200:
            logger.debug("File downloaded successfully")
            return response.content

    def get_bulk_team_file(self) -> bytes:
        """Returns a bulk file with team data."""   # FIXED: was "CSV file"
        logger.debug("Entered get bulk team file")
        team_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["teams"]
        response = httpx.get(team_file_path, follow_redirects=True)
        if response.status_code == 200:
            logger.debug("File downloaded successfully")
            return response.content

    def get_bulk_team_player_file(self) -> bytes:
        """Returns a bulk file with team-player data."""   # FIXED: was "CSV file"
        logger.debug("Entered get bulk team player file")
        team_player_file_path = self.BULK_FILE_BASE_URL + self.BULK_FILE_NAMES["team_players"]
        response = httpx.get(team_player_file_path, follow_redirects=True)
        if response.status_code == 200:
            logger.debug("File downloaded successfully")
            return response.content