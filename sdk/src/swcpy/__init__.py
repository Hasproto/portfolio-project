# --- THE FRONT DOOR ---
# These two lines pull SWCClient and SWCConfig up to the package entrance.
# Without this: user writes  from swcpy.swc_client import SWCClient  (needs to know your file names)
# With this:    user writes  from swcpy import SWCClient              (clean, file names hidden)
# The '.' means "from a file in this same folder" (relative import).

from .swc_client import SWCClient
from .swc_config import SWCConfig