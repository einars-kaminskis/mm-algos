from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from config import GLOBAL_START_TIME

Base = declarative_base()

"""
Game model

type - game type, e.g., TDM, King of the Hill, CTF, BR, etc.;
playtime - game duration (in seconds);
team_count - number of teams in the game;
team_size - number of players per team.
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

team - name of the team, e.g., "Team 1", "Team 2", etc., or "red", "blue", etc.
       Even solo players will be in a team (solo team) for the sake of consistency.
party_name - unique randomly generated party name, that allows to find players within the same party
team_placement - overall placement based the game type's main objective/-s
true_rating_before_game - simulated objective true rating of the player before game
true_rating_after_game - simulated objective true rating of the player after the game
is_most_valuable_player - the most positively impactful player in the game
is_least_valuable_player - the most negatively impactful player in the game
total_kills - amount of kills;
total_deaths - amount of deaths;
total_assists - amount of assists;
longest_time_alive - longest period alive (in seconds);
headshot_damage_dealt - damage dealth to enemies that were headshots;
torso_and_arm_damage_dealt - damage dealth to enemies that were body or arm shots;
leg_damage_dealt - damage dealth to enemies that were leg shots;
damage_taken - amount of damage absorbed from enemy attacks;

Objective-based game type only metrics:
contesting_kills - amount of kills gotten near or at certain objectives, e.g.,
                   flag points in CTF, hill zone in King of the Hill, the payload zone
                   in a payload game type.
objective_time - total time spent on objectives (in seconds)

Game types that split players in different classes:
character_class - the name of the class played in a certain game type, e.g.,
                  tank, flank, healer, etc., or scout, recon, assault, etc.
                  This metric impacts other metric importance since different
                  classes should focus on different playstyles.

domination_points

Payload game type only metrics:
points_earned - points awarded for getting the payload for your team or for
                 it reaching the required destination.

kills_per_minute - total_kills / (game's playtime / 60)
deaths_per_minute - total_deaths / (game's playtime / 60)
assists_per_minute - total_assists / (game's playtime / 60)
damage_dealt - headshot_damage_dealt + torso_and_arm_damage_dealt + leg_damage_dealt
damage_dealt_per_minute - damage_dealt / (game's playtime / 60)
damage_taken_per_minute - damage_taken / (game's playtime / 60)
headshot_damage_ratio - headshot_damage_dealt / damage_dealt
torso_and_arm_damage_ratio - torso_and_arm_damage_dealt / damage_dealt
leg_damage_ratio - leg_damage_dealt / damage_dealt
damage_dealt_and_taken_ratio - damage_dealt / damage_taken
kill_death_ratio - total_kills / total_deaths
avg_damage_dealt_delta - avg_damage_dealt before the game - avg_damage_dealt after the game
avg_damage_taken_delta - avg_damage_taken before the game - avg_damage_taken after the game
avg_kills_delta - avg_kills before the game - avg_kills after the game
avg_deaths_delta - avg_deaths before the game - avg_deaths after the game
avg_assists_delta - avg_assists before the game - avg_assists after the game

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

game_type - game type, e.g., TDM, King of the Hill, CTF, BR, etc.;
true_rating - simulated objective true rating of the player for this game type
total_headshot_damage - 
total_torso_and_arm_damage - 
total_leg_damage - 
total_kills - 
total_deaths - 
total_assists - 
total_damage_taken - 
win_streak - 
total_games_played - total amount of games played for this game type
last_time_played -last date and time played for this game type

total_damage_dealt - 
avg_damage_dealt - 
avg_damage_taken - 
avg_kills - 
avg_deaths - 
avg_assists - 
kill_death_ratio - 

total_wins - 
total_loses - 
total_ties - 
best_killstreak - 
win_loss_ratio - 
rounds_won_in_all_games - 
rounds_lost_in_all_games - 
rounds_played_in_all_games - 
rounds_win_loss_ratio - 

Association: PlayerGameTypeStats with Player in a one-to-many.
"""
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
