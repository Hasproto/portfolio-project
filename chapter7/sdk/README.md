# swcpy software development kit (SDK)

This is the Python SDK to interact with the SportsWorldCentral Football API,
which was created for the book [Hands-On APIs for AI and Data Science](https://handsonapibook.com).

## Installing swcpy
To install this SDK in your environment, execute the following command:

`pip install swcpy@git+https://github.com/Hasproto/portfolio-project#subdirectory=sdk`

## Example usage
This SDK implements all the endpoints in the SWC API, in addition to providing
bulk downloads of the SWC fantasy data in CSV format.

### Setting base URL for the API
The SDK looks for a value of `SWC_API_BASE_URL` in the environment. The preferred
method for setting the base URL is creating a `.env` file in your project directory:

You may also set this as an environment variable, or pass it as a parameter to `SWCConfig()`.

### Example of normal API functions
```python
from swcpy import SWCClient
from swcpy import SWCConfig

config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
client = SWCClient(config)
leagues_response = client.list_leagues()
print(leagues_response)
```

### Example of bulk data functions
The bulk data endpoint returns a bytes object. Example of saving a file locally:

```python
import csv
import os
from io import StringIO

config = SWCConfig()
client = SWCClient(config)

player_file = client.get_bulk_player_file()

# Write the file to disk to verify the download
output_file_path = data_dir + 'players_file.csv'
with open(output_file_path, 'wb') as f:
    f.write(player_file)
```