import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from sqlalchemy import asc, func, or_
from ..database.db_setup import engine, SessionLocal
from ..database.models import Base, Game, GamePlayer, Player, PlayerGameTypeStats
from ..config import (
    GameMode,
    GAME_GAP,
    ONE_WEEK,
    ONE_YEAR,
    GAME_TYPES,
    HALF_MINUTE,
    RANK_AVERAGES,
    TOTAL_PLAYERS,
    TOTAL_ATTRIBUTES,
    GLOBAL_START_TIME,
    REF_COEF_AND_GAMES,
    REFERENCE_PLAYER_COUNT,
    REF_INITIAL_TRUE_RATING,
    SCENARIO_PLAYER_PARTIES,
    RANK_DISTRIBUTION_WEIGHTS,
    ensure_utc,
    get_stat_parameters
)

# Set random seed for reproducibility
random.seed(42)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup SQLAlchemy engine and session (e.g., using SQLite)
session = SessionLocal()

# Create tables (if not exist)
Base.metadata.create_all(engine)


"""
Simulate the passage of time for a game.
"""
def simulate_game_time(prev_time: datetime, game_type: GameMode) -> Tuple[datetime, int]:
    mean = game_type.time_limit_mean
    variance = game_type.time_limit_variance
    playtime = max(int(random.gauss(mean, variance)), mean - (2 * variance))
    new_time = prev_time + timedelta(seconds=playtime) + GAME_GAP
    return new_time, playtime


def compute_basic_stats(game_type: GameMode, rank_avg_stats: dict, playtime: int) -> Dict[str, Any]:
    # Random Gausian values based on averages for rank
    accuracy = max(random.gauss((rank_avg_stats["mean_accuracy"]), (rank_avg_stats["sd_accuracy"])), 0.0)
    
    kills = max(int(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"])), 0) if accuracy > 0.0 else 0
    deaths = max(int(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"])), 0)
    assists = max(int(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"])), 0) if accuracy > 0.0 else 0

    damage_dealt = sum(int(max(random.gauss(100, 5), 0)) for _ in range(kills)) + sum(int(max(random.gauss(35, 34), 0)) for _ in range(assists)) if accuracy > 0.0 else 0
    damage_taken = max(sum(int(random.gauss(100, 5)) for _ in range(deaths)), 0)
    killstreak = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        killstreak = kills
    else:
        killstreak = min(kills, max(int(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"])), 0))

    headshot_accuracy = max(min(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]), accuracy), 0.0)
    torso_accuracy = max(min(random.gauss(rank_avg_stats["mean_torso_accuracy"], rank_avg_stats["sd_torso_accuracy"]), accuracy - headshot_accuracy), 0.0) if accuracy > 0.0 else 0.0

    # Calculatable values
    damage_missed = int((damage_dealt / accuracy) - damage_dealt) if accuracy > 0.0 and damage_dealt > 0 else max(int(random.gauss(rank_avg_stats["mean_damage_missed"], rank_avg_stats["sd_damage_missed"])), 0)
    leg_accuracy = accuracy - headshot_accuracy - torso_accuracy if accuracy > 0.0 else 0.0

    total_damage = damage_dealt + damage_missed

    headshot_damage_dealt = int(total_damage * headshot_accuracy)
    torso_damage_dealt = int(total_damage * torso_accuracy)
    leg_damage_dealt = total_damage - headshot_damage_dealt - torso_damage_dealt

    kills_per_minute = kills / playtime * 60 if playtime > 0 else 0.0
    deaths_per_minute = deaths / playtime * 60 if playtime > 0 else 0.0
    assists_per_minute = assists / playtime * 60 if playtime > 0 else 0.0
    damage_dealt_per_minute = damage_dealt / playtime * 60 if playtime > 0 else 0.0
    damage_taken_per_minute = damage_taken / playtime * 60 if playtime > 0 else 0.0

    kill_death_ratio = kills / deaths if deaths > 0 else 0.0
    damage_dealt_and_taken_ratio = damage_dealt / damage_taken if damage_taken > 0 else 0.0

    objective_time = 0
    if game_type.type == 'Domination':
        objective_time = min(max(int(random.gauss(rank_avg_stats["mean_objective_time"], rank_avg_stats["sd_objective_time"])), 10), int(0.8 * playtime))

    longest_time_alive = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        longest_time_alive = max(int(random.randrange(rank_avg_stats["mean_longest_time_alive"] - rank_avg_stats["sd_longest_time_alive"], playtime + 1, 1)), 20)
    elif game_type.type == 'SAD':
        longest_time_alive = max(int(random.randrange(rank_avg_stats["mean_longest_time_alive"] - rank_avg_stats["sd_longest_time_alive"], int(playtime / 30) + 101, 1)), 20)
    else:
        longest_time_alive = max(int(random.gauss(rank_avg_stats["mean_longest_time_alive"], rank_avg_stats["sd_longest_time_alive"])), 10)

    contesting_kills = 0

    return {
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "killstreak": killstreak,

        "headshot_damage_dealt": headshot_damage_dealt,
        "torso_damage_dealt": torso_damage_dealt,
        "leg_damage_dealt": leg_damage_dealt,

        "accuracy": accuracy,
        "damage_missed": damage_missed,

        "leg_accuracy": leg_accuracy,
        "torso_accuracy": torso_accuracy,
        "headshot_accuracy": headshot_accuracy,

        "kills_per_minute": kills_per_minute,
        "deaths_per_minute": deaths_per_minute,
        "assists_per_minute": assists_per_minute,
        "damage_dealt_per_minute": damage_dealt_per_minute,
        "damage_taken_per_minute": damage_taken_per_minute,

        "kill_death_ratio": kill_death_ratio,
        "damage_dealt_and_taken_ratio": damage_dealt_and_taken_ratio,

        "objective_time": objective_time,
        "longest_time_alive": longest_time_alive,
  
        "contesting_kills": contesting_kills,
    }


def compute_remaining_stats(game_player: GamePlayer, playtime: int, is_mvp: bool, is_lvp: bool) -> Dict[str, Any]:
    damage_missed = int((game_player.damage_dealt / game_player.accuracy) - game_player.damage_dealt) if game_player.accuracy else 0

    total_damage = damage_missed + game_player.damage_dealt

    headshot_damage_dealt = int(total_damage * game_player.headshot_accuracy)
    torso_damage_dealt = int(total_damage * game_player.torso_accuracy)
    leg_damage_dealt = total_damage - headshot_damage_dealt - torso_damage_dealt

    kills_per_minute = game_player.kills / playtime * 60 if playtime else 0.0
    deaths_per_minute = game_player.deaths / playtime * 60 if playtime else 0.0
    assists_per_minute = game_player.assists / playtime * 60 if playtime else 0.0
    damage_dealt_per_minute = game_player.damage_dealt / playtime * 60 if playtime else 0.0
    damage_taken_per_minute = game_player.damage_taken / playtime * 60 if playtime else 0.0

    kill_death_ratio = game_player.kills / game_player.deaths if game_player.deaths else 0.0
    damage_dealt_and_taken_ratio = game_player.damage_dealt / game_player.damage_taken if game_player.damage_taken else 0.0

    is_most_valuable_player = is_mvp
    is_least_valuable_player = is_lvp

    kills = game_player.kills if game_player.kills else 0
    deaths = game_player.deaths if game_player.deaths else 0
    assists = game_player.assists if game_player.assists else 0
    damage_taken = game_player.damage_taken if game_player.damage_taken else 0
    damage_dealt = game_player.damage_dealt if game_player.damage_dealt else 0
    accuracy = game_player.accuracy if game_player.accuracy else 0.0
    headshot_accuracy = game_player.headshot_accuracy if game_player.headshot_accuracy else 0.0
    torso_accuracy = game_player.torso_accuracy if game_player.torso_accuracy else 0.0
    leg_accuracy = game_player.leg_accuracy if game_player.leg_accuracy else 0.0
    contesting_kills = game_player.contesting_kills if game_player.contesting_kills else 0
    objective_time = game_player.objective_time if game_player.objective_time else 0
    longest_time_alive = game_player.longest_time_alive if game_player.longest_time_alive else 0
    domination_points = game_player.domination_points if game_player.domination_points else 0
    rounds_won = game_player.rounds_won if game_player.rounds_won else 0
    rounds_lost = game_player.rounds_lost if game_player.rounds_lost else 0
    killstreak = game_player.killstreak if game_player.killstreak else 0

    team_placement = game_player.team_placement if game_player.team_placement else 1
    is_tie = game_player.is_tie

    true_rating_after_game = 0.0

    return {
        "damage_missed": damage_missed,

        "headshot_damage_dealt": headshot_damage_dealt,
        "torso_damage_dealt": torso_damage_dealt,
        "leg_damage_dealt": leg_damage_dealt,

        "kills_per_minute": kills_per_minute,
        "deaths_per_minute": deaths_per_minute,
        "assists_per_minute": assists_per_minute,
        "damage_dealt_per_minute": damage_dealt_per_minute,
        "damage_taken_per_minute": damage_taken_per_minute,

        "kill_death_ratio": kill_death_ratio,
        "damage_dealt_and_taken_ratio": damage_dealt_and_taken_ratio,

        "is_most_valuable_player": is_most_valuable_player,
        "is_least_valuable_player": is_least_valuable_player,

        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "damage_taken": damage_taken,
        "damage_dealt": damage_dealt,
        "accuracy": accuracy,
        "headshot_accuracy": headshot_accuracy,
        "torso_accuracy": torso_accuracy,
        "leg_accuracy": leg_accuracy,
        "contesting_kills": contesting_kills,
        "objective_time": objective_time,
        "longest_time_alive": longest_time_alive,
        "domination_points": domination_points,
        "rounds_won": rounds_won,
        "rounds_lost": rounds_lost,
        "killstreak": killstreak,
        "team_placement": team_placement,
        "is_tie": is_tie,
        "true_rating_after_game": true_rating_after_game,
    }

def calculate_ranking(game_type: GameMode, game_player: GamePlayer, player_stats: PlayerGameTypeStats, player_average_stats: dict) -> int:
    # ref_player_rating_coef = 1 if game_player.player_id > 40 else RATING_COEFICIENT
    ref_player_rating_coef = 1

    total_avg_deltas = {}

    for (attr, koef) in TOTAL_ATTRIBUTES:
        rating_coeficient = ref_player_rating_coef ** -1 if koef < 0 else ref_player_rating_coef

        if getattr(player_stats, f"avg_{attr}") > 0:
            total_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * ((rating_coeficient * getattr(game_player, attr)) - getattr(player_stats, f"avg_{attr}")) / getattr(player_stats, f"avg_{attr}")
        else:
            total_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * rating_coeficient * 1.0 if getattr(game_player, attr) > 0.0 else 0.0  # if avg is zero, treat any positive performance as +1 and zero as 0

    if player_stats.best_killstreak > 0:
        total_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * ((ref_player_rating_coef * game_player.killstreak) - player_stats.best_killstreak) / player_stats.best_killstreak
    else:
        total_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * ref_player_rating_coef * 1.0 if game_player.killstreak > 0 else 0.0
   
    if player_stats.total_kill_death_ratio > 0:
        total_avg_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * ((ref_player_rating_coef * game_player.kill_death_ratio) - player_stats.total_kill_death_ratio) / player_stats.total_kill_death_ratio
    else:
        total_avg_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * ref_player_rating_coef * 1.0 if game_player.kill_death_ratio > 0.0 else 0.0

    if player_stats.total_damage_dealt_and_taken_ratio > 0:
        total_avg_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * ((ref_player_rating_coef * game_player.damage_dealt_and_taken_ratio) - player_stats.total_damage_dealt_and_taken_ratio) / player_stats.total_damage_dealt_and_taken_ratio
    else:
        total_avg_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * ref_player_rating_coef * 1.0 if game_player.damage_dealt_and_taken_ratio > 0.0 else 0.0

    rank_avg_deltas = {}

    for (attr, koef) in RANK_AVERAGES:
        rating_coeficient = ref_player_rating_coef ** -1 if koef < 0 else ref_player_rating_coef

        if player_stats.total_games_played == 0:
            rank_avg_deltas[f"delta_{attr}"] = 0.0
        elif player_average_stats[f"mean_{attr}"] > 0:
            rank_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * ((rating_coeficient * getattr(game_player, attr)) - player_average_stats[f"mean_{attr}"]) / player_average_stats[f"mean_{attr}"]
        else:
            rank_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * rating_coeficient * 1.0 if getattr(game_player, attr) > 0.0 else 0.0

    if player_stats.total_games_played == 0:
        rank_avg_deltas["delta_killstreak"] = 0.0
    elif player_average_stats["mean_best_killstreak"] > 0:
        rank_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * ((ref_player_rating_coef * game_player.killstreak) - player_average_stats["mean_best_killstreak"]) / player_average_stats["mean_best_killstreak"]
    else:
        rank_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * ref_player_rating_coef * 1.0 if game_player.killstreak > 0 else 0.0

    if player_stats.total_games_played == 0:
        rank_avg_deltas["delta_win_streak"] = 0.0
    elif player_average_stats["mean_win_streak"] > 0:
        rank_avg_deltas["delta_win_streak"] = game_type.rank_delta_weights["win_streak"] * ((ref_player_rating_coef * player_stats.win_streak) - player_average_stats["mean_win_streak"]) / player_average_stats["mean_win_streak"]
    else:
        rank_avg_deltas["delta_win_streak"] = game_type.rank_delta_weights["win_streak"] * ref_player_rating_coef * 1.0 if player_stats.win_streak > 0 else 0.0

    other_deltas = {}

    other_deltas["delta_win_loss_ratio"] = game_type.rank_delta_weights["win_loss_ratio"] * ((ref_player_rating_coef * player_stats.win_loss_ratio) - 0.5) / 0.5 if player_stats.total_games_played > 0 else 0.0

    mid = (game_type.team_count + 1) / 2
    range_from_mid   = (game_type.team_count - 1) / 2

    if range_from_mid == 0: # if there is ever a case, where team_count = 1, this guards against division by zero
        other_deltas["delta_placement"] = 0
    else:
        other_deltas["delta_placement"] = (mid - game_player.team_placement) / range_from_mid

    other_deltas["delta_tie"] = (ref_player_rating_coef ** -1) * game_type.rank_delta_weights["is_tie"] * -0.5 if game_player.is_tie is True else ref_player_rating_coef * game_type.rank_delta_weights["is_tie"] * 0.5

    other_deltas["delta_is_most_valuable_player"] = ref_player_rating_coef * int(game_player.is_most_valuable_player is True) * 1.5

    other_deltas["delta_is_least_valuable_player"] = (ref_player_rating_coef ** -1) * int(game_player.is_least_valuable_player is True) * -2.0

    perf_total   = 0.28 * sum(total_avg_deltas.values()) / len(total_avg_deltas)
    perf_rating  = 0.32 * sum(rank_avg_deltas.values()) / len(rank_avg_deltas)
    perf_other   = 0.40 * sum(other_deltas.values()) / len(other_deltas)

    ss = perf_total + perf_rating + perf_other

    last_playtime = ensure_utc(player_stats.last_time_played) if player_stats.last_time_played is not None else (ensure_utc(game_player.created_at) - ONE_YEAR)
    
    uncertainty_duration = (ensure_utc(game_player.created_at) - last_playtime).total_seconds() # Need to get seconds. Lower impact of this the higher rank you are and the more games played

    TWO_WEEKS = 1209600 # in seconds

    uncertainty_koef = 2 ** (-uncertainty_duration / TWO_WEEKS)

    gameplay_koef = math.exp(-0.0004 * player_stats.total_games_played)

    rating_koef = math.exp(-0.00025 * game_player.true_rating_before_game)

    kk = game_type.base_k * (max((1.5 - uncertainty_koef) * ((gameplay_koef + rating_koef) / 2), 0.3)) # Decay goes from 0.5 to 1.5 for new players and falls to 0.3 constant, if player is experienced or has played for a long time.

    true_rating_after_game = max(game_player.true_rating_before_game + (kk * ss), 0.0)

    return true_rating_after_game

"""
Update aggregated player stats based on the results of a game.
"""
def update_player_stats(player_stats: PlayerGameTypeStats, game_player: GamePlayer) -> None:
    player_stats.total_kills += game_player.kills
    player_stats.total_deaths += game_player.deaths
    player_stats.total_assists += game_player.assists
    player_stats.total_damage_missed += game_player.damage_missed
    player_stats.total_damage_taken += game_player.damage_taken
    player_stats.total_damage_dealt += game_player.damage_dealt
    player_stats.total_games_played += 1
    
    if not game_player.is_tie:
        if game_player.team_placement == 1:
            player_stats.total_wins += 1
            player_stats.win_streak = player_stats.win_streak + 1
        else:
            player_stats.total_loses += 1
            player_stats.win_streak = 0
    else:
        player_stats.total_ties += 1

    created_at = ensure_utc(game_player.created_at)
    starter_last_time_played = created_at - ONE_YEAR

    # Decay lowers by a week after each game and doesn't go further than a year ago.
    player_stats.last_time_played = min(created_at, max(starter_last_time_played, ensure_utc(player_stats.last_time_played) + ONE_WEEK)) if player_stats.last_time_played is not None else starter_last_time_played + ONE_WEEK
    player_stats.true_rating = game_player.true_rating_after_game
    player_stats.total_headshot_damage_dealt += game_player.headshot_damage_dealt
    player_stats.total_torso_damage_dealt += game_player.torso_damage_dealt
    player_stats.total_leg_damage_dealt += game_player.leg_damage_dealt
    player_stats.total_contesting_kills += game_player.contesting_kills
    player_stats.total_objective_time += game_player.objective_time
    player_stats.total_longest_time_alive += game_player.longest_time_alive
    player_stats.total_kills_per_minute += game_player.kills_per_minute
    player_stats.total_deaths_per_minute += game_player.deaths_per_minute
    player_stats.total_assists_per_minute += game_player.assists_per_minute
    player_stats.total_damage_dealt_per_minute += game_player.damage_dealt_per_minute
    player_stats.total_damage_taken_per_minute += game_player.damage_taken_per_minute

    total_damage = player_stats.total_damage_dealt + player_stats.total_damage_missed

    if total_damage > 0:
        player_stats.total_accuracy += game_player.accuracy
        player_stats.total_headshot_accuracy += game_player.headshot_accuracy
        player_stats.total_torso_accuracy += game_player.torso_accuracy
        player_stats.total_leg_accuracy += game_player.leg_accuracy

    player_stats.total_kill_death_ratio = player_stats.total_kills / player_stats.total_deaths if player_stats.total_deaths > 0 else float(player_stats.total_kills)
    player_stats.total_damage_dealt_and_taken_ratio = player_stats.total_damage_dealt / player_stats.total_damage_taken if player_stats.total_damage_taken > 0 else float(player_stats.total_damage_dealt)
    player_stats.win_loss_ratio = player_stats.total_wins / player_stats.total_loses if player_stats.total_loses > 0 else float(player_stats.total_wins)
        
    if player_stats.total_games_played > 0:
        player_stats.avg_kills = player_stats.total_kills / player_stats.total_games_played
        player_stats.avg_deaths = player_stats.total_deaths / player_stats.total_games_played
        player_stats.avg_assists = player_stats.total_assists / player_stats.total_games_played
        player_stats.avg_damage_dealt = player_stats.total_damage_dealt / player_stats.total_games_played
        player_stats.avg_damage_taken = player_stats.total_damage_taken / player_stats.total_games_played
        player_stats.avg_damage_missed = player_stats.total_damage_missed / player_stats.total_games_played
        player_stats.avg_headshot_damage_dealt = player_stats.total_headshot_damage_dealt / player_stats.total_games_played
        player_stats.avg_torso_damage_dealt = player_stats.total_torso_damage_dealt / player_stats.total_games_played
        player_stats.avg_leg_damage_dealt = player_stats.total_leg_damage_dealt / player_stats.total_games_played
        player_stats.avg_accuracy = player_stats.total_accuracy / player_stats.total_games_played
        player_stats.avg_headshot_accuracy = player_stats.total_headshot_accuracy / player_stats.total_games_played
        player_stats.avg_torso_accuracy = player_stats.total_torso_accuracy / player_stats.total_games_played
        player_stats.avg_leg_accuracy = player_stats.total_leg_accuracy / player_stats.total_games_played
        player_stats.avg_contesting_kills = player_stats.total_contesting_kills / player_stats.total_games_played
        player_stats.avg_objective_time = player_stats.total_objective_time / player_stats.total_games_played
        player_stats.avg_longest_time_alive = player_stats.total_longest_time_alive / player_stats.total_games_played
        player_stats.avg_kills_per_minute = player_stats.total_kills_per_minute / player_stats.total_games_played
        player_stats.avg_deaths_per_minute = player_stats.total_deaths_per_minute / player_stats.total_games_played
        player_stats.avg_assists_per_minute = player_stats.total_assists_per_minute / player_stats.total_games_played
        player_stats.avg_damage_dealt_per_minute = player_stats.total_damage_dealt_per_minute / player_stats.total_games_played
        player_stats.avg_damage_taken_per_minute = player_stats.total_damage_taken_per_minute / player_stats.total_games_played

    player_stats.best_killstreak = max(player_stats.best_killstreak, game_player.killstreak)


"""
Compute initial stats for a player based on their rank and skill multiplier.
"""
def compute_stats(game_type: GameMode, true_rating: float, rank_avg_stats: dict,) -> Dict[str, Any]:
    total_games_played = max(int(random.gauss(rank_avg_stats["mean_total_games_played"], rank_avg_stats["sd_total_games_played"])), 0)
    total_wins = max(int(random.gauss(rank_avg_stats["mean_total_wins"], rank_avg_stats["sd_total_wins"])), 0) if total_games_played > 0 else 0
    total_ties = max(int(random.gauss(rank_avg_stats["mean_total_ties"], rank_avg_stats["sd_total_ties"])), 0) if total_games_played > 0 else 0
    total_loses = total_games_played - total_wins - total_ties
    win_streak = max(int(random.gauss(rank_avg_stats["mean_win_streak"], rank_avg_stats["sd_win_streak"])), 0) if total_wins > 0 else 0
   
    total_accuracy = sum(max(random.gauss(rank_avg_stats["mean_accuracy"], rank_avg_stats["sd_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    if total_accuracy > 0.0 and total_games_played > 0:
        total_kills = sum(int(max(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"]), 0)) for _ in range(total_games_played))
        total_deaths = sum(int(max(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"]), 0)) for _ in range(total_games_played))
        total_assists = sum(int(max(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"]), 0)) for _ in range(total_games_played))
    
    avg_kills = total_kills / total_games_played if total_games_played > 0 else 0.0
    avg_deaths = total_deaths / total_games_played if total_games_played > 0 else 0.0
    avg_assists = total_assists / total_games_played if total_games_played > 0 else 0.0

    total_damage_dealt = 0
    if total_accuracy > 0.0:
        for _ in range(total_games_played):
            total_damage_dealt += sum(int(max(random.gauss(100, 5), 0)) for _ in range(int(avg_kills))) + sum(int(max(random.gauss(35, 34), 0)) for _ in range(int(avg_assists)))
    
    total_damage_taken = 0
    for _ in range(total_games_played):
        total_damage_taken += sum(int(max(random.gauss(100, 5), 0)) for _ in range(int(avg_deaths)))
 
    best_killstreak = 0
    for _ in range(total_games_played):
        best_killstreak = max(best_killstreak, min(int(max(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"]), 0)), total_kills)) if total_kills > 0 else 0

    total_headshot_accuracy = sum(max(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0
    total_torso_accuracy = sum(max(random.gauss(rank_avg_stats["mean_torso_accuracy"], rank_avg_stats["sd_torso_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0
    
    total_damage_missed = 0
    if total_accuracy > 0.0 and total_damage_dealt > 0:
        total_damage_missed = int(total_damage_dealt / total_accuracy - total_damage_dealt)
    else:
        for _ in range(total_games_played):
            total_damage_missed += max(int(random.gauss(rank_avg_stats["mean_damage_missed"], rank_avg_stats["sd_damage_missed"])), 0)

    total_leg_accuracy = total_accuracy - total_headshot_accuracy - total_torso_accuracy

    total_damage = total_damage_dealt + total_damage_missed
    
    total_headshot_damage_dealt = int(total_damage * total_headshot_accuracy)
    total_torso_damage_dealt = int(total_damage * total_torso_accuracy)
    total_leg_damage_dealt = total_damage - total_headshot_damage_dealt - total_torso_damage_dealt

    total_contesting_kills = sum(int(max(random.gauss(rank_avg_stats["mean_contesting_kills"], rank_avg_stats["sd_contesting_kills"]), 0)) for _ in range(total_games_played))
    total_objective_time = sum(int(max(random.gauss(rank_avg_stats["mean_objective_time"], rank_avg_stats["sd_objective_time"]), 0)) for _ in range(total_games_played))
    total_longest_time_alive = sum(int(max(random.gauss(rank_avg_stats["mean_longest_time_alive"], rank_avg_stats["sd_longest_time_alive"]), 0)) for _ in range(total_games_played))

    total_playtime = 0
    for _ in range(total_games_played):
        total_playtime += max(int(random.gauss(game_type.time_limit_mean, game_type.time_limit_variance)), game_type.time_limit_mean - (2 * game_type.time_limit_variance))

    total_kills_per_minute = total_kills / total_playtime * 60 if total_playtime > 0 else 0.0
    total_deaths_per_minute = total_deaths / total_playtime * 60 if total_playtime > 0 else 0.0
    total_assists_per_minute = total_assists / total_playtime * 60 if total_playtime > 0 else 0.0
    total_damage_dealt_per_minute = total_damage_dealt / total_playtime * 60 if total_playtime > 0 else 0.0
    total_damage_taken_per_minute = total_damage_taken / total_playtime * 60 if total_playtime > 0 else 0.0

    total_kill_death_ratio = total_kills / total_deaths if total_deaths > 0 else float(total_kills)
    total_damage_dealt_and_taken_ratio = total_damage_dealt / total_damage_taken if total_damage_taken > 0 else float(total_damage_dealt)
    win_loss_ratio = total_wins / total_loses if total_loses > 0 else float(total_wins)

    avg_headshot_damage_dealt = total_headshot_damage_dealt / total_games_played if total_games_played > 0 else 0.0
    avg_torso_damage_dealt = total_torso_damage_dealt / total_games_played if total_games_played > 0 else 0.0
    avg_leg_damage_dealt = total_leg_damage_dealt / total_games_played if total_games_played > 0 else 0.0
    avg_damage_missed = total_damage_missed / total_games_played if total_games_played > 0 else 0.0
    avg_damage_dealt = total_damage_dealt / total_games_played if total_games_played > 0 else 0.0
    avg_damage_taken = total_damage_taken / total_games_played if total_games_played > 0 else 0.0
    avg_accuracy = total_accuracy # Exception here, because we use accuracy to calculate some values
    avg_headshot_accuracy = total_headshot_accuracy # Exception here, because we use accuracy to calculate some values
    avg_torso_accuracy = total_torso_accuracy # Exception here, because we use accuracy to calculate some values
    avg_leg_accuracy = total_leg_accuracy # Exception here, because we use accuracy to calculate some values
    avg_contesting_kills = total_contesting_kills / total_games_played if total_games_played > 0 else 0.0
    avg_objective_time = total_objective_time / total_games_played if total_games_played > 0 else 0.0
    avg_longest_time_alive = total_longest_time_alive / total_games_played if total_games_played > 0 else 0.0
    avg_kills_per_minute = total_kills_per_minute / total_games_played if total_games_played > 0 else 0.0
    avg_deaths_per_minute = total_deaths_per_minute / total_games_played if total_games_played > 0 else 0.0
    avg_assists_per_minute = total_assists_per_minute / total_games_played if total_games_played > 0 else 0.0
    avg_damage_dealt_per_minute = total_damage_dealt_per_minute / total_games_played if total_games_played > 0 else 0.0
    avg_damage_taken_per_minute = total_damage_taken_per_minute / total_games_played if total_games_played > 0 else 0.0

    return {
        "true_rating": true_rating,

        "total_games_played": total_games_played,
        "total_wins": total_wins,
        "total_ties": total_ties,
        "total_loses": total_loses,
        "win_streak": win_streak,

        "total_kills": total_kills,
        "total_deaths": total_deaths,
        "total_assists": total_assists,

        "avg_kills": avg_kills,
        "avg_deaths": avg_deaths,
        "avg_assists": avg_assists,

        "total_damage_dealt": total_damage_dealt,
        "total_damage_taken": total_damage_taken,
        "best_killstreak": best_killstreak,

        "total_accuracy": total_accuracy,
        "total_headshot_accuracy": total_headshot_accuracy,
        "total_torso_accuracy": total_torso_accuracy,

        "total_damage_missed": total_damage_missed,
        "total_leg_accuracy": total_leg_accuracy,

        "total_headshot_damage_dealt": total_headshot_damage_dealt,
        "total_torso_damage_dealt": total_torso_damage_dealt,
        "total_leg_damage_dealt": total_leg_damage_dealt,

        "total_contesting_kills": total_contesting_kills,
        "total_objective_time": total_objective_time,
        "total_longest_time_alive": total_longest_time_alive,

        "total_kills_per_minute": total_kills_per_minute,
        "total_deaths_per_minute": total_deaths_per_minute,
        "total_assists_per_minute": total_assists_per_minute,
        "total_damage_dealt_per_minute": total_damage_dealt_per_minute,
        "total_damage_taken_per_minute": total_damage_taken_per_minute,

        "total_kill_death_ratio": total_kill_death_ratio,
        "win_loss_ratio": win_loss_ratio,
        "total_damage_dealt_and_taken_ratio": total_damage_dealt_and_taken_ratio,

        "avg_headshot_damage_dealt": avg_headshot_damage_dealt,
        "avg_torso_damage_dealt": avg_torso_damage_dealt,
        "avg_leg_damage_dealt": avg_leg_damage_dealt,
        "avg_damage_missed": avg_damage_missed,
        "avg_damage_dealt": avg_damage_dealt,
        "avg_damage_taken": avg_damage_taken,
        "avg_accuracy": avg_accuracy,
        "avg_headshot_accuracy": avg_headshot_accuracy,
        "avg_torso_accuracy": avg_torso_accuracy,
        "avg_leg_accuracy": avg_leg_accuracy,
        "avg_contesting_kills": avg_contesting_kills,
        "avg_objective_time": avg_objective_time,
        "avg_longest_time_alive": avg_longest_time_alive,
        "avg_kills_per_minute": avg_kills_per_minute,
        "avg_deaths_per_minute": avg_deaths_per_minute,
        "avg_assists_per_minute": avg_assists_per_minute,
        "avg_damage_dealt_per_minute": avg_damage_dealt_per_minute,
        "avg_damage_taken_per_minute": avg_damage_taken_per_minute,
    }


"""
Initialize and simulate game type stats for all players.
"""
def simulate_player_game_type_stats(game_type: GameMode, ref_players_ids: List[int]) -> None: 
    stats_to_create = []
    for player in session.query(Player).all():
        if player.id in ref_players_ids:
            true_rating = REF_INITIAL_TRUE_RATING
        else:
            interval_index = random.choices(range(len(RANK_DISTRIBUTION_WEIGHTS)), weights=RANK_DISTRIBUTION_WEIGHTS)[0]
            true_rating = random.randint(interval_index * 100, interval_index * 100 + 99) * 1.0
        player_stats = get_stat_parameters(game_type, true_rating)
        computed_stats = compute_stats(game_type, true_rating, player_stats)

        stats = PlayerGameTypeStats(
            player_id=player.id,
            created_at=GLOBAL_START_TIME,
            game_type=game_type.type,
            last_time_played=GLOBAL_START_TIME if computed_stats['total_games_played'] > 0 else None,
            **computed_stats
        )
        stats_to_create.append(stats)
    session.add_all(stats_to_create)
    session.commit()
    logger.info("Created stats for all players.")


"""
Simulate games for a given game mode and update player stats.
"""
def simulate_game_mode_games(game_type: GameMode, ref_players_ids: List[int]) -> None:    
    player_count = game_type.team_size * game_type.team_count
    prev_player_party_name = None
    
    for ref_player_id in ref_players_ids: # This is how we test each scenario (every player is every scenario in every combination)
        # Retrieve player's party name and stats
        current_ref_player = session.query(Player).filter_by(id=ref_player_id).first()
        player_party = [current_ref_player]
        player_party_ids = [ref_player_id]



        if prev_player_party_name == current_ref_player.party_name: # Skip player, if he was already in games as a party member
            continue
        else:
            prev_player_party_name = current_ref_player.party_name

        next_player_id = ref_player_id + 1
        
        if current_ref_player.party_name != f"Party_{ref_player_id}":
            if game_type.type in ["FFA", "BR_1V99"]:
                continue

            if "half" in current_ref_player.party_name:
                for _ in range(game_type.group_sizes[0] - 1):
                    player_party.append(session.query(Player).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)
                    next_player_id += 1
            else:
                for _ in range(game_type.group_sizes[1] - 1):
                    player_party.append(session.query(Player).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)
                    next_player_id += 1

        current_time = GLOBAL_START_TIME
        game_number = 1

        for (ref_rating_coeficient, ref_games_count, party_coeficient) in REF_COEF_AND_GAMES[f"player_{ref_player_id}"]:
            for _ in range(ref_games_count):
                game_players_to_insert = []
                filter_time = current_time + HALF_MINUTE

                player_stats = session.query(PlayerGameTypeStats).filter_by(
                    player_id=ref_player_id, game_type=game_type.type
                ).first()

                party_players_stats = session.query(PlayerGameTypeStats).filter(
                    PlayerGameTypeStats.game_type == game_type.type,
                    PlayerGameTypeStats.player_id.in_(player_party_ids),
                ).all()

                exclude_ids = set(ref_players_ids) | set(player_party_ids)
                
                game_players_stats = session.query(PlayerGameTypeStats).filter(
                    PlayerGameTypeStats.true_rating.between(player_stats.true_rating - 50.0,
                                                              player_stats.true_rating + 50.0),
                    PlayerGameTypeStats.game_type == game_type.type,
                    PlayerGameTypeStats.player_id.notin_(exclude_ids),
                    or_(PlayerGameTypeStats.last_time_played == None, PlayerGameTypeStats.last_time_played <= filter_time),
                ).order_by(
                    # asc(func.abs(PlayerGameTypeStats.true_rating - player_stats.true_rating))
                    func.rand()
                ).limit(player_count - len(player_party)).all()

                if len(game_players_stats) < (player_count - len(player_party)):
                    game_players_stats = session.query(PlayerGameTypeStats).filter(
                        PlayerGameTypeStats.true_rating.between(player_stats.true_rating - 100.0,
                                                                  player_stats.true_rating + 100.0),
                        PlayerGameTypeStats.game_type == game_type.type,
                        PlayerGameTypeStats.player_id.notin_(exclude_ids),
                        or_(PlayerGameTypeStats.last_time_played == None, PlayerGameTypeStats.last_time_played <= filter_time),
                    ).order_by(
                        func.rand()
                    ).limit(player_count - len(player_party)).all()
                
                current_time, playtime = simulate_game_time(current_time, game_type)
                
                game = Game(
                    created_at=current_time,
                    type=game_type.type,
                    playtime=playtime,
                    team_count=game_type.team_count,
                    team_size=game_type.team_size,
                    kill_cap=game_type.kill_cap or 0,
                    point_limit=game_type.point_limit or 0,
                    winning_round_limit=game_type.winning_round_limit or 1,
                    player_count=player_count,
                )
                session.add(game)

                for ref_player in party_players_stats:
                    ref_stats = get_stat_parameters(game_type, ref_player.true_rating)
                    ref_stats_calculated = compute_basic_stats(game_type, ref_stats, playtime)

                    game_players_to_insert.append(
                        GamePlayer(
                            created_at=current_time,
                            game=game,
                            player_id=ref_player.player_id,
                            team="Team_1",
                            party_name=ref_player.player.party_name,
                            true_rating_before_game=ref_player.true_rating,
                            **ref_stats_calculated
                        )
                    )
                
                team_player_index = 0
                team_number = 1

                for _ in range(game_type.team_count):
                    already_in_team = len(player_party_ids) if team_number == 1 else 0
                    team_name = f"Team_{team_number}"
                    slots_to_fill = game_type.team_size - already_in_team
                    if team_player_index + slots_to_fill > len(game_players_stats):
                        raise RuntimeError(
                            f"Asked for {slots_to_fill} players, but only "
                            f"{len(game_players_stats) - team_player_index} left."
                        )
                    for _ in range(slots_to_fill):
                        team_player = game_players_stats[team_player_index]
                        team_player_stats = get_stat_parameters(game_type, team_player.true_rating)
                        team_player_stats_calculated = compute_basic_stats(game_type, team_player_stats, playtime)
                        game_players_to_insert.append(
                            GamePlayer(
                                created_at=current_time,
                                game=game,
                                player_id=team_player.player_id,
                                team=team_name,
                                party_name=team_player.player.party_name,
                                true_rating_before_game=team_player.true_rating,
                                **team_player_stats_calculated
                            )
                        )
                        team_player_index += 1
                    team_number += 1

                for game_player in game_players_to_insert:
                    koef = 1.0
                    if game_player.team != 'Team_1':
                        koef = 1.0 + ((1.0 - ref_rating_coeficient) / (player_count - game_type.team_size))
                    elif game_player.player_id in ref_players_ids:
                        if game_player.player_id != ref_player_id:
                            koef = party_coeficient
                        else:
                            koef = ref_rating_coeficient

                    koef_negative = 1.0
                    if game_player.team != 'Team_1':
                        koef_negative = 1.0 * (ref_rating_coeficient / (player_count - game_type.team_size))
                    elif game_player.player_id in ref_players_ids:
                        if game_player.player_id != ref_player_id:
                            koef_negative = 1.0 + (1.0 - party_coeficient)
                        else:
                            koef_negative = 1.0 + (1.0 - ref_rating_coeficient)
    
                    game_player.accuracy = game_player.accuracy * koef
                    game_player.kills = game_player.kills * koef
                    game_player.deaths = game_player.deaths * koef_negative
                    game_player.assists = game_player.assists * koef
                    game_player.damage_dealt = game_player.damage_dealt * koef
                    game_player.damage_taken = game_player.damage_taken * koef_negative
                    game_player.killstreak = game_player.killstreak * koef
                    game_player.headshot_accuracy = game_player.headshot_accuracy * koef
                    game_player.torso_accuracy = game_player.torso_accuracy * koef
                    game_player.leg_accuracy = game_player.leg_accuracy * koef
                    game_player.objective_time = game_player.objective_time * koef
                    game_player.longest_time_alive = game_player.longest_time_alive * koef

                if game_type.type in ["BR_1V99", "BR_4V96"]:
                    all_player_kills = sum(player.kills for player in game_players_to_insert)
                    all_player_deaths = sum(player.deaths for player in game_players_to_insert)

                    all_kill_koeficient = game_type.kill_cap / all_player_kills
                    all_deaths_koeficient = game_type.kill_cap / all_player_deaths

                    longest_alive_player = max(game_players_to_insert, key=lambda player: player.longest_time_alive)

                    time_alive_koeficient = playtime / longest_alive_player.longest_time_alive

                    for player in game_players_to_insert:
                        player.longest_time_alive = int(player.longest_time_alive * time_alive_koeficient)
                        player.kills = int(player.kills * all_kill_koeficient)
                        player.deaths = int(player.deaths * all_deaths_koeficient)
                        player.damage_dealt = int(player.damage_dealt * all_kill_koeficient)
                        player.damage_taken = int(player.damage_taken * all_deaths_koeficient)
                        player.assists = int(player.assists * all_kill_koeficient)
                        player.killstreak = int(player.killstreak * all_kill_koeficient)
                    
                    if game_type.type == "BR_1V99":
                        sorted_players = sorted(game_players_to_insert, key=lambda player: player.longest_time_alive, reverse=True)

                        for idx, player in enumerate(sorted_players):
                            player.team_placement = idx + 1
                            player.deaths = min(idx, 1)
                            if (idx + 1 == 2):
                                player.longest_time_alive = 0.99 * longest_alive_player.longest_time_alive
                            
                    if game_type.type == "BR_4V96":
                        teams = { f"Team_{i+1}" for i in range(game_type.team_count) }

                        teams_best_time_alive = {
                            team: max(player.longest_time_alive for player in game_players_to_insert if player.team == team)
                            for team in teams
                        }

                        sorted_teams = sorted(teams_best_time_alive.items(), key=lambda item: item[1], reverse=True)

                        team_placements = { team: idx + 1 for idx, (team, _) in enumerate(sorted_teams) }

                        second_place_best_time_alive = max(player.longest_time_alive for player in game_players_to_insert if team_placements[player.team] == 2)

                        for player in game_players_to_insert:
                            player.team_placement = team_placements[player.team]
                            player.is_tie = False
                            if player.team_placement == 1 and player.longest_time_alive / longest_alive_player.longest_time_alive >= 0.85:
                                player.longest_time_alive = longest_alive_player.longest_time_alive
                                player.deaths = 0
                            elif player.team_placement == 2 and player.longest_time_alive / second_place_best_time_alive >= 0.85:
                                player.longest_time_alive = (player.longest_time_alive / second_place_best_time_alive) * 0.99 * longest_alive_player.longest_time_alive
                                player.deaths = 1
                            else:
                                player.deaths = 1

                if game_type.type == "FFA":
                    most_kills_player = max(game_players_to_insert, key=lambda player: player.kills)
                    most_kill_player_count = sum(1 for p in game_players_to_insert)

                    game_kill_cap = game_type.kill_cap * 0.8 if most_kill_player_count > 1 else game_type.kill_cap

                    kills_koeficient = game_kill_cap / most_kills_player.kills

                    for player in game_players_to_insert:
                        player.kills = int(player.kills * kills_koeficient)
                        player.damage_dealt = int(player.damage_dealt * kills_koeficient)
                        player.assists = int(player.assists * kills_koeficient)
                        player.killstreak = int(player.killstreak * kills_koeficient)

                    all_player_kills = sum(player.kills for player in game_players_to_insert) # new kill values sum
                    random_sorted_players = random.shuffle(game_players_to_insert)
                    death_weights = [(all_player_kills - player.kills + 1) for player in random_sorted_players]
                    weight_sum = sum(death_weights)

                    for player, weight in zip(game_players_to_insert, death_weights):
                        player_deaths_koeficient = (all_player_kills * weight / weight_sum) / player.deaths if player.deaths else 1
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                        average_time_alive = playtime / player.deaths if player.deaths else playtime
                        if average_time_alive < player.longest_time_alive * kills_koeficient:
                            player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                        else:
                            player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)

                    sorted_players = sorted(game_players_to_insert, key=lambda player: player.kills, reverse=True)
                    placement = 2
                    first_place_count = 0

                    for player in sorted_players:
                        if player.kills == game_kill_cap:
                            player.team_placement = 1
                            first_place_count += 1
                        else:
                            player.team_placement = placement
                            placement += 1

                    for player in sorted_players:
                        if first_place_count > 1 and player.kills == game_kill_cap:
                            player.is_tie = True
                        else:
                            player.is_tie = False

                if game_type.type in ['TDM', 'Domination', 'SAD']:
                    team1_kills = sum(p.kills for p in game_players_to_insert if p.team == "Team_1")
                    team2_kills = sum(p.kills for p in game_players_to_insert if p.team == "Team_2")

                    if game_type.type == 'TDM':
                        kills_koeficient = 1
                        winning_team = "Tie"
                        if team1_kills > team2_kills:
                            kills_koeficient = game_type.kill_cap / team1_kills
                            winning_team = "Team_1"
                        elif team1_kills == team2_kills:
                            kills_koeficient = int(game_type.kill_cap * 0.8) / team1_kills
                        else:
                            kills_koeficient = game_type.kill_cap / team2_kills
                            winning_team = "Team_2"

                        for player in game_players_to_insert:
                            player.kills = int(player.kills * kills_koeficient)
                            player.damage_dealt = int(player.damage_dealt * kills_koeficient)
                            player.assists = int(player.assists * kills_koeficient)
                            player.killstreak = int(player.killstreak * kills_koeficient)

                        team1_new_kills = int(team1_kills * kills_koeficient)
                        team2_new_kills = int(team2_kills * kills_koeficient)
                        team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']
                        team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        team1_sorted = sorted(team1_players, key=lambda player_1: player_1.kills, reverse=True)
                        team2_sorted = sorted(team2_players, key=lambda player_2: player_2.kills, reverse=True)

                        team1_death_weights = [(team1_new_kills - player_1.kills + 1) for player_1 in team1_sorted]
                        team2_death_weights = [(team2_new_kills - player_2.kills + 1) for player_2 in team2_sorted]
                        team1_weight_sum = sum(team1_death_weights)
                        team2_weight_sum = sum(team2_death_weights)

                        for player, weight in zip(team1_sorted, team2_death_weights):
                            player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)
                        
                        for player in game_players_to_insert:
                            if winning_team == 'Tie':
                                player.team_placement = 1
                                player.is_tie = True
                            elif player.team == winning_team:
                                player.team_placement = 1
                                player.is_tie = False
                            else:
                                player.team_placement = 2
                                player.is_tie = False
                        
                    if game_type.type == 'Domination':
                        """
                        Šo pēc tam atrisināt, lai visi kill_caps ir vienā vietā
                        """
                        kill_cap = random.randrange(90, 135 + 1, 1)
                        kills_koeficient = kill_cap / team1_kills if team1_kills >= team2_kills else kill_cap / team2_kills

                        for player in game_players_to_insert:
                            player.kills = int(player.kills * kills_koeficient)
                            player.damage_dealt = int(player.damage_dealt * kills_koeficient)
                            player.assists = int(player.assists * kills_koeficient)
                            player.killstreak = int(player.killstreak * kills_koeficient)

                        team1_new_kills = int(team1_kills * kills_koeficient)
                        team2_new_kills = int(team2_kills * kills_koeficient)
                        team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']
                        team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        team1_sorted = sorted(team1_players, key=lambda player_1: player_1.kills, reverse=True)
                        team2_sorted = sorted(team2_players, key=lambda player_2: player_2.kills, reverse=True)

                        team1_death_weights = [(team1_new_kills - player_1.kills + 1) for player_1 in team1_sorted]
                        team2_death_weights = [(team2_new_kills - player_2.kills + 1) for player_2 in team2_sorted]
                        team1_weight_sum = sum(team1_death_weights)
                        team2_weight_sum = sum(team2_death_weights)

                        for player, weight in zip(team1_sorted, team2_death_weights):
                            player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)

                        team1_domination_points = 0
                        team2_domination_points = 0

                        for player in game_players_to_insert:
                            old_objective_time = player.objective_time
                            player.objective_time = min(max(player.objective_time + 15 * player.kills - 20 * player.deaths, 10), int(0.8 * playtime))
                            objective_time_ratio = player.objective_time / old_objective_time

                            player.contesting_kills = int(player.kills * (min(0.5 * objective_time_ratio, 0.9)))

                            player_domination_points = 1 * (player.kills - player.contesting_kills) + 2 * player.contesting_kills + 6 * (player.objective_time / 10)

                            if player.team == 'Team_1':
                                team1_domination_points += player_domination_points
                            else:
                                team2_domination_points += player_domination_points

                        team1_domination_points = int(team1_domination_points / game_type.team_size)
                        team2_domination_points = int(team2_domination_points / game_type.team_size)

                        winning_team = "Tie"
                        point_koeficient = 1
                        if team1_domination_points > team2_domination_points:
                            point_koeficient = game_type.point_limit / team1_domination_points
                            winning_team = 'Team_1'
                        elif team1_domination_points == team2_domination_points:
                            point_koeficient = (game_type.point_limit * 0.8) / team1_domination_points
                        else:
                            point_koeficient = game_type.point_limit / team2_domination_points
                            winning_team = 'Team_2'

                        for player in game_players_to_insert:
                            points = team1_domination_points if player.team == 'Team_1' else team2_domination_points
                            player.domination_points = point_koeficient * points
                            if winning_team == 'Tie':
                                player.team_placement = 1
                                player.is_tie = True
                            elif player.team == winning_team:
                                player.team_placement = 1
                                player.is_tie = False
                            else:
                                player.team_placement = 2
                                player.is_tie = False

                    if game_type.type == 'SAD':
                        kill_cap = max(random.gauss(game_type.kill_cap, 6), game_type.kill_cap - 15)
                        kills_koeficient = kill_cap / team1_kills if team1_kills >= team2_kills else kill_cap / team2_kills

                        for player in game_players_to_insert:
                            player.kills = int(player.kills * kills_koeficient)
                            player.damage_dealt = int(player.damage_dealt * kills_koeficient)
                            player.assists = int(player.assists * kills_koeficient)
                            player.killstreak = int(player.killstreak * kills_koeficient)

                        team1_new_kills = int(team1_kills * kills_koeficient)
                        team2_new_kills = int(team2_kills * kills_koeficient)
                        team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']
                        team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        team1_sorted = sorted(team1_players, key=lambda player_1: player_1.kills, reverse=True)
                        team2_sorted = sorted(team2_players, key=lambda player_2: player_2.kills, reverse=True)

                        team1_death_weights = [(team1_new_kills - player_1.kills + 1) for player_1 in team1_sorted]
                        team2_death_weights = [(team2_new_kills - player_2.kills + 1) for player_2 in team2_sorted]
                        team1_weight_sum = sum(team1_death_weights)
                        team2_weight_sum = sum(team2_death_weights)

                        for player, weight in zip(team1_sorted, team2_death_weights):
                            player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = int(player.deaths * player_deaths_koeficient)
                            player.damage_taken = int(player.damage_taken * player_deaths_koeficient)

                        team1_new_deaths = sum(p.deaths for p in game_players_to_insert if p.team == "Team_1")
                        team2_new_deaths = sum(p.deaths for p in game_players_to_insert if p.team == "Team_2")
                        all_player_deaths = team1_new_deaths + team2_new_deaths
                        team1_rounds_won = int(team1_new_deaths / all_player_deaths * 30)
                        team2_rounds_won = int(team2_new_deaths / all_player_deaths * 30)
                        winning_team = "Tie"
                        if team1_rounds_won > team2_rounds_won:
                            winning_team = "Team_1"
                        elif team1_rounds_won < team2_rounds_won:
                            winning_team = "Team_2"

                        for player in team2_players:
                            player.rounds_won = team1_rounds_won if player.team == "Team_1" else team2_rounds_won
                            player.rounds_lost = 30 - player.rounds_won
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(int(average_time_alive), int(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = int(player.longest_time_alive * kills_koeficient)
                            
                            if winning_team == 'Tie':
                                player.team_placement = 1
                                player.is_tie = True
                            elif player.team == winning_team:
                                player.team_placement = 1
                                player.is_tie = False
                            else:
                                player.team_placement = 2
                                player.is_tie = False
                                
                
                mvp_attributes = {
                    'most_kills':            (max(game_players_to_insert, key=lambda p: p.kills).player_id, game_type.vp_weights[0]),
                    'least_deaths':          (min(game_players_to_insert, key=lambda p: p.deaths).player_id, game_type.vp_weights[1]),
                    'highest_killstreak':    (max(game_players_to_insert, key=lambda p: p.killstreak).player_id, game_type.vp_weights[2]),
                    'longest_time_alive':    (max(game_players_to_insert, key=lambda p: p.longest_time_alive).player_id, game_type.vp_weights[3]),
                    'most_contesting_kills': (max(game_players_to_insert, key=lambda p: p.contesting_kills).player_id, game_type.vp_weights[4]),
                    'highest_objective_time':(max(game_players_to_insert, key=lambda p: p.objective_time).player_id, game_type.vp_weights[5]),
                    'highest_accuracy':      (max(game_players_to_insert, key=lambda p: p.accuracy).player_id, game_type.vp_weights[6]),
                    'highest_damage_dealt':  (max(game_players_to_insert, key=lambda p: p.damage_dealt).player_id, game_type.vp_weights[7]),
                    'lowest_damage_taken':   (min(game_players_to_insert, key=lambda p: p.damage_taken).player_id, game_type.vp_weights[8]),
                }

                lvp_attributes = {
                    'least_kills':           (min(game_players_to_insert, key=lambda p: p.kills).player_id, game_type.vp_weights[0]),
                    'most_deaths':           (max(game_players_to_insert, key=lambda p: p.deaths).player_id, game_type.vp_weights[1]),
                    'lowest_killstreak':     (min(game_players_to_insert, key=lambda p: p.killstreak).player_id, game_type.vp_weights[2]),
                    'shortest_time_alive':   (min(game_players_to_insert, key=lambda p: p.longest_time_alive).player_id, game_type.vp_weights[3]),
                    'least_contesting_kills':(min(game_players_to_insert, key=lambda p: p.contesting_kills).player_id, game_type.vp_weights[4]),
                    'lowest_objective_time': (min(game_players_to_insert, key=lambda p: p.objective_time).player_id, game_type.vp_weights[5]),
                    'lowest_accuracy':       (min(game_players_to_insert, key=lambda p: p.accuracy).player_id, game_type.vp_weights[6]),
                    'lowest_damage_dealt':   (min(game_players_to_insert, key=lambda p: p.damage_dealt).player_id, game_type.vp_weights[7]),
                    'highest_damage_taken':  (max(game_players_to_insert, key=lambda p: p.damage_taken).player_id, game_type.vp_weights[8]),
                }

                current_mvp = (0, 0.0)
                current_lvp = (0, 0.0)

                STAT_ATTRS = ['kills', 'deaths', 'killstreak', 'longest_time_alive',
                    'contesting_kills', 'objective_time', 'accuracy', 'damage_dealt', 'damage_taken']

                for player in game_players_to_insert:
                    mvp_weight_sum = sum(weight for (pid, weight) in mvp_attributes.values() if player.player_id == pid)

                    if current_mvp[1] < mvp_weight_sum:
                        current_mvp = (player.player_id, mvp_weight_sum)
                    elif current_mvp[1] == mvp_weight_sum:
                        mvp_player = next((p for p in game_players_to_insert if p.player_id == current_mvp[0]), None)

                        if mvp_player is None:
                            current_mvp = (player.player_id, mvp_weight_sum)
                            continue

                        better_stats_count = 0
                        for attr in STAT_ATTRS:
                            if attr in ['deaths', 'damage_taken']:
                                better_stats_count += 1 if getattr(player, attr) < getattr(mvp_player, attr) else 0
                            else:
                                better_stats_count += 1 if getattr(player, attr) > getattr(mvp_player, attr) else 0
                            
                        if better_stats_count > len(STAT_ATTRS) / 2:
                            current_mvp = (player.player_id, mvp_weight_sum)

                for player in game_players_to_insert:
                    if player.player_id == current_mvp[0]:
                        continue

                    lvp_weight_sum = sum(weight for (pid, weight) in lvp_attributes.values() if player.player_id == pid)

                    if current_lvp[1] < lvp_weight_sum:
                        current_lvp = (player.player_id, lvp_weight_sum)
                    elif current_lvp[1] == lvp_weight_sum:
                        lvp_player = next((p for p in game_players_to_insert if p.player_id == current_lvp[0]), None)

                        if lvp_player is None:
                            current_lvp = (player.player_id, lvp_weight_sum)
                            continue

                        better_stats_count = 0
                        for attr in STAT_ATTRS:
                            if attr in ['deaths', 'damage_taken']:
                                better_stats_count += 1 if getattr(player, attr) > getattr(lvp_player, attr) else 0
                            else:
                                better_stats_count += 1 if getattr(player, attr) < getattr(lvp_player, attr) else 0
                            
                        if better_stats_count > len(STAT_ATTRS) / 2:
                            current_lvp = (player.player_id, lvp_weight_sum)

                new_game_players_to_insert = []
                for game_player in game_players_to_insert:
                    is_mvp = bool(game_player.player_id == current_mvp[0])
                    is_lvp = bool(game_player.player_id == current_lvp[0])
                    player_stats = get_stat_parameters(game_type, game_player.true_rating_before_game)
                    game_player_game_type_stats = session.query(PlayerGameTypeStats).filter(
                        PlayerGameTypeStats.player_id == game_player.player_id,
                    ).first()
                    player_stats_calculated = compute_remaining_stats(game_player, playtime, is_mvp, is_lvp)

                    new_game_player = GamePlayer(
                        created_at=current_time,
                        game=game,
                        player_id=game_player.player_id,
                        team=game_player.team,
                        party_name=game_player.party_name,
                        true_rating_before_game=game_player.true_rating_before_game,
                        **player_stats_calculated
                    )
                    new_game_player.true_rating_after_game = calculate_ranking(game_type, new_game_player, game_player_game_type_stats, player_stats)

                    new_game_players_to_insert.append(new_game_player)
                
                game_players_to_insert = new_game_players_to_insert
                
                logger.info(f"Inserting {len(game_players_to_insert)} game player records for game {game_number} in mode {game_type.type} in bulk...")
                session.add_all(game_players_to_insert)
                session.commit()
                logger.info("Game player records inserted.")
                
                # Update player stats for all game players inserted:
                for game_player in game_players_to_insert:
                    p_stats = session.query(PlayerGameTypeStats).filter_by(
                        player_id=game_player.player_id, game_type=game_type.type
                    ).first()
                    update_player_stats(p_stats, game_player)
                session.commit()
                logger.info(f"Player stats updated for game {game_number}.")
                game_number += 1


"""
Main simulation function to create players, initialize stats, and simulate games.
"""
def simulate_all_modes() -> None:
    players_to_create = []
    ref_players_ids = list(range(1, REFERENCE_PLAYER_COUNT + 1))
    logger.info("Creating players...")
    
    created_player_count = session.query(Player).count()
    if created_player_count < TOTAL_PLAYERS:
        for player_id_index in range(1, TOTAL_PLAYERS + 1):
            party_name = f"Party_{player_id_index}" # default/solo party name
            for id_range, name in SCENARIO_PLAYER_PARTIES:
                if player_id_index in id_range:
                    party_name = name
                    break
            players_to_create.append(Player(id=player_id_index, name=f"Player_{player_id_index}", party_name=party_name))
    
        session.add_all(players_to_create)
        session.commit()
        logger.info(f"Created {len(players_to_create)} players.")

        for game_type in GAME_TYPES:
            logger.info(f"Creating {game_type.type} stats for players")
            simulate_player_game_type_stats(game_type, ref_players_ids)
            logger.info(f"{game_type.type} stats for players finished!")
    else:
        logger.info("Players already created")
    
    for game_type in GAME_TYPES:
        logger.info(f"Starting simulation for game type: {game_type.type}")
        simulate_game_mode_games(game_type, ref_players_ids)
        logger.info(f"Completed simulation for game type: {game_type.type}")
