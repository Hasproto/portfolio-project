"""Testing SQLAlchemy Helper Functions"""

import pytest
from datetime import date
import crud # crud.py that we created
from database import SessionLocal

# Test date used to verify date-based filtering
# 2,711 of the 17,306 performance rows have last_changed_date >= this
test_date = date(2024, 4, 1)


# ─── Fixture: provides a fresh DB session to each test ──────────────────
@pytest.fixture(scope="function")
def db_session():
    """Opens a session before the test, closes it after."""
    session = SessionLocal()
    yield session            # test runs here, gets the session
    session.close()           # runs after the test, even if it failed


# ─── Tests ──────────────────────────────────────────────────────────────
def test_get_player(db_session):
    """Fetch one player by ID."""
    player = crud.get_player(db_session, player_id=1001)
    assert player.player_id == 1001


def test_get_players(db_session):
    """Filter players by date — all 1,018 players were updated since test_date."""
    players = crud.get_players(db_session, skip=0, limit=10000,
                               min_last_changed_date=test_date)
    assert len(players) == 1018


def test_get_players_by_name(db_session):
    """Filter by first + last name — should return exactly one player."""
    players = crud.get_players(db_session, first_name="Bryce", last_name="Young")
    assert len(players) == 1
    assert players[0].player_id == 2009


def test_get_all_performances(db_session):
    """No date filter — should return all 17,306 performance rows."""
    performances = crud.get_performances(db_session, skip=0, limit=18000)
    assert len(performances) == 17306


def test_get_new_performances(db_session):
    """With date filter — should return only the 2,711 recent performances."""
    performances = crud.get_performances(db_session, skip=0, limit=10000,
                                         min_last_changed_date=test_date)
    assert len(performances) == 2711


def test_get_player_count(db_session):
    """Verify the analytics count query."""
    player_count = crud.get_player_count(db_session)
    assert player_count == 1018