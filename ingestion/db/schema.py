"""
ingestion/db/schema.py
Full relational database schema for F1 AI platform.
Supports SQLite (default) and PostgreSQL (production).

Tables:
  drivers, teams, circuits, races,
  qualifying_results, race_results, pit_stops,
  weather_data, expert_predictions, regulations,
  ingestion_log
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text,
    Boolean, DateTime, ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()

# ─── CORE ENTITIES ────────────────────────────────────────────────

class Driver(Base):
    __tablename__ = "drivers"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    full_name      = Column(String(100), nullable=False, unique=True)
    abbreviation   = Column(String(3))
    nationality    = Column(String(50))
    date_of_birth  = Column(String(20))
    driver_number  = Column(Integer)
    active_season  = Column(Integer)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    race_results       = relationship("RaceResult", back_populates="driver_obj")
    qualifying_results = relationship("QualifyingResult", back_populates="driver_obj")
    expert_predictions = relationship("ExpertPrediction", back_populates="driver_obj")

    def __repr__(self):
        return f"<Driver {self.full_name} ({self.abbreviation})>"


class Team(Base):
    __tablename__ = "teams"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(100), nullable=False, unique=True)
    full_name     = Column(String(150))
    nationality   = Column(String(50))
    power_unit    = Column(String(50))
    active_season = Column(Integer)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    race_results       = relationship("RaceResult", back_populates="team_obj")
    qualifying_results = relationship("QualifyingResult", back_populates="team_obj")

    def __repr__(self):
        return f"<Team {self.name}>"


class Circuit(Base):
    __tablename__ = "circuits"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String(150), nullable=False, unique=True)
    location        = Column(String(100))
    country         = Column(String(100))
    circuit_type    = Column(String(50))   # street, permanent, semi-street
    total_laps      = Column(Integer)
    circuit_length_km = Column(Float)
    overtaking_difficulty = Column(String(20))  # very_low, low, medium, high
    drs_zones       = Column(Integer)
    created_at      = Column(DateTime, default=datetime.utcnow)

    races = relationship("Race", back_populates="circuit_obj")

    def __repr__(self):
        return f"<Circuit {self.name}>"


class Race(Base):
    __tablename__ = "races"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    season       = Column(Integer, nullable=False)
    round_number = Column(Integer, nullable=False)
    circuit_id   = Column(Integer, ForeignKey("circuits.id"))
    race_name    = Column(String(150), nullable=False)
    race_date    = Column(String(20))
    is_sprint_weekend = Column(Boolean, default=False)
    status       = Column(String(20), default="scheduled")  # scheduled, completed
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("season", "round_number", name="uq_season_round"),)

    circuit_obj        = relationship("Circuit", back_populates="races")
    race_results       = relationship("RaceResult", back_populates="race_obj")
    qualifying_results = relationship("QualifyingResult", back_populates="race_obj")
    weather_data       = relationship("WeatherData", back_populates="race_obj")
    pit_stops          = relationship("PitStop", back_populates="race_obj")

    def __repr__(self):
        return f"<Race {self.season} R{self.round_number}: {self.race_name}>"


# ─── RESULTS ──────────────────────────────────────────────────────

class QualifyingResult(Base):
    __tablename__ = "qualifying_results"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    race_id              = Column(Integer, ForeignKey("races.id"), nullable=False)
    driver_id            = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    team_id              = Column(Integer, ForeignKey("teams.id"), nullable=False)
    qualifying_position  = Column(Integer)
    q1_time              = Column(String(20))
    q2_time              = Column(String(20))
    q3_time              = Column(String(20))
    best_lap_time        = Column(String(20))
    gap_to_pole          = Column(Float)     # seconds
    is_pole              = Column(Boolean, default=False)
    created_at           = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("race_id", "driver_id", name="uq_qual_race_driver"),)

    race_obj   = relationship("Race", back_populates="qualifying_results")
    driver_obj = relationship("Driver", back_populates="qualifying_results")
    team_obj   = relationship("Team", back_populates="qualifying_results")

    def __repr__(self):
        return f"<QualResult P{self.qualifying_position} {self.driver_id}>"


class RaceResult(Base):
    __tablename__ = "race_results"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    race_id             = Column(Integer, ForeignKey("races.id"), nullable=False)
    driver_id           = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    team_id             = Column(Integer, ForeignKey("teams.id"), nullable=False)
    finish_position     = Column(Integer)
    grid_position       = Column(Integer)
    laps_completed      = Column(Integer)
    race_time           = Column(String(30))
    gap_to_winner       = Column(String(30))
    points              = Column(Float, default=0)
    fastest_lap         = Column(Boolean, default=False)
    fastest_lap_time    = Column(String(20))
    status              = Column(String(30), default="Finished")  # Finished, DNF, DNS, DSQ
    tire_strategy       = Column(String(30))
    pit_stop_count      = Column(Integer, default=0)
    incidents           = Column(Boolean, default=False)
    penalties           = Column(Integer, default=0)  # seconds
    podium              = Column(Boolean, default=False)
    win                 = Column(Boolean, default=False)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("race_id", "driver_id", name="uq_result_race_driver"),)

    race_obj   = relationship("Race", back_populates="race_results")
    driver_obj = relationship("Driver", back_populates="race_results")
    team_obj   = relationship("Team", back_populates="race_results")

    def __repr__(self):
        return f"<RaceResult P{self.finish_position} D{self.driver_id} R{self.race_id}>"


class PitStop(Base):
    __tablename__ = "pit_stops"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    race_id     = Column(Integer, ForeignKey("races.id"), nullable=False)
    driver_id   = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    stop_number = Column(Integer)
    lap         = Column(Integer)
    duration    = Column(Float)   # seconds
    compound_in  = Column(String(20))   # soft, medium, hard, inter, wet
    compound_out = Column(String(20))
    created_at  = Column(DateTime, default=datetime.utcnow)

    race_obj = relationship("Race", back_populates="pit_stops")

    def __repr__(self):
        return f"<PitStop R{self.race_id} D{self.driver_id} Stop{self.stop_number}>"


class WeatherData(Base):
    __tablename__ = "weather_data"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    race_id          = Column(Integer, ForeignKey("races.id"), nullable=False)
    session_type     = Column(String(20))  # qualifying, race, sprint
    condition        = Column(String(20))  # Dry, Wet, Mixed
    air_temp_c       = Column(Float)
    track_temp_c     = Column(Float)
    humidity_pct     = Column(Float)
    wind_speed_kmh   = Column(Float)
    rainfall_mm      = Column(Float, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)

    race_obj = relationship("Race", back_populates="weather_data")


# ─── EXPERT PREDICTIONS (NLP-derived) ─────────────────────────────

class ExpertPrediction(Base):
    __tablename__ = "expert_predictions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    race_id          = Column(Integer, ForeignKey("races.id"), nullable=True)
    driver_id        = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    source           = Column(String(100))    # e.g. "Sky Sports", "The Race", "Twitter"
    source_url       = Column(String(500))
    raw_text         = Column(Text)           # original quote/article snippet
    driver_name      = Column(String(100))    # extracted driver name
    team_name        = Column(String(100))    # extracted team name
    circuit_type     = Column(String(50))     # high_downforce, power, balanced
    prediction_type  = Column(String(50))     # qualifying, race, strategy, tire
    prediction_text  = Column(Text)           # normalized prediction
    sentiment        = Column(String(20))     # positive, negative, neutral
    sentiment_score  = Column(Float)          # -1.0 to 1.0
    confidence_score = Column(Float)          # 0.0 to 1.0
    entities         = Column(JSON)           # extracted NER entities
    ingested_at      = Column(DateTime, default=datetime.utcnow)
    race_weekend     = Column(String(50))     # e.g. "2026 Chinese GP"

    driver_obj = relationship("Driver", back_populates="expert_predictions")

    def __repr__(self):
        return f"<ExpertPred {self.driver_name} @ {self.source} conf={self.confidence_score}>"


# ─── REGULATIONS ──────────────────────────────────────────────────

class Regulation(Base):
    __tablename__ = "regulations"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    rule_id                 = Column(String(20), unique=True)   # e.g. REG-2026-PU-001
    category                = Column(String(50))   # power_unit, aerodynamics, tires, safety
    sub_category            = Column(String(50))
    rule_description        = Column(Text, nullable=False)
    effective_season        = Column(Integer, nullable=False)
    potential_race_impact   = Column(Text)
    potential_strategy_impact = Column(Text)
    impact_score            = Column(Float)   # 0-1, how much this rule affects race outcomes
    teams_affected          = Column(JSON)    # which teams benefit/lose
    created_at              = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Regulation {self.rule_id}: {self.category}>"


# ─── INGESTION LOG ────────────────────────────────────────────────

class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    source        = Column(String(100))       # data source name
    data_type     = Column(String(50))        # race_result, qualifying, expert, regulation
    season        = Column(Integer)
    round_number  = Column(Integer, nullable=True)
    status        = Column(String(20))        # success, failed, partial
    rows_inserted = Column(Integer, default=0)
    rows_updated  = Column(Integer, default=0)
    rows_skipped  = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_secs = Column(Float, nullable=True)
    triggered_by  = Column(String(50), default="manual")  # manual, scheduler, api
    timestamp     = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Log {self.data_type} {self.status} @ {self.timestamp}>"


# ─── DB CONNECTION ─────────────────────────────────────────────────

def get_engine(db_url: str = None):
    """
    Returns SQLAlchemy engine.
    Default: SQLite at data/f1_platform.db
    Production: set DB_URL env var to PostgreSQL connection string
    e.g. postgresql://user:pass@localhost:5432/f1_db
    """
    if db_url is None:
        db_url = os.environ.get(
            "F1_DB_URL",
            f"sqlite:///{ os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'f1_platform.db')}"
        )

    if "sqlite" in db_url:
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)

    return engine


def init_db(engine=None):
    """Create all tables if they don't exist."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    engine = init_db()
    print(f"✅ Database initialized")
    print(f"   Tables: {list(Base.metadata.tables.keys())}")
