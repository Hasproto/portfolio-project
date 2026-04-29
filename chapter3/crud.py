"""SQLAlchemy Query Functions"""

# ─── Imports ───────────────────────────────────────────────────────────
from sqlalchemy.orm import Session         # type for the DB session parameter
from sqlalchemy.orm import joinedload      # for eager loading related tables
from datetime import date                  # date type for filter parameters
import models                              # your models.py — gives access to Player, Team, etc.


# ─── Single-record lookups ─────────────────────────────────────────────
def get_player(db: Session, player_id: int):
    # Find one player by primary key. .first() returns one row or None.
    return db.query(models.Player).filter(
        models.Player.player_id == player_id).first()


def get_league(db: Session, league_id: int = None):
    return db.query(models.League).filter(
        models.League.league_id == league_id).first()


# ─── List queries with filters + pagination ────────────────────────────
def get_players(db: Session, skip: int = 0, limit: int = 100,
                min_last_changed_date: date = None,
                last_name: str = None, first_name: str = None):
    # Start with a base query: SELECT * FROM player
    query = db.query(models.Player)

    # Conditionally add WHERE clauses if the caller provided filter values
    if min_last_changed_date:
        query = query.filter(
            models.Player.last_changed_date >= min_last_changed_date)
    if first_name:
        query = query.filter(models.Player.first_name == first_name)
    if last_name:
        query = query.filter(models.Player.last_name == last_name)

    # Pagination: skip N rows, return up to `limit` rows
    return query.offset(skip).limit(limit).all()


def get_performances(db: Session, skip: int = 0, limit: int = 100,
                     min_last_changed_date: date = None):
    query = db.query(models.Performance)
    if min_last_changed_date:
        query = query.filter(
            models.Performance.last_changed_date >= min_last_changed_date)
    return query.offset(skip).limit(limit).all()


def get_leagues(db: Session, skip: int = 0, limit: int = 100,
                min_last_changed_date: date = None, league_name: str = None):
    # joinedload tells SQLAlchemy to fetch each league's teams in the same query
    # (eager loading — avoids the "N+1 query" problem)
    query = db.query(models.League).options(joinedload(models.League.teams))

    if min_last_changed_date:
        query = query.filter(
            models.League.last_changed_date >= min_last_changed_date)
    if league_name:
        query = query.filter(models.League.league_name == league_name)
    return query.offset(skip).limit(limit).all()


def get_teams(db: Session, skip: int = 0, limit: int = 100,
              min_last_changed_date: date = None,
              team_name: str = None, league_id: int = None):
    query = db.query(models.Team)
    if min_last_changed_date:
        query = query.filter(
            models.Team.last_changed_date >= min_last_changed_date)
    if team_name:
        query = query.filter(models.Team.team_name == team_name)
    if league_id:
        query = query.filter(models.Team.league_id == league_id)
    return query.offset(skip).limit(limit).all()


# ─── Analytics (count) queries ─────────────────────────────────────────
# Lightweight endpoints for "how many?" questions.
# Especially useful for LLMs/AI clients that want stats without big payloads.
def get_player_count(db: Session):
    return db.query(models.Player).count()


def get_team_count(db: Session):
    return db.query(models.Team).count()


def get_league_count(db: Session):
    return db.query(models.League).count()