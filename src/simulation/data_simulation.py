import random
import logging
import datetime
from typing import Dict, Any, List, Tuple

from sqlalchemy import asc, func, or_
from ..database.db_setup import engine, SessionLocal
from ..database.models import Base, Game, GamePlayer, Player, PlayerGameTypeStats
from ..config import (
    GameMode,
    GAME_GAP,
    GAME_TYPES,
    TOTAL_PLAYERS,
    GLOBAL_START_TIME,
    REFERENCE_PLAYER_COUNT,
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
def simulate_game_time(prev_time: datetime.datetime, game_type: GameMode) -> Tuple[datetime.datetime, int]:
    mean = game_type.time_limit_mean
    variance = game_type.time_limit_variance
    playtime = int(random.gauss(mean, variance))
    new_time = prev_time + datetime.timedelta(seconds=playtime) + GAME_GAP
    return new_time, playtime


def compute_basic_stats(game_type: GameMode, player_stats: PlayerGameTypeStats, rank_avg_stats: dict, playtime: int) -> Dict[str, Any]:
    # Random Gausian values based on averages for rank
    kills = int(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"]))
    deaths = int(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"]))
    assists = int(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"]))
    damage_dealt = sum(int(random.gauss(100, 5)) for i in range(kills)) + sum(int(random.gauss(35, 34)) for i in range(assists))
    damage_taken = sum(int(random.gauss(100, 5)) for i in range(deaths))
    killstreak = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        killstreak = kills
    else:
        killstreak = min(kills, int(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"])))

    accuracy = random.gauss((rank_avg_stats["mean_accuracy"]), (rank_avg_stats["sd_accuracy"])) / 100
    headshot_accuracy = min(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]) / 100, accuracy)
    torso_accuracy = min(random.gauss(rank_avg_stats["mean_torso_and_arm_accuracy"], rank_avg_stats["sd_torso_and_arm_accuracy"]) / 100, accuracy - headshot_accuracy)

    # Calculatable values
    damage_missed = int((damage_dealt / accuracy) - damage_dealt)
    leg_accuracy = accuracy - headshot_accuracy - torso_accuracy

    headshot_damage_dealt = int(damage_dealt * headshot_accuracy)
    torso_and_arm_damage_dealt = int(damage_dealt * torso_accuracy)
    leg_damage_dealt = damage_dealt - headshot_damage_dealt - torso_and_arm_damage_dealt

    kills_per_minute = kills / playtime * 60 if playtime else 0
    deaths_per_minute = deaths / playtime * 60 if playtime else 0
    assists_per_minute = assists / playtime * 60 if playtime else 0
    damage_dealt_per_minute = damage_dealt / playtime * 60 if playtime else 0
    damage_taken_per_minute = damage_taken / playtime * 60 if playtime else 0

    kill_death_ratio = kills / deaths if deaths else 0
    damage_dealt_and_taken_ratio = damage_dealt / damage_taken if damage_taken else 0

    # Averages
    avg_kills_delta = ((player_stats.total_kills + kills) / (player_stats.total_games_played + 1)) - player_stats.avg_kills
    avg_deaths_delta = ((player_stats.total_deaths + deaths) / (player_stats.total_games_played + 1)) - player_stats.avg_deaths
    avg_assists_delta = ((player_stats.total_assists + assists) / (player_stats.total_games_played + 1)) - player_stats.avg_assists
    avg_damage_dealt_delta = ((player_stats.total_damage_dealt + damage_dealt) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_dealt
    avg_damage_taken_delta = ((player_stats.total_damage_taken + damage_taken) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_taken
    avg_damage_missed_delta = ((player_stats.total_damage_missed + damage_missed) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_missed

    objective_time = min(max(int(random.gauss(rank_avg_stats["mean_objective_time"], rank_avg_stats["sd_objective_time"])), 10), int(0.8 * playtime))

    longest_time_alive = 0
    if game_type.type in ['BR_1V99', 'BR_4V96']:
        longest_time_alive = random.randrange(rank_avg_stats["mean_longest_time_alive"] - rank_avg_stats["sd_longest_time_alive"], playtime + 1, 1)
    elif game_type.type == 'SAD':
        longest_time_alive = random.randrange(rank_avg_stats["mean_longest_time_alive"] - rank_avg_stats["sd_longest_time_alive"], int(playtime / 30) + 101, 1)
    else:
        longest_time_alive = int(random.gauss(rank_avg_stats["mean_longest_time_alive"], rank_avg_stats["sd_longest_time_alive"]))

    return {
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "killstreak": killstreak,

        "headshot_damage_dealt": headshot_damage_dealt,
        "torso_and_arm_damage_dealt": torso_and_arm_damage_dealt,
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

        "avg_kills_delta": avg_kills_delta,
        "avg_deaths_delta": avg_deaths_delta,
        "avg_assists_delta": avg_assists_delta,
        "avg_damage_dealt_delta": avg_damage_dealt_delta,
        "avg_damage_taken_delta": avg_damage_taken_delta,
        "avg_damage_missed_delta": avg_damage_missed_delta,

        "objective_time": objective_time,
        "longest_time_alive": longest_time_alive,
    }


def compute_remaining_stats(game_player: GamePlayer, player_stats: PlayerGameTypeStats, playtime: int, is_mvp: bool, is_lvp: bool) -> Dict[str, Any]:
    damage_missed = int((game_player.damage_dealt / game_player.accuracy) - game_player.damage_dealt)

    headshot_damage_dealt = int(game_player.damage_dealt * game_player.headshot_accuracy)
    torso_and_arm_damage_dealt = int(game_player.damage_dealt * game_player.torso_accuracy)
    leg_damage_dealt = game_player.damage_dealt - headshot_damage_dealt - torso_and_arm_damage_dealt

    kills_per_minute = game_player.kills / playtime * 60 if playtime else 0
    deaths_per_minute = game_player.deaths / playtime * 60 if playtime else 0
    assists_per_minute = game_player.assists / playtime * 60 if playtime else 0
    damage_dealt_per_minute = game_player.damage_dealt / playtime * 60 if playtime else 0
    damage_taken_per_minute = game_player.damage_taken / playtime * 60 if playtime else 0

    kill_death_ratio = game_player.kills / game_player.deaths if game_player.deaths else 0
    damage_dealt_and_taken_ratio = game_player.damage_dealt / game_player.damage_taken if game_player.damage_taken else 0

    # Averages
    avg_kills_delta = ((player_stats.total_kills + game_player.kills) / (player_stats.total_games_played + 1)) - player_stats.avg_kills
    avg_deaths_delta = ((player_stats.total_deaths + game_player.deaths) / (player_stats.total_games_played + 1)) - player_stats.avg_deaths
    avg_assists_delta = ((player_stats.total_assists + game_player.assists) / (player_stats.total_games_played + 1)) - player_stats.avg_assists
    avg_damage_dealt_delta = ((player_stats.total_damage_dealt + game_player.damage_dealt) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_dealt
    avg_damage_taken_delta = ((player_stats.total_damage_taken + game_player.damage_taken) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_taken
    avg_damage_missed_delta = ((player_stats.total_damage_missed + damage_missed) / (player_stats.total_games_played + 1)) - player_stats.avg_damage_missed

    is_most_valuable_player = is_mvp
    is_least_valuable_player = is_lvp

    true_rating_after_game = 0 # Need to think of a combination of all the performance metrics that create the new rank.

    return {
        "damage_missed": damage_missed,

        "headshot_damage_dealt": headshot_damage_dealt,
        "torso_and_arm_damage_dealt": torso_and_arm_damage_dealt,
        "leg_damage_dealt": leg_damage_dealt,

        "kills_per_minute": kills_per_minute,
        "deaths_per_minute": deaths_per_minute,
        "assists_per_minute": assists_per_minute,
        "damage_dealt_per_minute": damage_dealt_per_minute,
        "damage_taken_per_minute": damage_taken_per_minute,

        "kill_death_ratio": kill_death_ratio,
        "damage_dealt_and_taken_ratio": damage_dealt_and_taken_ratio,

        "avg_kills_delta": avg_kills_delta,
        "avg_deaths_delta": avg_deaths_delta,
        "avg_assists_delta": avg_assists_delta,
        "avg_damage_dealt_delta": avg_damage_dealt_delta,
        "avg_damage_taken_delta": avg_damage_taken_delta,
        "avg_damage_missed_delta": avg_damage_missed_delta,

        "is_most_valuable_player": is_most_valuable_player,
        "is_least_valuable_player": is_least_valuable_player,

        "true_rating_after_game": true_rating_after_game,
    }


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

    player_stats.last_time_played = game_player.created_at
    player_stats.true_rating = game_player.true_rating_after_game
    player_stats.total_headshot_damage += game_player.headshot_damage_dealt
    player_stats.total_torso_and_arm_damage += game_player.torso_and_arm_damage_dealt
    player_stats.total_leg_damage += game_player.leg_damage_dealt

    total_damage = player_stats.total_damage_dealt + player_stats.total_damage_missed

    if total_damage > 0:
        player_stats.total_accuracy = player_stats.total_damage_dealt / total_damage
        player_stats.headshot_accuracy = player_stats.total_headshot_damage / total_damage
        player_stats.torso_accuracy = player_stats.total_torso_and_arm_damage / total_damage
        player_stats.leg_accuracy = player_stats.total_leg_damage / total_damage

    if player_stats.total_games_played:
        player_stats.avg_damage_dealt = player_stats.total_damage_dealt / player_stats.total_games_played
        player_stats.avg_damage_taken = player_stats.total_damage_taken / player_stats.total_games_played
        player_stats.avg_damage_missed = player_stats.total_damage_missed / player_stats.total_games_played
        player_stats.avg_kills = player_stats.total_kills / player_stats.total_games_played
        player_stats.avg_deaths = player_stats.total_deaths / player_stats.total_games_played
        player_stats.avg_assists = player_stats.total_assists / player_stats.total_games_played
        player_stats.total_kill_death_ratio = player_stats.total_kills / player_stats.total_deaths if player_stats.total_deaths else 0

    player_stats.best_killstreak = max(player_stats.best_killstreak, game_player.killstreak)


"""
Compute initial stats for a player based on their rank and skill multiplier.
"""
def compute_stats(true_rating: int, rank_avg_stats: dict,) -> Dict[str, Any]:
    total_games_played = int(random.gauss(rank_avg_stats["mean_total_games_played"], rank_avg_stats["sd_total_games_played"]))
    total_wins = int(random.gauss(rank_avg_stats["mean_total_wins"], rank_avg_stats["sd_total_wins"]))
    total_ties = int(random.gauss(rank_avg_stats["mean_total_ties"], rank_avg_stats["sd_total_ties"]))
    total_loses = total_games_played - total_wins - total_ties
    win_streak = int(random.gauss(rank_avg_stats["mean_win_streak"], rank_avg_stats["sd_win_streak"]))
   
    total_kills = sum(int(random.gauss(rank_avg_stats["mean_kills"], rank_avg_stats["sd_kills"])) for i in range(total_games_played))
    total_deaths = sum(int(random.gauss(rank_avg_stats["mean_deaths"], rank_avg_stats["sd_deaths"])) for i in range(total_games_played))
    total_assists = sum(int(random.gauss(rank_avg_stats["mean_assists"], rank_avg_stats["sd_assists"])) for i in range(total_games_played))
    
    avg_kills = total_kills / total_games_played if total_games_played else 0
    avg_deaths = total_deaths / total_games_played if total_games_played else 0
    avg_assists = total_assists / total_games_played if total_games_played else 0
    
    total_damage_dealt = 0
    for i in range(total_games_played):
        total_damage_dealt += sum(int(random.gauss(100, 5)) for i in range(int(avg_kills))) + sum(int(random.gauss(35, 34)) for i in range(int(avg_assists)))
    
    total_damage_taken = 0
    for i in range(total_games_played):
        total_damage_taken += sum(int(random.gauss(100, 5)) for i in range(int(avg_deaths)))
 
    best_killstreak = 0
    for i in range(total_games_played):
        best_killstreak = max(best_killstreak, int(random.gauss(rank_avg_stats["mean_best_killstreak"], rank_avg_stats["sd_best_killstreak"])))

    total_accuracy = sum(random.gauss((rank_avg_stats["mean_accuracy"]), (rank_avg_stats["sd_accuracy"])) for i in range(total_games_played)) / (total_games_played * 100)
    headshot_accuracy = sum(random.gauss(rank_avg_stats["mean_headshot_accuracy"], rank_avg_stats["sd_headshot_accuracy"]) for i in range(total_games_played)) / (total_games_played * 100)
    torso_accuracy = sum(random.gauss(rank_avg_stats["mean_torso_and_arm_accuracy"], rank_avg_stats["sd_torso_and_arm_accuracy"]) for i in range(total_games_played)) / (total_games_played * 100)
    
    total_damage_missed = int(total_damage_dealt / total_accuracy - total_damage_dealt)
    leg_accuracy = total_accuracy - headshot_accuracy - torso_accuracy
    
    total_headshot_damage = int(total_damage_dealt * headshot_accuracy)
    total_torso_and_arm_damage = int(total_damage_dealt * torso_accuracy)
    total_leg_damage = total_damage_dealt - total_headshot_damage - total_torso_and_arm_damage

    avg_damage_missed = total_damage_missed / total_games_played if total_games_played else 0
    avg_damage_dealt = total_damage_dealt / total_games_played if total_games_played else 0
    avg_damage_taken = total_damage_taken / total_games_played if total_games_played else 0
    total_kill_death_ratio = total_kills / total_deaths if total_deaths else 0
    win_loss_ratio = total_wins / total_loses if total_loses else 0

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
        "headshot_accuracy": headshot_accuracy,
        "torso_accuracy": torso_accuracy,

        "total_damage_missed": total_damage_missed,
        "leg_accuracy": leg_accuracy,

        "total_headshot_damage": total_headshot_damage,
        "total_torso_and_arm_damage": total_torso_and_arm_damage,
        "total_leg_damage": total_leg_damage,

        "avg_damage_missed": avg_damage_missed,
        "avg_damage_dealt": avg_damage_dealt,
        "avg_damage_taken": avg_damage_taken,
        "total_kill_death_ratio": total_kill_death_ratio,
        "win_loss_ratio": win_loss_ratio,
    }


"""
Initialize and simulate game type stats for all players.
"""
def simulate_player_game_type_stats(game_type: GameMode, ref_players_ids: List[int]) -> None:
    rank_weights = [
        0.0280, 0.0462, 0.0771, 0.0714, 0.0614, 0.0509, 0.0545, 0.0568,
        0.0630, 0.0585, 0.0551, 0.0546, 0.0510, 0.0508, 0.0424, 0.0356,
        0.0317, 0.0263, 0.0234, 0.0168, 0.0126, 0.0097, 0.0067, 0.0052,
        0.0037, 0.0028, 0.0014, 0.0005, 0.0003, 0.0002, 0.0002, 0.0002,
        0.0002, 0.0002, 0.0002, 0.0002, 0.0002
    ]
    
    stats_to_create = []
    for player in session.query(Player).all():
        if player.id in ref_players_ids:
            stats = PlayerGameTypeStats(
                player_id=player.id,
                game_type=game_type.type,
                last_time_played=None
            )
        else:
            interval_index = random.choices(range(len(rank_weights)), weights=rank_weights)[0]
            true_rating = random.randint(interval_index * 100, interval_index * 100 + 99)
            player_stats = get_stat_parameters(game_type, true_rating)
            computed_stats = compute_stats(true_rating, player_stats)

            stats = PlayerGameTypeStats(
                player_id=player.id,
                created_at=GLOBAL_START_TIME,
                game_type=game_type.type,
                last_time_played=GLOBAL_START_TIME,
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
    logger.info(f"Simulating {game_type.simulated_games_count} games for mode {game_type.type}")
    prev_player_party_name = None
    
    for player_id in ref_players_ids: # This is how we test each scenario (every player is every scenario)
        # Retrieve player's party name and stats
        player_obj = session.query(Player).filter_by(id=player_id).first()
        player_party = [player_obj]
        player_party_ids = [player_id]

        if prev_player_party_name == player_obj.party_name:
            continue
        else:
            prev_player_party_name = player_obj.party_name
        
        if player_obj.party_name != f"Party_{player_id}":
            if "half" in player_obj.party_name:
                for next_player_id in range(player_id + 1, player_id + game_type.group_sizes[0]):
                    player_party.append(session.query(Player).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)
            else:
                for next_player_id in range(player_id + 1, player_id + game_type.group_sizes[1]):
                    player_party.append(session.query(Player).filter_by(id=next_player_id).first())
                    player_party_ids.append(next_player_id)

        current_time = GLOBAL_START_TIME
        for game_index in range(game_type.simulated_games_count):
            game_players_to_insert = []

            player_stats = session.query(PlayerGameTypeStats).filter_by(
                player_id=player_id, game_type=game_type.type
            ).first()

            party_players_stats = session.query(PlayerGameTypeStats).filter(
                PlayerGameTypeStats.player_id.in_(player_party_ids),
            ).all()
            
            game_players_stats = session.query(PlayerGameTypeStats).filter(
                PlayerGameTypeStats.true_rating.between(player_stats.true_rating - 400,
                                                          player_stats.true_rating + 400),
                PlayerGameTypeStats.game_type == game_type.type,
                PlayerGameTypeStats.player_id.notin_(ref_players_ids),
                or_(PlayerGameTypeStats.last_time_played == None, PlayerGameTypeStats.last_time_played <= current_time),
            ).order_by(
                asc(func.abs(PlayerGameTypeStats.true_rating - player_stats.true_rating))
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
                ref_stats_calculated = compute_basic_stats(game_type, ref_player, ref_stats, playtime)

                game_players_to_insert.append(
                    GamePlayer(
                        created_at=current_time,
                        game=game,
                        player_id=player_id,
                        team="Team_1",
                        party_name=player_obj.party_name,
                        true_rating_before_game=player_stats.true_rating,
                        **ref_stats_calculated
                    )
                )
            
                team_player_index = 0

                for team_number in range(1, game_type.team_count + 1, 1):
                    team_size = len(player_party_ids) + 1 if team_number == 1 else 1
                    team_name = f"Team_{team_number}"
                    for _ in range(team_size, game_type.team_size + 1, 1):
                        team_player = game_players_stats[team_player_index]
                        team_player_stats = get_stat_parameters(game_type, team_player.true_rating)
                        team_player_stats_calculated = compute_basic_stats(game_type, team_player, team_player_stats, playtime)
                        game_players_to_insert.append(
                            GamePlayer(
                                created_at=current_time,
                                game=game,
                                player_id=team_player.player_id,
                                team=team_name,
                                party_name=team_player.party_name,
                                true_rating_before_game=team_player.true_rating,
                                **team_player_stats_calculated
                            )
                        )
                        team_player_index += 1

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
                    teams = { f"Team_{i+1}" for i in range(25) }

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
                death_weights = [(all_player_kills - player.kills + 1) for player in game_players_to_insert]
                weight_sum = sum(death_weights)

                for player, weight in zip(game_players_to_insert, death_weights):
                    player_deaths_koeficient = (all_player_kills * weight / weight_sum) / player.deaths
                    player.deaths = int(player.deaths * player_deaths_koeficient)
                    player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                    if playtime / player.deaths < player.longest_time_alive * kills_koeficient:
                        player.longest_time_alive = random.randrange(int(playtime / player.deaths), int(player.longest_time_alive * kills_koeficient) + 1, 1)
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
                    team1_death_weights = [(team1_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team1_weight_sum = sum(team1_death_weights)
                    team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']

                    for player, weight in zip(team1_players, team1_death_weights):
                        player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)

                    team2_new_kills = int(team2_kills * kills_koeficient)
                    team2_death_weights = [(team2_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team2_weight_sum = sum(team2_death_weights)
                    team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        
                    for player, weight in zip(team2_players, team2_death_weights):
                        player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                        if playtime / player.deaths < player.longest_time_alive * kills_koeficient:
                            player.longest_time_alive = random.randrange(int(playtime / player.deaths), int(player.longest_time_alive * kills_koeficient) + 1, 1)
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
                    team1_death_weights = [(team1_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team1_weight_sum = sum(team1_death_weights)
                    team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']

                    for player, weight in zip(team1_players, team1_death_weights):
                        player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)

                    team2_new_kills = int(team2_kills * kills_koeficient)
                    team2_death_weights = [(team2_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team2_weight_sum = sum(team2_death_weights)
                    team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        
                    for player, weight in zip(team2_players, team2_death_weights):
                        player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)
                        if playtime / player.deaths < player.longest_time_alive * kills_koeficient:
                            player.longest_time_alive = random.randrange(int(playtime / player.deaths), int(player.longest_time_alive * kills_koeficient) + 1, 1)
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
                    kill_cap = random.gauss(game_type.kill_cap, 6)
                    kills_koeficient = kill_cap / team1_kills if team1_kills >= team2_kills else kill_cap / team2_kills

                    for player in game_players_to_insert:
                        player.kills = int(player.kills * kills_koeficient)
                        player.damage_dealt = int(player.damage_dealt * kills_koeficient)
                        player.assists = int(player.assists * kills_koeficient)
                        player.killstreak = int(player.killstreak * kills_koeficient)

                    team1_new_kills = int(team1_kills * kills_koeficient)
                    team1_death_weights = [(team1_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team1_weight_sum = sum(team1_death_weights)
                    team1_players = [player for player in game_players_to_insert if player.team == 'Team_1']

                    for player, weight in zip(team1_players, team1_death_weights):
                        player_deaths_koeficient = (team1_new_kills * weight / team1_weight_sum) / player.deaths
                        player.deaths = int(player.deaths * player_deaths_koeficient)
                        player.damage_taken = int(player.damage_taken * player_deaths_koeficient)

                    team2_new_kills = int(team2_kills * kills_koeficient)
                    team2_death_weights = [(team2_new_kills - player.kills + 1) for player in game_players_to_insert]
                    team2_weight_sum = sum(team2_death_weights)
                    team2_players = [player for player in game_players_to_insert if player.team == 'Team_2']
                        
                    for player, weight in zip(team2_players, team2_death_weights):
                        player_deaths_koeficient = (team2_new_kills * weight / team2_weight_sum) / player.deaths
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
                        if playtime / player.deaths < player.longest_time_alive * kills_koeficient:
                            player.longest_time_alive = random.randrange(int(playtime / player.deaths), int(player.longest_time_alive * kills_koeficient) + 1, 1)
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
                'most_kills':            (max(game_players_to_insert, key=lambda p: p.kills).id, game_type.vp_weights[0]),
                'least_deaths':          (min(game_players_to_insert, key=lambda p: p.deaths).id, game_type.vp_weights[1]),
                'highest_killstreak':    (max(game_players_to_insert, key=lambda p: p.killstreak).id, game_type.vp_weights[2]),
                'longest_time_alive':    (max(game_players_to_insert, key=lambda p: p.longest_time_alive).id, game_type.vp_weights[3]),
                'most_contesting_kills': (max(game_players_to_insert, key=lambda p: p.contesting_kills).id, game_type.vp_weights[4]),
                'highest_objective_time':(max(game_players_to_insert, key=lambda p: p.objective_time).id, game_type.vp_weights[5]),
                'highest_accuracy':      (max(game_players_to_insert, key=lambda p: p.accuracy).id, game_type.vp_weights[6]),
                'highest_damage_dealt':  (max(game_players_to_insert, key=lambda p: p.damage_dealt).id, game_type.vp_weights[7]),
                'lowest_damage_taken':   (min(game_players_to_insert, key=lambda p: p.damage_taken).id, game_type.vp_weights[8]),
            }

            lvp_attributes = {
                'least_kills':           (min(game_players_to_insert, key=lambda p: p.kills).id, game_type.vp_weights[0]),
                'most_deaths':           (max(game_players_to_insert, key=lambda p: p.deaths).id, game_type.vp_weights[1]),
                'lowest_killstreak':     (min(game_players_to_insert, key=lambda p: p.killstreak).id, game_type.vp_weights[2]),
                'shortest_time_alive':   (min(game_players_to_insert, key=lambda p: p.longest_time_alive).id, game_type.vp_weights[3]),
                'least_contesting_kills':(min(game_players_to_insert, key=lambda p: p.contesting_kills).id, game_type.vp_weights[4]),
                'lowest_objective_time': (min(game_players_to_insert, key=lambda p: p.objective_time).id, game_type.vp_weights[5]),
                'lowest_accuracy':       (min(game_players_to_insert, key=lambda p: p.accuracy).id, game_type.vp_weights[6]),
                'lowest_damage_dealt':   (min(game_players_to_insert, key=lambda p: p.damage_dealt).id, game_type.vp_weights[7]),
                'highest_damage_taken':  (max(game_players_to_insert, key=lambda p: p.damage_taken).id, game_type.vp_weights[8]),
            }

            current_mvp = (None, 0.0)
            current_lvp = (None, 0.0)

            STAT_ATTRS = ['kills', 'deaths', 'killstreak', 'longest_time_alive',
                'contesting_kills', 'objective_time', 'accuracy', 'damage_dealt', 'damage_taken']

            for player in game_players_to_insert:
                mvp_weight_sum = sum(weight for (pid, weight) in mvp_attributes.values() if player.id == pid)
                lvp_weight_sum = sum(weight for (pid, weight) in lvp_attributes.values() if player.id == pid)

                if current_mvp[1] < mvp_weight_sum:
                    current_mvp = (player.id, mvp_weight_sum)
                elif current_mvp[1] == mvp_weight_sum:
                    mvp_player = next((p for p in game_players_to_insert if p.id == current_mvp[0]), None)

                    if mvp_player is None:
                        current_mvp = (player.id, mvp_weight_sum)
                        continue

                    better_stats_count = 0
                    for attr in STAT_ATTRS:
                        if attr in ['deaths', 'damage_taken']:
                            better_stats_count += 1 if getattr(player, attr) < getattr(mvp_player, attr) else 0
                        else:
                            better_stats_count += 1 if getattr(player, attr) > getattr(mvp_player, attr) else 0
                        
                    if better_stats_count > len(STAT_ATTRS) / 2:
                        current_mvp = (player.id, mvp_weight_sum)

                if current_lvp[1] < lvp_weight_sum:
                    current_lvp = (player.id, lvp_weight_sum)
                elif current_lvp[1] == lvp_weight_sum:
                    lvp_player = next((p for p in game_players_to_insert if p.id == current_lvp[0]), None)

                    if lvp_player is None:
                        current_lvp = (player.id, lvp_weight_sum)
                        continue

                    better_stats_count = 0
                    for attr in STAT_ATTRS:
                        if attr in ['deaths', 'damage_taken']:
                            better_stats_count += 1 if getattr(player, attr) > getattr(lvp_player, attr) else 0
                        else:
                            better_stats_count += 1 if getattr(player, attr) < getattr(lvp_player, attr) else 0
                        
                    if better_stats_count > len(STAT_ATTRS) / 2:
                        current_lvp = (player.id, lvp_weight_sum)

            new_game_players_to_insert = []
            for game_player in game_players_to_insert:
                is_mvp = bool(game_player.id == current_mvp[0])
                is_lvp = bool(game_player.id == current_lvp[0])
                player_stats = get_stat_parameters(game_type, game_player.true_rating)
                game_player_game_type_stats = session.query(PlayerGameTypeStats).filter(
                    PlayerGameTypeStats.player_id == game_player.player_id,
                ).first()
                player_stats_calculated = compute_remaining_stats(game_player, game_player_game_type_stats, playtime, is_mvp, is_lvp)

                new_game_player = GamePlayer(
                    created_at=current_time,
                    game=game,
                    player_id=game_player.player_id,
                    team=game_player.team,
                    party_name=game_player.party_name,
                    true_rating_before_game=game_player.true_rating,
                    **player_stats_calculated
                )
                new_game_players_to_insert.append(new_game_player)
            
            game_players_to_insert = new_game_players_to_insert
            
            logger.info(f"Inserting {len(game_players_to_insert)} game player records for game {game_index + 1} in mode {game_type.type} in bulk...")
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
            logger.info(f"Player stats updated for game {game_index + 1}.")


"""
Main simulation function to create players, initialize stats, and simulate games.
"""
def simulate_all_modes() -> None:
    players_to_create = []
    ref_players_ids = list(range(1, REFERENCE_PLAYER_COUNT + 1))
    logger.info("Creating players...")
    
    # Half and full team players with corresponding party names for each scenario
    rules = [
        (range(5, 8), "linear_increase_decrease_half"),
        (range(8, 14), "linear_increase_decrease_full"),
        (range(14, 17), "increase_then_constant_half"),
        (range(17, 23), "increase_then_constant_full"),
        (range(23, 26), "skill_gap_half"),
        (range(26, 32), "skill_gap_full"),
        (range(32, 35), "huge_fall_then_jump_half"),
        (range(35, 41), "huge_fall_then_jump_full")
    ]
    
    for player_id in range(1, TOTAL_PLAYERS + 1):
        party_name = f"Party_{player_id}" # default/solo party name
        for id_range, name in rules:
            if player_id in id_range:
                party_name = name
                break
        players_to_create.append(Player(id=player_id, name=f"Player_{player_id}", party_name=party_name))
    
    session.add_all(players_to_create)
    session.commit()
    logger.info(f"Created {len(players_to_create)} players.")
    
    for game_type in GAME_TYPES:
        logger.info(f"Creating {game_type.type} stats for players")
        simulate_player_game_type_stats(game_type, ref_players_ids)
        logger.info(f"{game_type.type} stats for players finished!")
    
    for game_type in GAME_TYPES:
        logger.info(f"Starting simulation for game type: {game_type.type} ({game_type.simulated_games_count} games)")
        simulate_game_mode_games(game_type, ref_players_ids)
        logger.info(f"Completed simulation for game type: {game_type.type}")
