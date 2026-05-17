"""Pydantic schemas"""

# ─── Imports ───────────────────────────────────────────────────────────
# BaseModel: parent class for all Pydantic schemas
# ConfigDict: lets us configure schema behavior (like reading from SQLAlchemy objects)
from pydantic import BaseModel, ConfigDict

# List: type hint for fields that hold multiple objects
from typing import List

# date: type for date fields (matches SQLAlchemy's Date column)
from datetime import date


# ─── Performance schema ────────────────────────────────────────────────
class Performance(BaseModel):
    # from_attributes=True lets Pydantic auto-fill this schema from a SQLAlchemy object
    # (without it, you'd have to manually convert each field)
    model_config = ConfigDict(from_attributes=True)

    # Note: Pydantic uses COLON (:), NOT equals (=), for type assignment
    performance_id: int
    player_id: int
    week_number: str
    fantasy_points: float
    last_changed_date: date


# ─── Player schemas (split into Base + full) ───────────────────────────
class PlayerBase(BaseModel):
    """Player WITHOUT performances — used when embedding in Team responses."""
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    gsis_id: str
    first_name: str
    last_name: str
    position: str
    last_changed_date: date


class Player(PlayerBase):
    """Player WITH performances — used for /v0/players/ endpoints."""
    model_config = ConfigDict(from_attributes=True)
    performances: List[Performance] = []  # list of nested Performance objects


# ─── Team schemas ──────────────────────────────────────────────────────
class TeamBase(BaseModel):
    """Team WITHOUT players — used when embedding in League responses."""
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    team_id: int
    team_name: str
    last_changed_date: date


class Team(TeamBase):
    """Team WITH players — used for /v0/teams/ endpoint."""
    model_config = ConfigDict(from_attributes=True)
    players: List[PlayerBase] = []  # uses PlayerBase, not Player (no nested performances)


# ─── League schema ─────────────────────────────────────────────────────
class League(BaseModel):
    """League WITH teams — used for /v0/leagues/ endpoint."""
    model_config = ConfigDict(from_attributes=True)

    league_id: int
    league_name: str
    scoring_type: str
    last_changed_date: date
    teams: List[TeamBase] = []  # uses TeamBase, not Team (no nested players)


# ─── Counts schema (analytics) ─────────────────────────────────────────
class Counts(BaseModel):
    """Pure response object — no database table behind it, so no from_attributes."""
    league_count: int
    team_count: int
    player_count: int