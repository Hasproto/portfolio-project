"""SQLAlchemy models"""

# ─── Imports ───────────────────────────────────────────────────────────
# Column types and ForeignKey from SQLAlchemy core
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date

# relationship() lets us navigate between tables in Python
# (e.g., player.performances instead of writing a SQL JOIN)
from sqlalchemy.orm import relationship

# Base is the parent class all our models inherit from.
# It comes from database.py (which you'll create next).
from database import Base


# ─── Player ────────────────────────────────────────────────────────────
class Player(Base):
    # Maps this Python class to the SQL table named "player"
    __tablename__ = "player"

    # Each Column = one column in the SQL table
    player_id = Column(Integer, primary_key=True, index=True)
    gsis_id = Column(String, nullable=True)          # external NFL ID, optional
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    last_changed_date = Column(Date, nullable=False)

    # One-to-many: one player has many performances.
    # back_populates pairs this with Performance.player below.
    performances = relationship("Performance", back_populates="player")

    # Many-to-many: one player can be on many teams (via team_player).
    # secondary="team_player" tells SQLAlchemy to use the junction table.
    teams = relationship("Team", secondary="team_player",
                         back_populates="players")


# ─── Performance ───────────────────────────────────────────────────────
class Performance(Base):
    __tablename__ = "performance"

    performance_id = Column(Integer, primary_key=True, index=True)
    week_number = Column(String, nullable=False)
    fantasy_points = Column(Float, nullable=False)
    last_changed_date = Column(Date, nullable=False)

    # Foreign key to the player table — this is what links a performance to a player
    player_id = Column(Integer, ForeignKey("player.player_id"))

    # Mirror of Player.performances above — gives us performance.player navigation
    player = relationship("Player", back_populates="performances")


# ─── League ────────────────────────────────────────────────────────────
class League(Base):
    __tablename__ = "league"

    league_id = Column(Integer, primary_key=True, index=True)
    league_name = Column(String, nullable=False)
    scoring_type = Column(String, nullable=False)
    last_changed_date = Column(Date, nullable=False)

    # One league has many teams
    teams = relationship("Team", back_populates="league")


# ─── Team ──────────────────────────────────────────────────────────────
class Team(Base):
    __tablename__ = "team"

    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, nullable=False)
    last_changed_date = Column(Date, nullable=False)

    # FK to league
    league_id = Column(Integer, ForeignKey("league.league_id"))

    # Mirror of League.teams — gives team.league navigation
    league = relationship("League", back_populates="teams")

    # Many-to-many: a team has many players
    players = relationship("Player", secondary="team_player",
                           back_populates="teams")


# ─── TeamPlayer (junction / association table) ─────────────────────────
class TeamPlayer(Base):
    __tablename__ = "team_player"

    # Composite primary key: (team_id, player_id) together must be unique
    team_id = Column(Integer, ForeignKey("team.team_id"),
                     primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("player.player_id"),
                       primary_key=True, index=True)
    last_changed_date = Column(Date, nullable=False)
    # No relationship() lines here — those are defined on Player and Team