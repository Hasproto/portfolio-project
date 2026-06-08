# Has: SWCClient is the main class in my swcpy SDK. It's the thing that turns "make an HTTP request to my API'" into "call a Python method"
# --- READING SETTINGS FROM OUTSIDE THE CODE ---
# 'os' lets Python read settings stored in your computer's environment
# (like the API address), so you don't hard-code them into the source.
import os

# 'dotenv' reads a file called .env (a plain text file of settings)
# and loads those settings into the environment so 'os' can find them.
from dotenv import load_dotenv

# Actually do the loading. After this line, anything in your .env file
# is available via os.getenv("SETTING_NAME").
load_dotenv()


class SWCConfig:
    """
    This is the "hotel check-in form." The user fills in their preferences
    once here, then hands this object to SWCClient so it knows how to behave.
    """

    # --- DECLARING WHAT SETTINGS THIS FORM HAS ---
    # These are type hints — labels saying "this form has these fields
    # and each one holds this type of data." They don't set values yet.
    swc_base_url: str              # The API's web address (a string of text)
    swc_backoff: bool              # Retry on failure? (True or False)
    swc_backoff_max_time: int      # How many seconds to keep retrying (a number)
    swc_bulk_file_format: str      # Download format: "csv" or "parquet"

    def __init__(
        self,
        swc_base_url: str = None,         # SANE DEFAULT: None — will check the environment
        backoff: bool = True,             # SANE DEFAULT: retry is ON (safe for most users)
        backoff_max_time: int = 30,       # SANE DEFAULT: retry for up to 30 seconds
        bulk_file_format: str = "csv",    # SANE DEFAULT: CSV (most common for data scientists)
    ):
        """
        The constructor — runs exactly once when the user creates SWCConfig().
        Each parameter has a default value after the '=' sign.
        That's "sane defaults" in action: the user can pass nothing and
        everything still works. The 20% who need something different
        override just the setting they care about.
        """

        # --- THE FALLBACK PATTERN (GPS analogy) ---
        # Step 1: Did the user pass the URL directly? Use that.
        # Step 2: No? Check the environment variable. Use that.
        # The 'or' keyword means: "if the left side is empty, try the right side."
        self.swc_base_url = swc_base_url or os.getenv("SWC_API_BASE_URL")

        # Debug line — prints the URL so you can see what was loaded.
        # Helpful during development; you'd remove this in a real release.
        print(f"SWC_API_BASE_URL in SWCConfig init: {self.swc_base_url}")

        # --- FAIL FAST ---
        # If BOTH sources came back empty, stop immediately with a clear message.
        # Better to crash now with "you forgot the URL" than to crash later
        # with a confusing "cannot connect to None" error.
        if not self.swc_base_url:
            raise ValueError(
                "Base URL is required. Set SWC_API_BASE_URL environment variable."
            )

        # --- STORE THE REMAINING SETTINGS ON THIS INSTANCE ---
        # These just save the user's choices (or defaults) so SWCClient
        # can read them later when making API calls.
        self.swc_backoff = backoff
        self.swc_backoff_max_time = backoff_max_time
        self.swc_bulk_file_format = bulk_file_format

    def __str__(self):
        """ 
        Stringigy fucntion to return contents of congif object for logging.
        How this object describes itself when you print() it or write it to a log.
        Without this, printing gives a useless '<object at 0x7f3a...>'.
        With this, you see the actual settings — like a shipping box
        with a label listing its contents instead of just a barcode.
        """
        return (
            f"{self.swc_base_url} {self.swc_backoff} "
            f"{self.swc_backoff_max_time} {self.swc_bulk_file_format}"
        )