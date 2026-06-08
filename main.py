"""FastAPI program - Chapter 4"""

# ─── Imports ───────────────────────────────────────────────────────────
# Depends: for dependency injection (auto-creates DB sessions)
# FastAPI: the main framework class
# HTTPException: returns HTTP error codes (like 404 Not Found)
from fastapi import Depends, FastAPI, HTTPException, Query

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
@app.get("/",
         summary="API Health Check",
         description="Returns a simple message to verify the API is running",
         response_description="Health check message",
         operation_id="v0_health_check",
         tags=["analytics"]) 
async def root():
    return {"message": "API health check successful"}

#####################################################################################################################
# ─── Players ───────────────────────────────────────────────────────────
# List of players with optional filters (query parameters)
# Example URL: /v0/players/?first_name=Bryce&last_name=Young&limit=10
@app.get("/v0/players/",
         response_model=list[schemas.Player],
         summary="Get a list of NFL players with optional filters",
         description="Returns a list of NFL players. You can filter by first name, last name, or minimum last changed date. Supports pagination with skip and limit.",
         response_description="A list of NFL players with their scoring performances",
         operation_id="v0_get_players",
         tags=["player"])
# def read_players(skip: int = 0, 
#                  limit: int = 100,
#                  minimum_last_changed_date: date = None,
#                  first_name: str = None,
#                  last_name: str = None,
#                  db: Session = Depends(get_db)):
# But after adding paramter descriptions: 
# Before — default only
# param: type = default_value

# # After — default + description
# param: type = Query(default_value, description="...")
def read_players(skip: int = Query(0, description="The number of items to skip at the beginning of API call."),
                 limit: int = Query(100, description="The number of records to return after the skipped records."),
                 minimum_last_changed_date: date = Query(None, description="The minimum date of change that you want to return records. Exclude any records changed before this."),
                 first_name: str = Query(None, description="The first name of the players to return"),
                 last_name: str = Query(None, description="The last name of the players to return"),
                 db: Session = Depends(get_db)):
    players = crud.get_players(db,
                               skip=skip,
                               limit=limit,
                               min_last_changed_date=minimum_last_changed_date,
                               first_name=first_name,
                               last_name=last_name)
    return players

#####################################################################################################################
# Single player by ID (path parameter)
# Example URL: /v0/players/1001

# Functions that DON'T change
# These only have path parameters or Depends, no query parameters to describe:
# read_player — player_id is a path parameter (already described by the URL)
# read_league — same, league_id is a path parameter
# root — no parameters
# get_count — no query parameters
@app.get("/v0/players/{player_id}",
         response_model=schemas.Player,
         summary="Get one player using the Player ID, which is internal to SWC",
         description="If you have an SWC Player ID of a player from another API call such as v0_get_players, you can call this API using the player ID",
         response_description="One NFL player",
         operation_id="v0_get_players_by_player_id",
         tags=["player"]) 
def read_player(player_id: int,  db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404,
                            detail="Player not found")
    return player


# ─── Performances ──────────────────────────────────────────────────────
@app.get("/v0/performances/",
         response_model=list[schemas.Performance],
         summary="Get a list of NFL player scoring performances",
         description="Returns a list of weekly fantasy scoring performances. You can filter by minimum last changed date. Supports pagination with skip and limit.",
         response_description="A list of NFL player scoring performances",
         operation_id="v0_get_performances",
         tags=["scoring"]) 
# def read_performances(skip: int = 0,
#                       limit: int = 100,
#                       minimum_last_changed_date: date = None,
#                       db: Session = Depends(get_db)):
def read_performances(skip: int = Query(0, description="The number of items to skip at the beginning of API call."),
                      limit: int = Query(100, description="The number of records to return after the skipped records."),
                      minimum_last_changed_date: date = Query(None, description="The minimum date of change that you want to return records. Exclude any records changed before this."),
                      db: Session = Depends(get_db)):
    performances = crud.get_performances(db,
                                         skip=skip,
                                         limit=limit,
                                         min_last_changed_date=minimum_last_changed_date)
    return performances


# ─── Leagues ───────────────────────────────────────────────────────────
# Single league by ID
@app.get("/v0/leagues/{league_id}",
         response_model=schemas.League,
         summary="Get one league using the League ID",
         description="Returns a single SWC fantasy football league with its teams. Use this if you have a league ID from another API call such as v0_get_leagues.",
         response_description="One SWC fantasy football league",
         operation_id="v0_get_leagues_by_league_id",
         tags=["membership"]) 
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="League not found")
    return league


# List of leagues
@app.get("/v0/leagues/",
         response_model=list[schemas.League],
         summary="Get a list of SWC fantasy football leagues",
         description="Returns a list of SWC fantasy football leagues with their teams. You can filter by league name or minimum last changed date. Supports pagination with skip and limit.",
         response_description="A list of SWC fantasy football leagues",
         operation_id="v0_get_leagues",
         tags=["membership"]) 
def read_leagues(skip: int = Query(0, description="The number of items to skip at the beginning of API call."),
                 limit: int = Query(100, description="The number of records to return after the skipped records."),
                 minimum_last_changed_date: date = Query(None, description="The minimum date of change that you want to return records. Exclude any records changed before this."),
                 league_name: str = Query(None, description="The name of the league to return"),
                 db: Session = Depends(get_db)):
    leagues = crud.get_leagues(db,
                               skip=skip,
                               limit=limit,
                               min_last_changed_date=minimum_last_changed_date,
                               league_name=league_name)
    return leagues


# ─── Teams ─────────────────────────────────────────────────────────────
@app.get("/v0/teams/",
         response_model=list[schemas.Team],
         summary="Get a list of SWC fantasy football teams",
         description="Returns a list of SWC fantasy football teams with their players. You can filter by team name, league ID, or minimum last changed date. Supports pagination with skip and limit.",
         response_description="A list of SWC fantasy football teams",
         operation_id="v0_get_teams",
         tags=["membership"]) 
# def read_teams(skip: int = 0,
#                limit: int = 100,
#                minimum_last_changed_date: date = None,
#                team_name: str = None,
#                league_id: int = None,
#                db: Session = Depends(get_db)):
def read_teams(skip: int = Query(0, description="The number of items to skip at the beginning of API call."),
               limit: int = Query(100, description="The number of records to return after the skipped records."),
               minimum_last_changed_date: date = Query(None, description="The minimum date of change that you want to return records. Exclude any records changed before this."),
               team_name: str = Query(None, description="The name of the team to return"),
               league_id: int = Query(None, description="The league ID to filter teams by"),
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
@app.get("/v0/counts/",
         response_model=schemas.Counts,
         summary="Get counts of leagues, teams, and players",
         description="Returns the total number of leagues, teams, and players in the SWC API. Useful for analytics and AI applications that need to understand the size of the dataset before making detailed queries.",
         response_description="Counts of leagues, teams, and players",
         operation_id="v0_get_counts",
         tags=["analytics"])
def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db))
    return counts