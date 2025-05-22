import os
import math
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Tuple

import trueskill

from ..database.db_setup import engine, SessionLocal
from ..database.models5 import Base, Game5, GamePlayer5, Player5, PlayerGameTypeStats5
from ..config5 import (
    GameMode,
    GAME_GAP,
    ONE_WEEK,
    ONE_YEAR,
    BASE_BETA,
    BASE_TAU,
    STAT_ATTRS,
    GAME_TYPES,
    HALF_MINUTE,
    TS_MIN_SIGMA,
    TS_MAX_SIGMA,
    GLICKO_MIN_RD,
    GLICKO_MAX_RD,
    RANK_AVERAGES,
    TOTAL_PLAYERS,
    STARTING_PLAYER,
    TOTAL_ATTRIBUTES,
    GLOBAL_START_TIME,
    REF_COEF_AND_GAMES,
    REFERENCE_PLAYER_COUNT,
    REF_INITIAL_TRUE_RATING,
    SCENARIO_PLAYER_PARTIES,
    DISTRIBUTION,
    # RANK_DISTRIBUTION_WEIGHTS, # Uncomment this, if you want to use distributions
    ZeroFloorElo,
    ZeroFloorGlicko,
    roundInt,
    ensure_utc,
    get_stat_parameters
)

seed = os.getenv("SEED") # Set a seed inside .env file to always get the same outcomes for testing purposes.
if seed is not None:
    random.seed(int(seed))

# Logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = SessionLocal() # Setup SQLAlchemy engine and session for creating records

Base.metadata.create_all(engine) # Creates tables, if none exist

"""
Simulate the passage of time for a game.
"""
def simulate_game_time(prev_time: datetime, game_type: GameMode) -> Tuple[datetime, int]:
    mean = game_type.time_limit_mean
    variance = game_type.time_limit_variance
    playtime = max(roundInt(random.gauss(mean, variance)), mean - (2 * variance))
    new_time = prev_time + timedelta(seconds=playtime) + GAME_GAP
    return new_time, playtime


def compute_game_player_stats(game_type: GameMode, rank_avg_stats: dict, playtime: int) -> Dict[str, Any]:
    # Random Gausian values based on averages for rank
    accuracy = max(random.gauss((rank_avg_stats["mean_accuracy"]), (rank_avg_stats["sd_accuracy"])), 0.0)
    
    kills = max(roundInt(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"])), 0) if accuracy > 0.0 else 0
    deaths = max(roundInt(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"])), 0)
    assists = max(roundInt(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"])), 0) if accuracy > 0.0 else 0

    damage_dealt = sum(roundInt(max(random.gauss(100, 5), 0)) for _ in range(kills)) + sum(roundInt(max(random.gauss(35, 34), 0)) for _ in range(assists)) if accuracy > 0.0 else 0
    damage_taken = max(sum(roundInt(random.gauss(100, 5)) for _ in range(deaths)), 0)
    killstreak = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        killstreak = kills
    else:
        killstreak = min(kills, max(roundInt(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"])), 0))

    headshot_accuracy = max(min(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]), accuracy), 0.0)
    torso_accuracy = max(min(random.gauss(rank_avg_stats["mean_torso_accuracy"], rank_avg_stats["sd_torso_accuracy"]), accuracy - headshot_accuracy), 0.0) if accuracy > 0.0 else 0.0

    # Calculatable values
    damage_missed = roundInt((damage_dealt / accuracy) - damage_dealt) if accuracy > 0.0 and damage_dealt > 0 else max(roundInt(random.gauss(rank_avg_stats["mean_damage_missed"], rank_avg_stats["sd_damage_missed"])), 0)
    leg_accuracy = accuracy - headshot_accuracy - torso_accuracy if accuracy > 0.0 else 0.0

    total_damage = damage_dealt + damage_missed

    headshot_damage_dealt = roundInt(total_damage * headshot_accuracy)
    torso_damage_dealt = roundInt(total_damage * torso_accuracy)
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
        objective_time = min(max(roundInt(random.gauss(rank_avg_stats["mean_objective_time"], rank_avg_stats["sd_objective_time"])), 10), roundInt(0.8 * playtime))

    longest_time_alive = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        longest_time_alive_min = roundInt(rank_avg_stats["mean_longest_time_alive"]) - roundInt(rank_avg_stats["sd_longest_time_alive"])
        if longest_time_alive_min > playtime:
            longest_time_alive = playtime
        else:
            longest_time_alive = max(roundInt(random.randrange(longest_time_alive_min, playtime + 1, 1)), 20)
    elif game_type.type == 'SAD':
        longest_time_alive_min = roundInt(rank_avg_stats["mean_longest_time_alive"]) - roundInt(rank_avg_stats["sd_longest_time_alive"])
        if longest_time_alive_min > roundInt(playtime / 30) + 101:
            longest_time_alive = roundInt(playtime / 30) + 101
        else:
            longest_time_alive = max(roundInt(random.randrange(longest_time_alive_min, roundInt(playtime / 30) + 101, 1)), 20)
    else:
        longest_time_alive = max(roundInt(random.gauss(rank_avg_stats["mean_longest_time_alive"], rank_avg_stats["sd_longest_time_alive"])), 10)

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


def compute_remaining_game_player_stats(game_player: GamePlayer5, playtime: int, is_mvp: bool, is_lvp: bool) -> Dict[str, Any]:
    damage_missed = roundInt((game_player.damage_dealt / game_player.accuracy) - game_player.damage_dealt) if game_player.accuracy else 0

    total_damage = damage_missed + game_player.damage_dealt

    headshot_damage_dealt = roundInt(total_damage * game_player.headshot_accuracy)
    torso_damage_dealt = roundInt(total_damage * game_player.torso_accuracy)
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
    elo_after = 0.0
    glicko_rating_after = 0.0
    glicko_rd_after = GLICKO_MAX_RD

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
        "elo_after": elo_after,
        "glicko_rating_after": glicko_rating_after,
        "glicko_rd_after": glicko_rd_after,
    }

def calculate_game_player_rating(game_type: GameMode, game_player: GamePlayer5, player_stats: PlayerGameTypeStats5, player_average_stats: dict, team_elo, team_glicko, game_players_to_insert) -> int:
    total_avg_deltas = {}

    for (attr, koef) in TOTAL_ATTRIBUTES:
        if getattr(player_stats, f"avg_{attr}") > 0:
            total_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * (getattr(game_player, attr) - getattr(player_stats, f"avg_{attr}")) / getattr(player_stats, f"avg_{attr}")
        else:
            total_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * 1.0 if getattr(game_player, attr) > 0.0 else 0.0

    if player_stats.best_killstreak > 0:
        total_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * (game_player.killstreak - player_stats.best_killstreak) / player_stats.best_killstreak
    else:
        total_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * 1.0 if game_player.killstreak > 0 else 0.0
   
    if player_stats.total_kill_death_ratio > 0:
        total_avg_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * (game_player.kill_death_ratio - player_stats.total_kill_death_ratio) / player_stats.total_kill_death_ratio
    else:
        total_avg_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * 1.0 if game_player.kill_death_ratio > 0.0 else 0.0

    if player_stats.total_damage_dealt_and_taken_ratio > 0:
        total_avg_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * (game_player.damage_dealt_and_taken_ratio - player_stats.total_damage_dealt_and_taken_ratio) / player_stats.total_damage_dealt_and_taken_ratio
    else:
        total_avg_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * 1.0 if game_player.damage_dealt_and_taken_ratio > 0.0 else 0.0

    rank_avg_deltas = {}

    for (attr, koef) in RANK_AVERAGES:
        if player_stats.total_games_played == 0:
            rank_avg_deltas[f"delta_{attr}"] = 0.0
        elif player_average_stats[f"mean_{attr}"] > 0:
            rank_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * (getattr(game_player, attr) - player_average_stats[f"mean_{attr}"]) / player_average_stats[f"mean_{attr}"]
        else:
            rank_avg_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * 1.0 if getattr(game_player, attr) > 0.0 else 0.0

    if player_stats.total_games_played == 0:
        rank_avg_deltas["delta_killstreak"] = 0.0
    elif player_average_stats["mean_best_killstreak"] > 0:
        rank_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * (game_player.killstreak - player_average_stats["mean_best_killstreak"]) / player_average_stats["mean_best_killstreak"]
    else:
        rank_avg_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * 1.0 if game_player.killstreak > 0 else 0.0

    if player_stats.total_games_played == 0:
        rank_avg_deltas["delta_win_streak"] = 0.0
    elif player_average_stats["mean_win_streak"] > 0:
        rank_avg_deltas["delta_win_streak"] = game_type.rank_delta_weights["win_streak"] * (player_stats.win_streak - player_average_stats["mean_win_streak"]) / player_average_stats["mean_win_streak"]
    else:
        rank_avg_deltas["delta_win_streak"] = game_type.rank_delta_weights["win_streak"] * 1.0 if player_stats.win_streak > 0 else 0.0

    opponent_weight = 0

    for each_player in game_players_to_insert:
        if each_player.player_id == game_player.player_id:
            continue
        else:
            player_deltas = {}

            for (attr, koef) in TOTAL_ATTRIBUTES:
                if getattr(each_player, attr) > 0:
                    player_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * (getattr(game_player, attr) - getattr(each_player, attr)) / getattr(each_player, attr)
                else:
                    player_deltas[f"delta_{attr}"] = koef * game_type.rank_delta_weights[attr] * 1.0 if getattr(game_player, attr) > 0.0 else 0.0

            if each_player.killstreak > 0:
                player_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * (game_player.killstreak - each_player.killstreak) / each_player.killstreak
            else:
                player_deltas["delta_killstreak"] = game_type.rank_delta_weights["killstreak"] * 1.0 if game_player.killstreak > 0 else 0.0
          
            if each_player.kill_death_ratio > 0:
                player_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * (game_player.kill_death_ratio - each_player.kill_death_ratio) / each_player.kill_death_ratio
            else:
                player_deltas["delta_kill_death_ratio"] = game_type.rank_delta_weights["kill_death_ratio"] * 1.0 if game_player.kill_death_ratio > 0.0 else 0.0

            if each_player.damage_dealt_and_taken_ratio > 0:
                player_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * (game_player.damage_dealt_and_taken_ratio - each_player.damage_dealt_and_taken_ratio) / each_player.damage_dealt_and_taken_ratio
            else:
                player_deltas["delta_damage_dealt_and_taken_ratio"] = game_type.rank_delta_weights["damage_dealt_and_taken_ratio"] * 1.0 if game_player.damage_dealt_and_taken_ratio > 0.0 else 0.0

            opponent_weight += sum(player_deltas.values()) / len(player_deltas)

    opponent_weight = opponent_weight / (game_type.team_size * game_type.team_count - 1)

    other_deltas = {}

    other_deltas["delta_win_loss_ratio"] = game_type.rank_delta_weights["win_loss_ratio"] * (player_stats.win_loss_ratio - 0.5) / 0.5 if player_stats.total_games_played > 0 else 0.0

    other_deltas["delta_is_most_valuable_player"] = roundInt(game_player.is_most_valuable_player is True) * 1.0

    other_deltas["delta_is_least_valuable_player"] = roundInt(game_player.is_least_valuable_player is True) * -1.0
    
    win_deltas = {}
    
    mid = (game_type.team_count + 1) / 2
    range_from_mid   = (game_type.team_count - 1) / 2

    if range_from_mid == 0:
        win_deltas["delta_placement"] = 0
    else:
        win_deltas["delta_placement"] = ((mid - game_player.team_placement) / range_from_mid)

    win_deltas["delta_tie"] = game_type.rank_delta_weights["is_tie"] * -0.5 if game_player.is_tie is True else game_type.rank_delta_weights["is_tie"] * 0.5

    
    total_avg_weight = 0.13 * sum(total_avg_deltas.values()) / len(total_avg_deltas)
    rank_avg_weight = 0.10 * sum(rank_avg_deltas.values()) / len(rank_avg_deltas)
    other_metric_weight = 0.27 * sum(other_deltas.values()) / len(other_deltas)
    opponent_weight = 0.43 * opponent_weight
    win_metric_weight = 0.07 * sum(win_deltas.values()) / len(win_deltas)

    performance_weight = total_avg_weight + rank_avg_weight + other_metric_weight + win_metric_weight + opponent_weight

    utc_created_at = ensure_utc(game_player.created_at)
    
    uncertainty_duration = (utc_created_at - ensure_utc(player_stats.last_time_played)).total_seconds()

    TWO_WEEKS = 1209600 # in seconds

    uncertainty_koef = 2 ** (-uncertainty_duration / TWO_WEEKS)

    gameplay_koef = math.exp(-0.0004 * player_stats.total_games_played)

    rating_koef = math.exp(-0.00025 * game_player.true_rating_before_game)

    base_p = game_type.base_performance * (max((1.5 - uncertainty_koef) * ((gameplay_koef + rating_koef) / 2), 0.3)) # Decay goes from 0.5 to 1.5 for new players and falls to 0.3 constant, if player is experienced or has played for a long time.

    true_rating_after_game = max(game_player.true_rating_before_game + (base_p * performance_weight), 0.0)

    final_elo = 0.0
    final_glicko_rating = 0.0
    final_glicko_rd = 0.0
    
    for team_index in range(game_type.team_count):
        if game_player.team == f"Team_{team_index + 1}":
            continue
        else:
            gp_elo_rating = game_player.elo_before
            opp_elo_rating = team_elo[f"Team_{team_index + 1}"]['initial_rating']
            gp_glicko_rating = game_player.glicko_rating_before
            gp_glicko_rd = game_player.glicko_rd_before
            opp_glicko_rating = team_glicko[f"Team_{team_index + 1}"]['initial_rating']

            gp = ZeroFloorElo(initial_rating=gp_elo_rating if gp_elo_rating > 0 else 0, k_factor=team_elo[game_player.team]['k_factor'])
            opp = ZeroFloorElo(initial_rating=opp_elo_rating if opp_elo_rating > 0 else 0, k_factor=team_elo[f"Team_{team_index + 1}"]['k_factor'])
            
            opp_placement = next(p.team_placement for p in game_players_to_insert if p.team == f"Team_{team_index + 1}")
            
            if game_player.team_placement < opp_placement:
                gp.beat(opp)
            elif game_player.team_placement == opp_placement:
                gp.tied(opp)
            elif game_player.team_placement > opp_placement:
                opp.beat(gp)

            final_elo += gp.rating

            gp = ZeroFloorGlicko(
                initial_rating=gp_glicko_rating if gp_glicko_rating > 0 else 0,
                initial_rd=gp_glicko_rd if gp_glicko_rd > GLICKO_MIN_RD else GLICKO_MIN_RD,
                initial_time=ensure_utc(player_stats.last_time_played),
            )
            opp = ZeroFloorGlicko(
                initial_rating=opp_glicko_rating if opp_glicko_rating > 0 else 0,
                initial_rd=team_glicko[f"Team_{team_index + 1}"]['initial_rd'],
                initial_time=team_glicko[f"Team_{team_index + 1}"]['initial_time'],
            )

            if game_player.team_placement < opp_placement:
                gp.beat(opp, utc_created_at)
            elif game_player.team_placement == opp_placement:
                gp.tied(opp, utc_created_at)
            elif game_player.team_placement > opp_placement:
                opp.beat(gp, utc_created_at)
            
            final_glicko_rating += gp.rating
            final_glicko_rd += gp.rd

    divider = game_type.team_count - 1
    
    final_elo = final_elo / divider if divider != 0 else final_elo
    final_glicko_rating = final_glicko_rating / divider if divider != 0 else final_glicko_rating
    final_glicko_rd = final_glicko_rd / divider if divider != 0 else final_glicko_rd
    if final_glicko_rd < GLICKO_MIN_RD:
        final_glicko_rd = GLICKO_MIN_RD
    elif final_glicko_rd > GLICKO_MAX_RD:
        final_glicko_rd = GLICKO_MAX_RD
    
    return true_rating_after_game, final_elo, final_glicko_rating, final_glicko_rd

"""
Update aggregated player stats based on the results of a game.
"""
def update_player_game_type_stats(player_stats: PlayerGameTypeStats5, game_player: GamePlayer5) -> None:
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

    # Decay lowers by a week after each game and doesn't go further than a year ago.
    player_stats.last_time_played = min(created_at, max(created_at - ONE_YEAR, ensure_utc(player_stats.last_time_played) + ONE_WEEK))

    player_stats.true_rating = game_player.true_rating_after_game
    player_stats.elo_rating = game_player.elo_after
    player_stats.glicko_rating = game_player.glicko_rating_after
    player_stats.glicko_rd = game_player.glicko_rd_after
    player_stats.ts_rating = game_player.ts_rating_after
    player_stats.ts_volatility = game_player.ts_volatility_after

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
def compute_player_game_type_stats(game_type: GameMode, true_rating: float, rank_avg_stats: dict,) -> Dict[str, Any]:
    total_games_played = max(roundInt(random.gauss(rank_avg_stats["mean_total_games_played"], rank_avg_stats["sd_total_games_played"])), 0)
    total_wins = max(roundInt(random.gauss(rank_avg_stats["mean_total_wins"], rank_avg_stats["sd_total_wins"])), 0) if total_games_played > 0 else 0
    total_ties = max(roundInt(random.gauss(rank_avg_stats["mean_total_ties"], rank_avg_stats["sd_total_ties"])), 0) if total_games_played > 0 else 0
    total_loses = total_games_played - total_wins - total_ties
    win_streak = max(roundInt(random.gauss(rank_avg_stats["mean_win_streak"], rank_avg_stats["sd_win_streak"])), 0) if total_wins > 0 else 0
   
    total_accuracy = sum(max(random.gauss(rank_avg_stats["mean_accuracy"], rank_avg_stats["sd_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    if total_accuracy > 0.0 and total_games_played > 0:
        total_kills = sum(roundInt(max(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"]), 0)) for _ in range(total_games_played))
        total_deaths = sum(roundInt(max(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"]), 0)) for _ in range(total_games_played))
        total_assists = sum(roundInt(max(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"]), 0)) for _ in range(total_games_played))
    
    avg_kills = total_kills / total_games_played if total_games_played > 0 else 0.0
    avg_deaths = total_deaths / total_games_played if total_games_played > 0 else 0.0
    avg_assists = total_assists / total_games_played if total_games_played > 0 else 0.0

    total_damage_dealt = 0
    if total_accuracy > 0.0:
        for _ in range(total_games_played):
            total_damage_dealt += sum(roundInt(max(random.gauss(100, 5), 0)) for _ in range(roundInt(avg_kills))) + sum(roundInt(max(random.gauss(35, 34), 0)) for _ in range(roundInt(avg_assists)))
    
    total_damage_taken = 0
    for _ in range(total_games_played):
        total_damage_taken += sum(roundInt(max(random.gauss(100, 5), 0)) for _ in range(roundInt(avg_deaths)))
 
    best_killstreak = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        best_killstreak = total_kills
    else:
        for _ in range(total_games_played):
            best_killstreak = max(best_killstreak, min(roundInt(max(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"]), 0)), total_kills)) if total_kills > 0 else 0

    total_headshot_accuracy = sum(max(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0
    total_torso_accuracy = sum(max(random.gauss(rank_avg_stats["mean_torso_accuracy"], rank_avg_stats["sd_torso_accuracy"]), 0.0) for _ in range(total_games_played)) / (total_games_played) if total_games_played > 0 else 0.0
    
    total_damage_missed = 0
    if total_accuracy > 0.0 and total_damage_dealt > 0:
        total_damage_missed = roundInt(total_damage_dealt / total_accuracy - total_damage_dealt)
    else:
        for _ in range(total_games_played):
            total_damage_missed += max(roundInt(random.gauss(rank_avg_stats["mean_damage_missed"], rank_avg_stats["sd_damage_missed"])), 0)

    total_leg_accuracy = total_accuracy - total_headshot_accuracy - total_torso_accuracy

    total_damage = total_damage_dealt + total_damage_missed
    
    total_headshot_damage_dealt = roundInt(total_damage * total_headshot_accuracy)
    total_torso_damage_dealt = roundInt(total_damage * total_torso_accuracy)
    total_leg_damage_dealt = total_damage - total_headshot_damage_dealt - total_torso_damage_dealt

    total_contesting_kills = sum(roundInt(max(random.gauss(rank_avg_stats["mean_contesting_kills"], rank_avg_stats["sd_contesting_kills"]), 0)) for _ in range(total_games_played))
    total_objective_time = sum(roundInt(max(random.gauss(rank_avg_stats["mean_objective_time"], rank_avg_stats["sd_objective_time"]), 0)) for _ in range(total_games_played))
    total_longest_time_alive = sum(roundInt(max(random.gauss(rank_avg_stats["mean_longest_time_alive"], rank_avg_stats["sd_longest_time_alive"]), 0)) for _ in range(total_games_played))

    total_playtime = 0
    for _ in range(total_games_played):
        total_playtime += max(roundInt(random.gauss(game_type.time_limit_mean, game_type.time_limit_variance)), game_type.time_limit_mean - (2 * game_type.time_limit_variance))

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

    elo_rating = true_rating
    glicko_rating = true_rating
    ts_rating = true_rating

    if total_games_played == 0:
        glicko_rd = GLICKO_MAX_RD
        ts_volatility = TS_MAX_SIGMA
    else:
        glicko_rd = GLICKO_MIN_RD
        ts_volatility = TS_MIN_SIGMA
        

    return {
        "true_rating": true_rating,
        "elo_rating": elo_rating,
        "glicko_rating": glicko_rating,
        "glicko_rd": glicko_rd,
        "ts_rating": ts_rating,
        "ts_volatility": ts_volatility,

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
    interval_index = 0
    player_id_countdown = DISTRIBUTION # Remove this if you want to use distributions
    for player in session.query(Player5).all():
        if player.id in ref_players_ids:
            true_rating = REF_INITIAL_TRUE_RATING
        else:
            if player_id_countdown == 0: # Remove this if you want to use distributions
                interval_index += 1 # Remove this if you want to use distributions
                player_id_countdown = DISTRIBUTION - 1 # Remove this if you want to use distributions
            # interval_index = random.choices(range(len(RANK_DISTRIBUTION_WEIGHTS)), weights=RANK_DISTRIBUTION_WEIGHTS)[0] # Uncomment this, if you want to use distributions
            true_rating = random.randint(interval_index * 100, interval_index * 100 + 99) * 1.0
        player_stats = get_stat_parameters(game_type, true_rating)
        computed_stats = compute_player_game_type_stats(game_type, true_rating, player_stats)

        stats = PlayerGameTypeStats5(
            player_id=player.id,
            created_at=GLOBAL_START_TIME,
            game_type=game_type.type,
            last_time_played=GLOBAL_START_TIME if computed_stats['total_games_played'] > 0 else GLOBAL_START_TIME - ONE_YEAR,
            **computed_stats
        )
        stats_to_create.append(stats)
        player_id_countdown -= 1
    session.add_all(stats_to_create)
    session.commit()
    logger.info("Created stats for all players.")


"""
Simulate games for a given game mode and update player stats.
"""
def simulate_game_mode_games(game_type: GameMode, ref_players_ids: List[int], env) -> None:    
    player_count = game_type.team_size * game_type.team_count
    prev_player_party_name = None

    total_games_number = 1
    for ref_player_id in ref_players_ids: # This is how we test each scenario (every player is every scenario in every combination)
        if ref_player_id != STARTING_PLAYER:
            for player_game_type_stat in session.query(PlayerGameTypeStats5).all():
                player_game_type_stat.last_time_played = GLOBAL_START_TIME
        # Retrieve player's party name and stats
        current_ref_player = session.query(Player5).filter_by(id=ref_player_id).first()
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
                    player_party.append(session.query(Player5).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)
                    next_player_id += 1
            else:
                for _ in range(game_type.group_sizes[1] - 1):
                    player_party.append(session.query(Player5).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)
                    next_player_id += 1

        current_time = GLOBAL_START_TIME
        game_number = 1

        for (ref_rating_coeficient, ref_games_count, party_coeficient, time_gap, k_factor) in REF_COEF_AND_GAMES[f"player_{ref_player_id}"]:
            gap_added = False
            for _ in range(ref_games_count):
                game_players_to_insert = []
                filter_time = current_time + HALF_MINUTE

                party_players_stats = session.query(PlayerGameTypeStats5).filter(
                    PlayerGameTypeStats5.game_type == game_type.type,
                    PlayerGameTypeStats5.player_id.in_(player_party_ids),
                ).all()

                player_stats = next(game_type_stats for game_type_stats in party_players_stats if game_type_stats.player_id == ref_player_id)

                if not player_stats:
                    raise ValueError(f"Missing stats for player_{ref_player_id}")

                if not gap_added:
                    player_stats.last_time_played -= timedelta(days=time_gap)
                    gap_added = True

                search_rating = sum(p.true_rating for p in party_players_stats) / len(party_players_stats)

                exclude_ids = set(ref_players_ids) | set(player_party_ids)
                
                unsorted_game_players_stats = session.query(PlayerGameTypeStats5).filter(
                    PlayerGameTypeStats5.true_rating.between(search_rating - 50.0,
                                                              search_rating + 50.0),
                    PlayerGameTypeStats5.game_type == game_type.type,
                    PlayerGameTypeStats5.player_id.notin_(exclude_ids),
                    PlayerGameTypeStats5.last_time_played <= filter_time,
                ).limit(player_count - len(player_party)).all()

                if len(unsorted_game_players_stats) < (player_count - len(player_party)):
                    unsorted_game_players_stats = session.query(PlayerGameTypeStats5).filter(
                        PlayerGameTypeStats5.true_rating.between(search_rating - 100.0,
                                                                  search_rating + 100.0),
                        PlayerGameTypeStats5.game_type == game_type.type,
                        PlayerGameTypeStats5.player_id.notin_(exclude_ids),
                        PlayerGameTypeStats5.last_time_played <= filter_time,
                    ).limit(player_count - len(player_party)).all()

                if len(unsorted_game_players_stats) < (player_count - len(player_party)):
                    raise RuntimeError(
                        f"Ref player #{ref_player_id}.\n"
                        f"Game mode: {game_type.type}.\n"
                        f"Total games: {total_games_number}.\n"
                        f"Game #: {game_number}.\n"
                        f"Asked for {player_count - len(player_party)} players, but only "
                        f"{len(unsorted_game_players_stats)} left."
                    )
                
                game_players_stats = random.sample(unsorted_game_players_stats, player_count - len(player_party))
                
                current_time, playtime = simulate_game_time(current_time, game_type)
                
                game = Game5(
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
                session.flush()

                for ref_player in party_players_stats:
                    ref_stats = get_stat_parameters(game_type, ref_player.true_rating)
                    ref_stats_calculated = compute_game_player_stats(game_type, ref_stats, playtime)
                    
                    idle_days = roundInt((ensure_utc(current_time) - ensure_utc(ref_player.last_time_played)).days)
                    inflated_ts_volatility = math.sqrt(ref_player.ts_volatility**2 + (idle_days * env.tau**2))

                    game_players_to_insert.append(
                        GamePlayer5(
                            created_at=current_time,
                            game_id=game.id,
                            player_id=ref_player.player_id,
                            team="Team_1",
                            party_name=ref_player.player5.party_name,
                            true_rating_before_game=ref_player.true_rating,
                            elo_before=ref_player.elo_rating,
                            glicko_rating_before=ref_player.glicko_rating,
                            glicko_rd_before=ref_player.glicko_rd,
                            ts_rating_before=ref_player.ts_rating,
                            ts_volatility_before=inflated_ts_volatility,
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
                            f"Ref player #{ref_player_id}.\n"
                            f"Game mode: {game_type.type}.\n"
                            f"Total games: {total_games_number}.\n"
                            f"Game #: {game_number}.\n"
                            f"Asked for {slots_to_fill} players, but only "
                            f"{len(game_players_stats) - team_player_index} left."
                        )
                    for _ in range(slots_to_fill):
                        team_player = game_players_stats[team_player_index]
                        team_player_stats = get_stat_parameters(game_type, team_player.true_rating)
                        team_player_stats_calculated = compute_game_player_stats(game_type, team_player_stats, playtime)

                        idle_days = roundInt((ensure_utc(current_time) - ensure_utc(team_player.last_time_played)).days)
                        inflated_ts_volatility = math.sqrt(team_player.ts_volatility**2 + (idle_days * env.tau**2))

                        game_players_to_insert.append(
                            GamePlayer5(
                                created_at=current_time,
                                game_id=game.id,
                                player_id=team_player.player_id,
                                team=team_name,
                                party_name=team_player.player5.party_name,
                                true_rating_before_game=team_player.true_rating,
                                elo_before=team_player.elo_rating,
                                glicko_rating_before=team_player.glicko_rating,
                                glicko_rd_before=team_player.glicko_rd,
                                ts_rating_before=team_player.ts_rating,
                                ts_volatility_before=inflated_ts_volatility,
                                **team_player_stats_calculated
                            )
                        )
                        team_player_index += 1
                    team_number += 1

                team_elo = {}
                team_glicko = {}
                players_stats = party_players_stats + game_players_stats

                for team_index in range(game_type.team_count):
                    
                    team_elo[f"Team_{team_index + 1}"] = {
                        "initial_rating": sum(p.elo_before for p in game_players_to_insert if p.team == f"Team_{team_index + 1}") / game_type.team_size,
                        "k_factor": k_factor,
                    }

                    total_time = sum(ensure_utc(p.last_time_played).timestamp() for p, gp in zip(players_stats, game_players_to_insert) if gp.team == f"Team_{team_index + 1}") / game_type.team_size
                    
                    team_glicko[f"Team_{team_index + 1}"] = {
                        "initial_rating": sum(p.glicko_rating_before for p in game_players_to_insert if p.team == f"Team_{team_index + 1}") / game_type.team_size,
                        "initial_rd": sum(p.glicko_rd_before for p in game_players_to_insert if p.team == f"Team_{team_index + 1}") / game_type.team_size,
                        "initial_time": datetime.fromtimestamp(total_time, tz=timezone.utc),
                    }

                for game_player in game_players_to_insert:
                    koef = 1.0
                    if ref_rating_coeficient != 1.0: #game_player.team != 'Team_1':
                        # koef = 1.0 + ((1.0 - ref_rating_coeficient) / 2)
                        koef = 0.95 if ref_rating_coeficient > 1.0 else 1.05
                    if game_player.player_id in ref_players_ids:
                        if game_player.player_id != ref_player_id:
                            koef = party_coeficient
                        else:
                            koef = ref_rating_coeficient

                    koef_negative = 1.0
                    if ref_rating_coeficient != 1.0: #game_player.team != 'Team_1':
                        # koef_negative = 1.0 - ((1.0 - ref_rating_coeficient) / 2)
                        koef_negative = 1.05 if ref_rating_coeficient > 1.0 else 0.95
                    if game_player.player_id in ref_players_ids:
                        if game_player.player_id != ref_player_id:
                            koef_negative = 1.0 + (1.0 - party_coeficient)
                        else:
                            koef_negative = 1.0 + (1.0 - ref_rating_coeficient)
    
                    game_player.accuracy = (game_player.accuracy + 0.1) * koef if game_player.accuracy == 0.0 else game_player.accuracy * koef
                    game_player.kills = roundInt((game_player.kills + 0.5) * koef) if game_player.kills == 0 else roundInt(game_player.kills * koef)
                    game_player.deaths = roundInt((game_player.deaths + 0.5) * koef_negative) if game_player.deaths == 0 else roundInt(game_player.deaths * koef_negative)
                    game_player.assists = roundInt((game_player.assists + 0.5) * koef) if game_player.assists == 0 else roundInt(game_player.assists * koef)
                    game_player.damage_dealt = roundInt((game_player.damage_dealt + 0.5) * koef) if game_player.damage_dealt == 0 else roundInt(game_player.damage_dealt * koef)
                    game_player.damage_taken = roundInt((game_player.damage_taken + 0.5) * koef_negative) if game_player.damage_taken == 0 else roundInt(game_player.damage_taken * koef_negative)
                    game_player.killstreak = roundInt((game_player.killstreak + 0.5) * koef) if game_player.killstreak == 0 else roundInt(game_player.killstreak * koef)
                    game_player.headshot_accuracy = (game_player.headshot_accuracy + 0.033) * koef if game_player.headshot_accuracy == 0.0 else game_player.headshot_accuracy * koef
                    game_player.torso_accuracy = (game_player.torso_accuracy + 0.034) * koef if game_player.torso_accuracy == 0.0 else game_player.torso_accuracy * koef
                    game_player.leg_accuracy = (game_player.leg_accuracy + 0.033) * koef if game_player.leg_accuracy == 0.0 else game_player.leg_accuracy * koef
                    game_player.objective_time = roundInt((game_player.objective_time + 0.5) * koef) if game_player.objective_time == 0 else roundInt(game_player.objective_time * koef)
                    game_player.longest_time_alive = roundInt((game_player.longest_time_alive + 0.5) * koef) if game_player.longest_time_alive == 0 else roundInt(game_player.longest_time_alive * koef)

                if game_type.type in ["BR_1V99", "BR_4V96"]:
                    all_player_kills = sum(player.kills for player in game_players_to_insert)
                    all_player_deaths = sum(player.deaths for player in game_players_to_insert)

                    all_kill_koeficient = game_type.kill_cap / all_player_kills
                    all_deaths_koeficient = game_type.kill_cap / all_player_deaths

                    longest_alive_player = max(game_players_to_insert, key=lambda player: player.longest_time_alive)

                    time_alive_koeficient = playtime / longest_alive_player.longest_time_alive

                    for player in game_players_to_insert:
                        player.longest_time_alive = roundInt((player.longest_time_alive + 0.5) * time_alive_koeficient) if player.longest_time_alive == 0 else roundInt(player.longest_time_alive * time_alive_koeficient)
                        player.kills = roundInt((player.kills + 0.5) * all_kill_koeficient) if player.kills == 0 else roundInt(player.kills * all_kill_koeficient)
                        player.damage_dealt = roundInt((player.damage_dealt + 0.5) * all_kill_koeficient) if player.damage_dealt == 0 else roundInt(player.damage_dealt * all_kill_koeficient)
                        player.damage_taken = roundInt((player.damage_taken + 0.5) * all_deaths_koeficient) if player.damage_taken == 0 else roundInt(player.damage_taken * all_deaths_koeficient)
                        player.assists = roundInt((player.assists + 0.5) * all_kill_koeficient) if player.assists == 0 else roundInt(player.assists * all_kill_koeficient)
                        player.killstreak = roundInt((player.killstreak + 0.5) * all_kill_koeficient) if player.killstreak == 0 else roundInt(player.killstreak * all_kill_koeficient)
                    
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
                        player.kills = roundInt((player.kills + 0.5) * kills_koeficient) if player.kills == 0 else roundInt(player.kills * kills_koeficient)
                        player.damage_dealt = roundInt((player.damage_dealt + 0.5) * kills_koeficient) if player.damage_dealt == 0 else roundInt(player.damage_dealt * kills_koeficient)
                        player.assists = roundInt((player.assists + 0.5) * kills_koeficient) if player.assists == 0 else roundInt(player.assists * kills_koeficient)
                        player.killstreak = roundInt((player.killstreak + 0.5) * kills_koeficient) if player.killstreak == 0 else roundInt(player.killstreak * kills_koeficient)

                    all_player_kills = sum(player.kills for player in game_players_to_insert)
                    random_sorted_players = random.sample(game_players_to_insert, k=len(game_players_to_insert))
                    death_weights = [(all_player_kills - player.kills + 1) for player in random_sorted_players]
                    weight_sum = sum(death_weights)

                    for player, weight in zip(game_players_to_insert, death_weights):
                        player_deaths_koeficient = (all_player_kills * weight / weight_sum) / player.deaths if player.deaths else 1
                        player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                        player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                        average_time_alive = playtime / player.deaths if player.deaths else playtime
                        if average_time_alive < player.longest_time_alive * kills_koeficient:
                            player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                        else:
                            player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)

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
                            kills_koeficient = roundInt(game_type.kill_cap * 0.8) / team1_kills
                        else:
                            kills_koeficient = game_type.kill_cap / team2_kills
                            winning_team = "Team_2"

                        for player in game_players_to_insert:
                            player.kills = roundInt((player.kills + 0.5) * kills_koeficient) if player.kills == 0 else roundInt(player.kills * kills_koeficient)
                            player.damage_dealt = roundInt((player.damage_dealt + 0.5) * kills_koeficient) if player.damage_dealt == 0 else roundInt(player.damage_dealt * kills_koeficient)
                            player.assists = roundInt((player.assists + 0.5) * kills_koeficient) if player.assists == 0 else roundInt(player.assists * kills_koeficient)
                            player.killstreak = roundInt((player.killstreak + 0.5) * kills_koeficient) if player.killstreak == 0 else roundInt(player.killstreak * kills_koeficient)

                        team1_new_kills = roundInt(team1_kills * kills_koeficient)
                        team2_new_kills = roundInt(team2_kills * kills_koeficient)
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
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)
                        
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
                            player.kills = roundInt((player.kills + 0.5) * kills_koeficient) if player.kills == 0 else roundInt(player.kills * kills_koeficient)
                            player.damage_dealt = roundInt((player.damage_dealt + 0.5) * kills_koeficient) if player.damage_dealt == 0 else roundInt(player.damage_dealt * kills_koeficient)
                            player.assists = roundInt((player.assists + 0.5) * kills_koeficient) if player.assists == 0 else roundInt(player.assists * kills_koeficient)
                            player.killstreak = roundInt((player.killstreak + 0.5) * kills_koeficient) if player.killstreak == 0 else roundInt(player.killstreak * kills_koeficient)

                        team1_new_kills = roundInt(team1_kills * kills_koeficient)
                        team2_new_kills = roundInt(team2_kills * kills_koeficient)
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
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)

                        team1_domination_points = 0
                        team2_domination_points = 0

                        for player in game_players_to_insert:
                            old_objective_time = player.objective_time
                            player.objective_time = min(max(player.objective_time + 15 * player.kills - 20 * player.deaths, 10), roundInt(0.8 * playtime))
                            objective_time_ratio = player.objective_time / old_objective_time if old_objective_time else 1

                            player.contesting_kills = roundInt(player.kills * (min(0.5 * objective_time_ratio, 0.9)))

                            player_domination_points = 1 * (player.kills - player.contesting_kills) + 2 * player.contesting_kills + 6 * (player.objective_time / 10)

                            if player.team == 'Team_1':
                                team1_domination_points += player_domination_points
                            else:
                                team2_domination_points += player_domination_points

                        team1_domination_points = roundInt(team1_domination_points / game_type.team_size)
                        team2_domination_points = roundInt(team2_domination_points / game_type.team_size)

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
                            player.kills = roundInt((player.kills + 0.5) * kills_koeficient) if player.kills == 0 else roundInt(player.kills * kills_koeficient)
                            player.damage_dealt = roundInt((player.damage_dealt + 0.5) * kills_koeficient) if player.damage_dealt == 0 else roundInt(player.damage_dealt * kills_koeficient)
                            player.assists = roundInt((player.assists + 0.5) * kills_koeficient) if player.assists == 0 else roundInt(player.assists * kills_koeficient)
                            player.killstreak = roundInt((player.killstreak + 0.5) * kills_koeficient) if player.killstreak == 0 else roundInt(player.killstreak * kills_koeficient)

                        team1_new_kills = roundInt(team1_kills * kills_koeficient)
                        team2_new_kills = roundInt(team2_kills * kills_koeficient)
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
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)
                            
                        for player, weight in zip(team2_sorted, team1_death_weights):
                            player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths if player.deaths else 1
                            player.deaths = roundInt(player.deaths * player_deaths_koeficient)
                            player.damage_taken = roundInt(player.damage_taken * player_deaths_koeficient)

                        team1_new_deaths = sum(p.deaths for p in game_players_to_insert if p.team == "Team_1")
                        team2_new_deaths = sum(p.deaths for p in game_players_to_insert if p.team == "Team_2")
                        all_player_deaths = team1_new_deaths + team2_new_deaths
                        team1_rounds_won = roundInt(team1_new_deaths / all_player_deaths * 30)
                        team2_rounds_won = roundInt(team2_new_deaths / all_player_deaths * 30)
                        winning_team = "Tie"
                        if team1_rounds_won > team2_rounds_won:
                            winning_team = "Team_1"
                        elif team1_rounds_won < team2_rounds_won:
                            winning_team = "Team_2"

                        for player in game_players_to_insert:
                            player.rounds_won = team1_rounds_won if player.team == "Team_1" else team2_rounds_won
                            player.rounds_lost = 30 - player.rounds_won
                            average_time_alive = playtime / player.deaths if player.deaths else playtime
                            if average_time_alive < player.longest_time_alive * kills_koeficient:
                                player.longest_time_alive = random.randrange(roundInt(average_time_alive), roundInt(player.longest_time_alive * kills_koeficient) + 1, 1)
                            else:
                                player.longest_time_alive = roundInt(player.longest_time_alive * kills_koeficient)
                            
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
                    'most_kills':            (max(game_players_to_insert, key=lambda p: p.kills).player_id, game_type.vp_weights['kills']),
                    'least_deaths':          (min(game_players_to_insert, key=lambda p: p.deaths).player_id, game_type.vp_weights['deaths']),
                    'highest_killstreak':    (max(game_players_to_insert, key=lambda p: p.killstreak).player_id, game_type.vp_weights['killstreak']),
                    'longest_time_alive':    (max(game_players_to_insert, key=lambda p: p.longest_time_alive).player_id, game_type.vp_weights['time_alive']),
                    'most_contesting_kills': (max(game_players_to_insert, key=lambda p: p.contesting_kills).player_id, game_type.vp_weights['contesting_kills']),
                    'highest_objective_time':(max(game_players_to_insert, key=lambda p: p.objective_time).player_id, game_type.vp_weights['objective_time']),
                    'highest_accuracy':      (max(game_players_to_insert, key=lambda p: p.accuracy).player_id, game_type.vp_weights['accuracy']),
                    'highest_damage_dealt':  (max(game_players_to_insert, key=lambda p: p.damage_dealt).player_id, game_type.vp_weights['damage_dealt']),
                    'lowest_damage_taken':   (min(game_players_to_insert, key=lambda p: p.damage_taken).player_id, game_type.vp_weights['damage_taken']),
                }

                lvp_attributes = {
                    'least_kills':           (min(game_players_to_insert, key=lambda p: p.kills).player_id, game_type.vp_weights['kills']),
                    'most_deaths':           (max(game_players_to_insert, key=lambda p: p.deaths).player_id, game_type.vp_weights['deaths']),
                    'lowest_killstreak':     (min(game_players_to_insert, key=lambda p: p.killstreak).player_id, game_type.vp_weights['killstreak']),
                    'shortest_time_alive':   (min(game_players_to_insert, key=lambda p: p.longest_time_alive).player_id, game_type.vp_weights['time_alive']),
                    'least_contesting_kills':(min(game_players_to_insert, key=lambda p: p.contesting_kills).player_id, game_type.vp_weights['contesting_kills']),
                    'lowest_objective_time': (min(game_players_to_insert, key=lambda p: p.objective_time).player_id, game_type.vp_weights['objective_time']),
                    'lowest_accuracy':       (min(game_players_to_insert, key=lambda p: p.accuracy).player_id, game_type.vp_weights['accuracy']),
                    'lowest_damage_dealt':   (min(game_players_to_insert, key=lambda p: p.damage_dealt).player_id, game_type.vp_weights['damage_dealt']),
                    'highest_damage_taken':  (max(game_players_to_insert, key=lambda p: p.damage_taken).player_id, game_type.vp_weights['damage_taken']),
                }

                current_mvp = (0, 0.0)
                current_lvp = (0, 0.0)

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

                ranks = []
                teams_ratings = []
                player_teams = []

                for team_index in range(game_type.team_count):
                    team_ratings = []
                    team_players = []
                    for p in game_players_to_insert:
                        if p.team == f"Team_{team_index + 1}":
                            team_ratings.append(env.Rating(mu=p.ts_rating_before, sigma = p.ts_volatility_before))
                            team_players.append(p)

                    ranks.append(team_players[0].team_placement - 1)

                    player_teams.append(team_players)
                    
                    teams_ratings.append(team_ratings)

                updated_ts_ratings = env.rate(teams_ratings, ranks)

                for team_ratings, team_players in zip(updated_ts_ratings, player_teams):
                    for rating, gp in zip(team_ratings, team_players):
                        gp.ts_rating_after    = rating.mu
                        gp.ts_volatility_after = rating.sigma

                game_type_stats_by_player_id = {p.player_id: p for p in party_players_stats + game_players_stats}

                for game_player in game_players_to_insert:
                    is_mvp = bool(game_player.player_id == current_mvp[0])
                    is_lvp = bool(game_player.player_id == current_lvp[0])
                    player_stats = get_stat_parameters(game_type, game_player.true_rating_before_game)
                    game_player_game_type_stats = game_type_stats_by_player_id[game_player.player_id]
                    player_stats_calculated = compute_remaining_game_player_stats(game_player, playtime, is_mvp, is_lvp)

                    for calculated_stat, val in player_stats_calculated.items():
                        setattr(game_player, calculated_stat, val)

                    game_player.true_rating_after_game, game_player.elo_after, game_player.glicko_rating_after, game_player.glicko_rd_after = calculate_game_player_rating(game_type, game_player, game_player_game_type_stats, player_stats, team_elo, team_glicko, game_players_to_insert)
                
                logger.info(f"Inserting {len(game_players_to_insert)} game player records for game {game_number} in mode {game_type.type} in bulk...")
                session.add_all(game_players_to_insert)
                logger.info("Game player records inserted.")
                
                # Update player stats for all game players inserted:
                for game_player in game_players_to_insert:
                    p_stats = game_type_stats_by_player_id[game_player.player_id] 
                    update_player_game_type_stats(p_stats, game_player)
                session.commit()
                logger.info(f"Player stats updated for game {game_number}.")
                game_number += 1
        total_games_number += 1

"""
Main simulation function to create players, initialize stats, and simulate games.
"""
def simulate_all_modes() -> None:
    players_to_create = []
    ref_players_ids = list(range(STARTING_PLAYER, REFERENCE_PLAYER_COUNT + 1))
    logger.info("Creating players...")
    
    created_player_count = session.query(Player5).count()
    if created_player_count < TOTAL_PLAYERS:
        for player_id_index in range(1, TOTAL_PLAYERS + 1):
            party_name = f"Party_{player_id_index}" # default/solo party name
            for id_range, name in SCENARIO_PLAYER_PARTIES:
                if player_id_index in id_range:
                    party_name = name
                    break
            players_to_create.append(Player5(id=player_id_index, name=f"Player_{player_id_index}", party_name=party_name))
    
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
        if game_type.type in ['BR_1V99', 'BR_4V96']:
            draw_probability = 0
        else:
            draw_probability = 0.01
        env = trueskill.TrueSkill(
          mu = 0.0,
          sigma = TS_MAX_SIGMA,
          beta = BASE_BETA, 
          tau = BASE_TAU,
          draw_probability = draw_probability
        )
        logger.info(f"Starting simulation for game type: {game_type.type}")
        simulate_game_mode_games(game_type, ref_players_ids, env)
        logger.info(f"Completed simulation for game type: {game_type.type}")
