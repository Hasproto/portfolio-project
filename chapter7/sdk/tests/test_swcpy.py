import pytest
from swcpy import SWCClient           # your installed package
from swcpy import SWCConfig
from swcpy.schemas import League, Team, Player, Performance, Counts
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

# =============================   Note.  ===============================
# 
# TESTS FOR THE NEW SDK METHODS
# Every test follows the same 3-part shape, often called
# "Arrange, Act, Assert":
#   1. ARRANGE — set up the config and client (the tools you need)
#   2. ACT     — call the method you're testing
#   3. ASSERT  — check the result is what you expect; fail loudly if not
# A pytest function is recognized as a test simply because its
# name starts with "test_". pytest finds and runs them automatically.
# =======================================================================


def test_get_league_by_id():
    # --- ARRANGE ---
    # Build a config pointing at the LOCAL API. backoff=False means
    # "don't retry on failure" — in a test we WANT a failure to surface
    # immediately, not get silently retried and hidden.
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    # Create the client, handing it the config (the "hotel check-in form").
    client = SWCClient(config)

    # --- ACT ---
    # Call the method under test. 5001 is the league_id we're asking for.
    # >>> Replace 5001 with a league_id that actually exists in your data. <
    league = client.get_league_by_id(5001)

    # --- ASSERT ---
    # get_league_by_id returns ONE object, so we check it's a single League
    # (not a list). isinstance(x, League) asks "is x a League object?"
    # If the API returned bad data, Pydantic would have already errored
    # inside the method — so reaching here with a League proves validation passed.
    assert isinstance(league, League)


def test_get_counts():
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)

    # get_counts takes no arguments — it just hits the /v0/counts/ endpoint.
    counts = client.get_counts()

    # Returns a single Counts object (one summary), so check for that type.
    assert isinstance(counts, Counts)


def test_list_teams():
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)

    # list_teams returns MANY objects, so the result should be a list.
    teams = client.list_teams()

    # First assertion: the result itself is a list.
    assert isinstance(teams, list)
    # Second assertion: every element in that list is a real Team object.
    # We loop through and check each one — proving the list comprehension
    # in list_teams correctly turned each JSON row into a validated Team.
    for team in teams:
        assert isinstance(team, Team)


def test_list_players():
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)

    # Same "list of objects" pattern as test_list_teams, but for players.
    players = client.list_players()

    assert isinstance(players, list)            # the container is a list
    for player in players:
        assert isinstance(player, Player)        # each item is a Player


def test_get_player_by_id():
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)

    # Single-object lookup by ID. 1001 = Aaron Rodgers in the sample data,
    # so this ID should exist. Swap it if your data differs.
    player = client.get_player_by_id(1001)

    # One object expected, so check for a single Player (not a list).
    assert isinstance(player, Player)


def test_list_performances():
    config = SWCConfig(swc_base_url="http://0.0.0.0:8000", backoff=False)
    client = SWCClient(config)

    # Same "list of objects" pattern, for performances.
    performances = client.list_performances()

    assert isinstance(performances, list)
    for performance in performances:
        assert isinstance(performance, Performance)