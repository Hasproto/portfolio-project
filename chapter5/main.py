"""FastAPI program - Chapter 4"""

# ─── Imports ───────────────────────────────────────────────────────────
# Depends: for dependency injection (auto-creates DB sessions)
# FastAPI: the main framework class
# HTTPException: returns HTTP error codes (like 404 Not Found)
from fastapi import Depends, FastAPI, HTTPException

from sqlalchemy.orm import Session
from datetime import date
import crud, schemas
from database import SessionLocal


# ─── App instance ──────────────────────────────────────────────────────
# This single object IS your API. All routes attach to it.
# When you run "uvicorn main:app", Uvicorn looks for this object.
#
# added in chapter 5
#
api_description = """
This API provides read-only access to info from the SportsWorldCentral
(SWC) Fantasy Football API.

The endpoints are grouped into the following categories:

## Analytics
Get information about the health of the API and counts of leagues, teams,
and players.

## Player
You can get a list of NFL players, or search for an individual player by
player_id.

## Scoring
You can get a list of NFL player performances, including the fantasy points
they scored using SWC league scoring.

## Membership
Get information about all the SWC fantasy football leagues and the teams in them.
"""

app = FastAPI(
    description=api_description,
    title="Sports World Central (SWC) Fantasy Football API",
    version="0.1"
)


# ─── Database dependency ───────────────────────────────────────────────
# Every route needs a DB session. Instead of repeating session creation
# in every function, we define it once here and inject it via Depends().
def get_db():
    db = SessionLocal()
    try:
        yield db          # hand the session to the route function
    finally:
        db.close()        # always close, even if the route crashes


# ─── Health check ──────────────────────────────────────────────────────
# Root endpoint — just proves the API is running.
# No database, no schema. Returns a simple JSON message.
@app.get("/")
async def root():
    return {"message": "API health check successful"}


# ─── Players ───────────────────────────────────────────────────────────
# List of players with optional filters (query parameters)
# Example URL: /v0/players/?first_name=Bryce&last_name=Young&limit=10
@app.get("/v0/players/", response_model=list[schemas.Player])
def read_players(skip: int = 0,
                 limit: int = 100,
                 minimum_last_changed_date: date = None,
                 first_name: str = None,
                 last_name: str = None,
                 db: Session = Depends(get_db)):
    players = crud.get_players(db,
                               skip=skip,
                               limit=limit,
                               min_last_changed_date=minimum_last_changed_date,
                               first_name=first_name,
                               last_name=last_name)
    return players


# Single player by ID (path parameter)
# Example URL: /v0/players/1001
@app.get("/v0/players/{player_id}", response_model=schemas.Player)
def read_player(player_id: int,
                db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404,
                            detail="Player not found")
    return player


# ─── Performances ──────────────────────────────────────────────────────
@app.get("/v0/performances/", response_model=list[schemas.Performance])
def read_performances(skip: int = 0,
                      limit: int = 100,
                      minimum_last_changed_date: date = None,
                      db: Session = Depends(get_db)):
    performances = crud.get_performances(db,
                                         skip=skip,
                                         limit=limit,
                                         min_last_changed_date=minimum_last_changed_date)
    return performances


# ─── Leagues ───────────────────────────────────────────────────────────
# Single league by ID
@app.get("/v0/leagues/{league_id}", response_model=schemas.League)
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="League not found")
    return league


# List of leagues
@app.get("/v0/leagues/", response_model=list[schemas.League])
def read_leagues(skip: int = 0,
                 limit: int = 100,
                 minimum_last_changed_date: date = None,
                 league_name: str = None,
                 db: Session = Depends(get_db)):
    leagues = crud.get_leagues(db,
                               skip=skip,
                               limit=limit,
                               min_last_changed_date=minimum_last_changed_date,
                               league_name=league_name)
    return leagues


# ─── Teams ─────────────────────────────────────────────────────────────
@app.get("/v0/teams/", response_model=list[schemas.Team])
def read_teams(skip: int = 0,
               limit: int = 100,
               minimum_last_changed_date: date = None,
               team_name: str = None,
               league_id: int = None,
               db: Session = Depends(get_db)):
    teams = crud.get_teams(db,
                           skip=skip,
                           limit=limit,
                           min_last_changed_date=minimum_last_changed_date,
                           team_name=team_name,
                           league_id=league_id)
    return teams


# ─── Analytics ─────────────────────────────────────────────────────────
# Returns counts only — no raw data. Lightweight endpoint for AI/LLM clients.
@app.get("/v0/counts/", response_model=schemas.Counts)
def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db))
    return counts