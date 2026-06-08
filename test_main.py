"""Testing the FastAPI endpoints"""

# TestClient lets us call FastAPI endpoints without running a real server
from fastapi.testclient import TestClient
from main import app

# Create a test client bound to our FastAPI app
client = TestClient(app)


# ─── Health check ──────────────────────────────────────────────────────
def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API health check successful"}


# ─── /v0/players/ ──────────────────────────────────────────────────────
def test_read_players():
    response = client.get("/v0/players/?skip=0&limit=10000")
    assert response.status_code == 200
    assert len(response.json()) == 1018


def test_read_players_by_name():
    response = client.get("/v0/players/?first_name=Bryce&last_name=Young")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0].get("player_id") == 2009


# ─── /v0/players/{player_id} ───────────────────────────────────────────
def test_read_players_with_id():
    response = client.get("/v0/players/1001/")
    assert response.status_code == 200
    assert response.json().get("player_id") == 1001


# ─── /v0/performances/ ─────────────────────────────────────────────────
def test_read_performances():
    response = client.get("/v0/performances/?skip=0&limit=20000")
    assert response.status_code == 200
    assert len(response.json()) == 17306


def test_read_performances_by_date():
    # NOTE: URL must be on one line — book printed a line break that would break it
    response = client.get(
        "/v0/performances/?skip=0&limit=20000&minimum_last_changed_date=2024-04-01"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2711


# ─── /v0/leagues/ ──────────────────────────────────────────────────────
def test_read_leagues_with_id():
    response = client.get("/v0/leagues/5002/")
    assert response.status_code == 200
    assert len(response.json()["teams"]) == 8


def test_read_leagues():
    response = client.get("/v0/leagues/?skip=0&limit=500")
    assert response.status_code == 200
    assert len(response.json()) == 5


# ─── /v0/teams/ ────────────────────────────────────────────────────────
def test_read_teams():
    response = client.get("/v0/teams/?skip=0&limit=500")
    assert response.status_code == 200
    assert len(response.json()) == 20


def test_read_teams_for_one_league():
    response = client.get("/v0/teams/?skip=0&limit=500&league_id=5001")
    assert response.status_code == 200
    assert len(response.json()) == 12


# ─── /v0/counts/ ───────────────────────────────────────────────────────
def test_counts():
    response = client.get("/v0/counts/")
    response_data = response.json()
    assert response.status_code == 200
    assert response_data["league_count"] == 5
    assert response_data["team_count"] == 20
    assert response_data["player_count"] == 1018