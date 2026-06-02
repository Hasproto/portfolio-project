# ============================================================
# FILE: src/swcpy/swc_client.py
# Replace the ENTIRE file with this content.
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
        "https://raw.githubusercontent.com/[github ID]"
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