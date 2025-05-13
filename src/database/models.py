from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship, declarative_base
from ..config import ONE_YEAR, GLOBAL_START_TIME, GLICKO_MAX_RD, TS_MAX_SIGMA

Base = declarative_base()

"""
Game model

type - game type, e.g., TDM, King of the Hill, CTF, BR, etc.;
playtime - game duration (in seconds);
team_count - number of teams in the game;
team_size - number of players per team.
kill_cap - 
point_limit - 
winning_round_limit - 
player_count - number of total players in the game.

Association: Game with Player in a many-to-many through GamePlayer
"""
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

"""
GamePlayer model

Association: GamePlayer with Player and Game in one-to-many
"""
class GamePlayer(Base):
    __tablename__ = "game_players"

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
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

    # Glicko‑2 rating
    glicko_rating_before = Column(Float, nullable=False)
    glicko_rd_before = Column(Float, nullable=False)
    glicko_volatility_before = Column(Float, nullable=False)
    glicko_rating_after = Column(Float, default=0.0)
    glicko_rd_after = Column(Float, default=GLICKO_MAX_RD)
    glicko_volatility_after = Column(Float, default=0.06)

    # TrueSkill rating
    ts_rating_before = Column(Float, nullable=False)
    ts_volatility_before = Column(Float, nullable=False)
    ts_rating_after = Column(Float, default=0.0)
    ts_volatility_after = Column(Float, default=TS_MAX_SIGMA)
    
    game = relationship("Game", back_populates="game_players")
    player = relationship("Player", back_populates="game_players")

"""
Player model

name - player profile name
party_name - unique randomly generated party name, that allows to find players within the same party

Association:
 - Player with Game in a many-to-many through GamePlayer;
 - Player with PlayerGameTypeStats in a one-to-many;
"""
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=GLOBAL_START_TIME)
    name = Column(String(50), unique=True, index=True, nullable=False)
    party_name = Column(String(50), nullable=True)

    game_players = relationship("GamePlayer", back_populates="player")
    game_type_stats = relationship("PlayerGameTypeStats", back_populates="player")

"""
PlayerGameTypeStats model

Association: PlayerGameTypeStats with Player in a one-to-many.
"""
class PlayerGameTypeStats(Base):
    __tablename__ = "player_game_type_stats"

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
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

    # Glicko‑2 rating
    glicko_rating = Column(Float, default=0.0)
    glicko_rd = Column(Float, default=GLICKO_MAX_RD)
    glicko_volatility = Column(Float, default=0.06)

    # TrueSkill rating
    ts_rating = Column(Float, default=0.0)
    ts_volatility = Column(Float, default=TS_MAX_SIGMA)

    player = relationship("Player", back_populates="game_type_stats")
