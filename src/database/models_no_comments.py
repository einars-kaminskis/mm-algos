from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config import GLOBAL_START_TIME

Base = declarative_base()

class Game(Base):
    __tablename__ = "games"

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

    game_players = relationship("GamePlayer", back_populates="game")

class GamePlayer(Base):
    __tablename__ = "game_players"

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    team = Column(String(50), nullable=False)
    party_name = Column(String(50))
    team_placement = Column(Integer, nullable=False)
    is_tie = Column(Boolean, default=False)
    true_rating_before_game = Column(Integer, nullable=False)
    true_rating_after_game = Column(Integer)
    is_most_valuable_player = Column(Boolean, default=False)
    is_least_valuable_player = Column(Boolean, default=False)
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    longest_time_alive = Column(Float, default=0.0)
    headshot_damage_dealt = Column(Integer, default=0)
    torso_and_arm_damage_dealt = Column(Integer, default=0)
    leg_damage_dealt = Column(Integer, default=0)
    damage_taken = Column(Integer, default=0)
    contesting_kills = Column(Integer, default=0)
    objective_time = Column(Float, default=0.0)
    domination_points = Column(Integer, default=0)
    
    accuracy = Column(Float, default=0.0)
    headshot_accuracy = Column(Float, default=0.0)
    torso_accuracy = Column(Float, default=0.0)
    leg_accuracy = Column(Float, default=0.0)
    damage_missed = Column(Integer, default=0)
    avg_damage_missed_delta = Column(Float, default=0.0)

    kills_per_minute = Column(Float, default=0.0)
    deaths_per_minute = Column(Float, default=0.0)
    assists_per_minute = Column(Float, default=0.0)
    damage_dealt = Column(Integer, default=0)
    damage_dealt_per_minute = Column(Float, default=0.0)
    damage_taken_per_minute = Column(Float, default=0.0)
    damage_dealt_and_taken_ratio = Column(Float, default=0.0)
    kill_death_ratio = Column(Float, default=0.0)
    avg_damage_dealt_delta = Column(Float, default=0.0)
    avg_damage_taken_delta = Column(Float, default=0.0)
    avg_kills_delta = Column(Float, default=0.0)
    avg_deaths_delta = Column(Float, default=0.0)
    avg_assists_delta = Column(Float, default=0.0)
    best_killstreak = Column(Integer, default=0)
    rounds_won = Column(Integer, default=0)
    rounds_lost = Column(Integer, default=0)
    
    game = relationship("Game", back_populates="game_players")
    player = relationship("Player", back_populates="game_players")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    name = Column(String(50), unique=True, index=True, nullable=False)
    party_name = Column(String(50), nullable=True)

    game_players = relationship("GamePlayer", back_populates="player")
    game_type_stats = relationship("PlayerGameTypeStats", back_populates="player")

class PlayerGameTypeStats(Base):
    __tablename__ = "player_game_type_stats"

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    game_type = Column(String(50), nullable=False)
    true_rating = Column(Float, default=300)
    total_headshot_damage = Column(Integer, default=0)
    total_torso_and_arm_damage = Column(Integer, default=0)
    total_leg_damage = Column(Integer, default=0)
    total_kills = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    total_assists = Column(Integer, default=0)
    total_damage_taken = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    total_games_played = Column(Integer, default=0)
    last_time_played = Column(DateTime, nullable=True)
    total_damage_dealt = Column(Integer, default=0)
    total_damage_missed = Column(Integer, default=0)
    avg_damage_dealt = Column(Float, default=0.0)
    avg_damage_taken = Column(Float, default=0.0)
    avg_damage_missed = Column(Float, default=0.0)
    total_accuracy = Column(Float, default=0.0)
    headshot_accuracy = Column(Float, default=0.0)
    torso_accuracy = Column(Float, default=0.0)
    leg_accuracy = Column(Float, default=0.0)
    avg_kills = Column(Float, default=0.0)
    avg_deaths = Column(Float, default=0.0)
    avg_assists = Column(Float, default=0.0)
    total_kill_death_ratio = Column(Float, default=0.0)
    total_wins = Column(Integer, default=0)
    total_loses = Column(Integer, default=0)
    total_ties = Column(Integer, default=0)
    best_killstreak = Column(Integer, default=0)
    win_loss_ratio = Column(Float, default=0.0)

    """
    top_2_squad_count
    top_3_squad_count
    top_6_squad_count
    top_2_solo_count
    top_3_solo_count
    top_10_solo_count
    top_25_solo_count
    """

    player = relationship("Player", back_populates="game_type_stats")
