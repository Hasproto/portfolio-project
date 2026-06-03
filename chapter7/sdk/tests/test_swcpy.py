import pytest
from swcpy import SWCClient           # your installed package
from swcpy import SWCConfig
from swcpy.schemas import League, Team, Player, Performance
from io import BytesIO               # treats in-memory bytes like a file
import pyarrow.parquet as pq         # reads Parquet files
import pandas as pd                  # used here to count rows


def test_health_check():
    """Tests health check from SDK"""
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)
    response = client.get_health_check()
    assert response.status_code == 200
    assert response.json() == {"message": "API health check successful"}


def test_list_leagues():
    """Tests get leagues from SDK"""
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)
    leagues_response = client.list_leagues()
    assert isinstance(leagues_response, list)        # it returned a list
    for league in leagues_response:
        assert isinstance(league, League)            # every item is a League object
    assert len(leagues_response) == 5                # exactly 5 leagues


def test_bulk_player_file_parquet():
    """Tests bulk player download - Parquet"""
    config = SWCConfig(bulk_file_format="parquet")
    client = SWCClient(config)
    player_file_parquet = client.get_bulk_player_file()
    player_table = pq.read_table(BytesIO(player_file_parquet))
    player_df = player_table.to_pandas()
    assert len(player_df) == 1018                    # expected number of player records