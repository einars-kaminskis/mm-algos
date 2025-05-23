from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship, declarative_base
from ..config2 import ONE_YEAR, GLOBAL_START_TIME, GLICKO_MAX_RD, TS_MAX_SIGMA

Base = declarative_base()

"""
Game2 model
"""
class Game2(Base):
    __tablename__ = "games2"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    type = Column(String(50), nullable=False)
    playtime = Column(Float, default=0.0)
    team_count = Column(Integer, default=0)
    team_size = Column(Integer, default=0)
    kill_cap = Column(Integer, default=0)
    point_limit = Column(Integer, default=0)
    winning_round_limit = Column(Integer, default=0)
    player_count = Column(Integer, default=0)

    game_players2 = relationship("GamePlayer2", back_populates="game2")

"""
GamePlayer2 model
"""
class GamePlayer2(Base):
    __tablename__ = "game_players2"

    game_id = Column(Integer, ForeignKey("games2.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players2.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    team = Column(String(50), nullable=False)
    party_name = Column(String(50))

    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    headshot_damage_dealt = Column(Integer, default=0)
    torso_damage_dealt = Column(Integer, default=0)
    leg_damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    damage_dealt = Column(Integer, default=0)
    damage_missed = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    headshot_accuracy = Column(Float, default=0.0)
    torso_accuracy = Column(Float, default=0.0)
    leg_accuracy = Column(Float, default=0.0)
    contesting_kills = Column(Integer, default=0)
    objective_time = Column(Integer, default=0)
    longest_time_alive = Column(Integer, default=0)
    kills_per_minute = Column(Float, default=0.0)
    deaths_per_minute = Column(Float, default=0.0)
    assists_per_minute = Column(Float, default=0.0)
    damage_dealt_per_minute = Column(Float, default=0.0)
    damage_taken_per_minute = Column(Float, default=0.0)
    domination_points = Column(Integer, default=0)
    rounds_won = Column(Integer, default=0)
    rounds_lost = Column(Integer, default=0)
    killstreak = Column(Integer, default=0)
    
    team_placement = Column(Integer)
    is_tie = Column(Boolean, default=False)
    is_most_valuable_player = Column(Boolean, default=False)
    is_least_valuable_player = Column(Boolean, default=False)
    kill_death_ratio = Column(Float, default=0.0)
    damage_dealt_and_taken_ratio = Column(Float, default=0.0)

    # Simulation rating
    true_rating_before_game = Column(Float, nullable=False)
    true_rating_after_game = Column(Float, default=0.0)

    # Elo rating
    elo_before = Column(Float, nullable=False)
    elo_after = Column(Float, default=0.0)

    # Glicko rating
    glicko_rating_before = Column(Float, nullable=False)
    glicko_rd_before = Column(Float, nullable=False)
    glicko_rating_after = Column(Float, default=0.0)
    glicko_rd_after = Column(Float, default=GLICKO_MAX_RD)

    # TrueSkill rating
    ts_rating_before = Column(Float, nullable=False)
    ts_volatility_before = Column(Float, nullable=False)
    ts_rating_after = Column(Float, default=0.0)
    ts_volatility_after = Column(Float, default=TS_MAX_SIGMA)
    
    game2 = relationship("Game2", back_populates="game_players2")
    player2 = relationship("Player2", back_populates="game_players2")

"""
Player2 model
"""
class Player2(Base):
    __tablename__ = "players2"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    name = Column(String(50), unique=True, index=True, nullable=False)
    party_name = Column(String(50), nullable=True)

    game_players2 = relationship("GamePlayer2", back_populates="player2")
    game_type_stats2 = relationship("PlayerGameTypeStats2", back_populates="player2")

"""
PlayerGameTypeStats2 model
"""
class PlayerGameTypeStats2(Base):
    __tablename__ = "player_game_type_stats2"

    player_id = Column(Integer, ForeignKey("players2.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    game_type = Column(String(50), nullable=False)

    total_games_played = Column(Integer, default=0)

    total_kills = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    total_assists = Column(Integer, default=0)
    total_headshot_damage_dealt = Column(Integer, default=0)
    total_torso_damage_dealt = Column(Integer, default=0)
    total_leg_damage_dealt = Column(Integer, default=0)
    total_damage_taken = Column(Integer, default=0)
    total_damage_dealt = Column(Integer, default=0)
    total_damage_missed = Column(Integer, default=0)
    total_accuracy = Column(Float, default=0.0)
    total_headshot_accuracy = Column(Float, default=0.0)
    total_torso_accuracy = Column(Float, default=0.0)
    total_leg_accuracy = Column(Float, default=0.0)
    total_contesting_kills = Column(Integer, default=0)
    total_objective_time = Column(Integer, default=0)
    total_longest_time_alive = Column(Integer, default=0)
    total_kills_per_minute = Column(Float, default=0.0)
    total_deaths_per_minute = Column(Float, default=0.0)
    total_assists_per_minute = Column(Float, default=0.0)
    total_damage_dealt_per_minute = Column(Float, default=0.0)
    total_damage_taken_per_minute = Column(Float, default=0.0)
    best_killstreak = Column(Integer, default=0)

    last_time_played = Column(DateTime, default=(GLOBAL_START_TIME - ONE_YEAR))
    total_wins = Column(Integer, default=0)
    total_loses = Column(Integer, default=0)
    total_ties = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    win_loss_ratio = Column(Float, default=0.0)
    total_kill_death_ratio = Column(Float, default=0.0)
    total_damage_dealt_and_taken_ratio = Column(Float, default=0.0)

    avg_kills = Column(Float, default=0.0)
    avg_deaths = Column(Float, default=0.0)
    avg_assists = Column(Float, default=0.0)
    avg_headshot_damage_dealt = Column(Float, default=0.0)
    avg_torso_damage_dealt = Column(Float, default=0.0)
    avg_leg_damage_dealt = Column(Float, default=0.0)
    avg_damage_taken = Column(Float, default=0.0)
    avg_damage_dealt = Column(Float, default=0.0)
    avg_damage_missed = Column(Float, default=0.0)
    avg_accuracy = Column(Float, default=0.0)
    avg_headshot_accuracy = Column(Float, default=0.0)
    avg_torso_accuracy = Column(Float, default=0.0)
    avg_leg_accuracy = Column(Float, default=0.0)
    avg_contesting_kills = Column(Float, default=0.0)
    avg_objective_time = Column(Float, default=0.0)
    avg_longest_time_alive = Column(Float, default=0.0)
    avg_kills_per_minute = Column(Float, default=0.0)
    avg_deaths_per_minute = Column(Float, default=0.0)
    avg_assists_per_minute = Column(Float, default=0.0)
    avg_damage_dealt_per_minute = Column(Float, default=0.0)
    avg_damage_taken_per_minute = Column(Float, default=0.0)

    # Simulation rating
    true_rating = Column(Float, default=0.0)

    # Elo rating
    elo_rating = Column(Float, default=0.0)

    # Glicko rating
    glicko_rating = Column(Float, default=0.0)
    glicko_rd = Column(Float, default=GLICKO_MAX_RD)

    # TrueSkill rating
    ts_rating = Column(Float, default=0.0)
    ts_volatility = Column(Float, default=TS_MAX_SIGMA)

    player2 = relationship("Player2", back_populates="game_type_stats2")
