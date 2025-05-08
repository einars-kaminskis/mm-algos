import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()  # This will load variables from .env file in the project root directory

DATABASE_URL = os.getenv("DATABASE_URL")

class GameMode:
    def __init__(
        self,
        type: str,
        team_size: int,
        team_count: int,
        time_limit_mean: int,
        time_limit_variance: int,
        kill_cap: int = None,
        point_limit: int = None,
        winning_round_limit: int = None,
        base_k: float = None,
        group_sizes: list = None,
        adjustments: dict = None,
        vp_weights: list = None, # Valuable player weight order:
                                 # [kills, deaths, killstreak, time_alive, contesting_kills,
                                 # objective_time, accuracy, damage_dealt, damage_taken]
        rank_delta_weights: dict = None,
    ) -> None:
        self.type = type
        self.team_size = team_size
        self.team_count = team_count
        self.time_limit_mean = time_limit_mean
        self.time_limit_variance = time_limit_variance
        self.kill_cap = kill_cap
        self.point_limit = point_limit
        self.winning_round_limit = winning_round_limit
        self.base_k = base_k
        self.vp_weights = vp_weights if vp_weights is not None else []
        self.rank_delta_weights = rank_delta_weights if rank_delta_weights is not None else {}
        self.group_sizes = group_sizes if group_sizes is not None else []
        self.adjustments = adjustments if adjustments is not None else {}

GAME_TYPES = [
    GameMode(
        type = "TDM", # Team deathmatch (from Call of Duty)
        team_size = 6,
        team_count = 2,
        time_limit_mean = 600, # seconds or 10 minutes
        time_limit_variance = 120, # seconds or 2 minutes
        kill_cap = 50,
        base_k = 20.00,
        vp_weights = [1.00, 0.67, 0.50, 0.33, 0.00, 0.00, 0.33, 0.50, 0.00],
        group_sizes = [3, 6],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  50, 'sd_total_games_played': 10,
                'mean_total_wins':           8, 'sd_total_wins':  3,
                'mean_total_loses':         40, 'sd_total_loses': 10,
                'mean_total_ties':           2, 'sd_total_ties':  1,
                'mean_win_streak':           2, 'sd_win_streak':  1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    8,  'sd_kills':   3,   # ~8 kills
                'mean_deaths':  10,  'sd_deaths':   3,
                'mean_assists': 1.0, 'sd_assists': 0.5, # ~1 assist
                'mean_accuracy':0.18,'sd_accuracy':0.01, # mid of 20%–25%
                'mean_damage_missed': 3400, 'sd_damage_missed': 300, # Not used in calculating true_rating_after_game, because it is situational.
                'mean_headshot_accuracy':0.06, 'sd_headshot_accuracy':0.005,
                'mean_torso_accuracy':0.08,'sd_torso_accuracy':0.007,
                'mean_best_killstreak':3,   'sd_best_killstreak':1,

                # For GamePlayer:
                'mean_longest_time_alive':  35, 'sd_longest_time_alive': 15,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played': 200, 'sd_total_games_played': 50,
                'mean_total_wins':          80, 'sd_total_wins':        20,
                'mean_total_loses':        110, 'sd_total_loses':        30,
                'mean_total_ties':          10, 'sd_total_ties':         5,
                'mean_win_streak':          5, 'sd_win_streak':         2,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   15, 'sd_kills':  5,   # ~15–18 kills
                'mean_deaths':  15, 'sd_deaths':  5,
                'mean_assists': 1.5,'sd_assists': 0.7,
                'mean_accuracy':0.25,'sd_accuracy':0.015,
                'mean_damage_missed': 4000, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.08,'sd_headshot_accuracy':0.007,
                'mean_torso_accuracy':0.11,'sd_torso_accuracy':0.01,
                'mean_best_killstreak':5,  'sd_best_killstreak':2,

                # For GamePlayer:
                'mean_longest_time_alive':  55, 'sd_longest_time_alive': 20,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':1000,'sd_total_games_played':200,
                'mean_total_wins':         600, 'sd_total_wins':        100,
                'mean_total_loses':        350, 'sd_total_loses':         80,
                'mean_total_ties':          50, 'sd_total_ties':         10,
                'mean_win_streak':          8, 'sd_win_streak':         3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   25, 'sd_kills':  7,   # ~20–30 kills
                'mean_deaths':  19, 'sd_deaths':  6,
                'mean_assists': 2.0,'sd_assists': 1.0,
                'mean_accuracy':0.36,'sd_accuracy':0.02, # pro ~40 %
                'mean_damage_missed': 4200, 'sd_damage_missed': 400,
                'mean_headshot_accuracy':0.15,'sd_headshot_accuracy':0.015,
                'mean_torso_accuracy':0.16,'sd_torso_accuracy':0.02,
                'mean_best_killstreak':10,'sd_best_killstreak':3,
                
                # For GamePlayer:
                'mean_longest_time_alive':  80, 'sd_longest_time_alive': 25,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            }
        },
        rank_delta_weights = {
            "kills": 1.00,
            "deaths": 1.00,
            "assists": 0.10,
            "damage_dealt": 0.90,
            "damage_taken": 0.90,
            "damage_missed": 0.10,
            "headshot_damage_dealt": 0.50,
            "torso_damage_dealt": 0.40,
            "leg_damage_dealt": 0.30,
            "accuracy": 0.80,
            "headshot_accuracy": 0.50,
            "torso_accuracy": 0.40,
            "leg_accuracy": 0.30,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 0.10,
            "kills_per_minute": 0.95,
            "deaths_per_minute": 0.95,
            "assists_per_minute": 0.10,
            "damage_dealt_per_minute": 0.85,
            "damage_taken_per_minute": 0.85,
            "kill_death_ratio": 0.95,
            "damage_dealt_and_taken_ratio": 0.95,
            "killstreak": 0.80,
            "win_streak": 1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 1.00
        },
    ),
    GameMode(
        type = "FFA", # Free-for-All (from Call of Duty)
        team_size = 1,
        team_count = 12,
        time_limit_mean = 600, # seconds or 10 minutes
        time_limit_variance = 120, # seconds or 2 minutes
        kill_cap = 50,
        base_k = 15.00,
        vp_weights = [1.00, 0.13, 0.38, 0.38, 0.00, 0.00, 0.25, 0.38, 0.00],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  30, 'sd_total_games_played': 10,
                'mean_total_wins':           3, 'sd_total_wins':  2,
                'mean_total_loses':         27, 'sd_total_loses':  8,
                'mean_total_ties':           0, 'sd_total_ties':   0,
                'mean_win_streak':           1, 'sd_win_streak':   1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    5, 'sd_kills':  3,   # ~3–5
                'mean_deaths':  12, 'sd_deaths':  5,
                'mean_assists': 0,  'sd_assists': 0,
                'mean_accuracy':0.18,'sd_accuracy':0.01,
                'mean_damage_missed': 2200, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.06, 'sd_headshot_accuracy':0.005,
                'mean_torso_accuracy':0.08,'sd_torso_accuracy':0.007,
                'mean_best_killstreak':2,  'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':  30, 'sd_longest_time_alive': 13,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':150, 'sd_total_games_played': 40,
                'mean_total_wins':          50, 'sd_total_wins':        15,
                'mean_total_loses':         90, 'sd_total_loses':        25,
                'mean_total_ties':           0, 'sd_total_ties':         0,
                'mean_win_streak':           5, 'sd_win_streak':         2,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   13, 'sd_kills':  4,   # solo med ~10–15
                'mean_deaths':  13, 'sd_deaths':  4,
                'mean_assists': 0,  'sd_assists': 0,
                'mean_accuracy':0.25,'sd_accuracy':0.015,
                'mean_damage_missed': 3900, 'sd_damage_missed': 600,
                'mean_headshot_accuracy':0.08,'sd_headshot_accuracy':0.007,
                'mean_torso_accuracy':0.11,'sd_torso_accuracy':0.01,
                'mean_best_killstreak':4,  'sd_best_killstreak':1.5,
                
                # For GamePlayer:
                'mean_longest_time_alive':  48, 'sd_longest_time_alive': 17,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':800, 'sd_total_games_played':150,
                'mean_total_wins':         400, 'sd_total_wins':         80,
                'mean_total_loses':        350, 'sd_total_loses':         70,
                'mean_total_ties':           0, 'sd_total_ties':         0,
                'mean_win_streak':          8, 'sd_win_streak':         3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   25, 'sd_kills':  8,   # solo high ~20–30
                'mean_deaths':  20, 'sd_deaths':  6,
                'mean_assists': 0,  'sd_assists': 0,
                'mean_accuracy':0.36,'sd_accuracy':0.02,
                'mean_damage_missed': 4200, 'sd_damage_missed': 400,
                'mean_headshot_accuracy':0.15,'sd_headshot_accuracy':0.015,
                'mean_torso_accuracy':0.16,'sd_torso_accuracy':0.02,
                'mean_best_killstreak':6,  'sd_best_killstreak':2,
                
                # For GamePlayer:
                'mean_longest_time_alive':  70, 'sd_longest_time_alive': 22,
                'mean_contesting_kills':0,   'sd_contesting_kills':0,
                'mean_objective_time':0,     'sd_objective_time':0,
            }
        },
        rank_delta_weights = {
            "kills": 1.00,
            "deaths": 1.00,
            "assists": 0.10,
            "damage_dealt": 0.90,
            "damage_taken": 0.90,
            "damage_missed": 0.10,
            "headshot_damage_dealt": 0.50,
            "torso_damage_dealt": 0.40,
            "leg_damage_dealt": 0.30,
            "accuracy": 0.80,
            "headshot_accuracy": 0.50,
            "torso_accuracy": 0.40,
            "leg_accuracy": 0.30,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 0.10,
            "kills_per_minute": 0.95,
            "deaths_per_minute": 0.95,
            "assists_per_minute": 0.10,
            "damage_dealt_per_minute": 0.85,
            "damage_taken_per_minute": 0.85,
            "kill_death_ratio": 0.95,
            "damage_dealt_and_taken_ratio": 0.95,
            "killstreak": 0.80,
            "win_streak": 1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 1.00
        },
    ),
    GameMode(
        type = "Domination", # Domination (from Call of Duty)
        team_size = 6,
        team_count = 2,
        time_limit_mean = 1020, # seconds or 17 minutes
        time_limit_variance = 180, # seconds or 3 minutes
        point_limit = 200, # 1 point per 5 seconds for each of the 3 zones
        base_k = 20.00,
        vp_weights = [0.14, 0.00, 0.00, 0.00, 0.14, 1.00, 0.07, 0.07, 0.00],
        group_sizes = [3, 6],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  60, 'sd_total_games_played': 15,
                'mean_total_wins':          20, 'sd_total_wins':         8,
                'mean_total_loses':         40, 'sd_total_loses':        15,
                'mean_total_ties':           0, 'sd_total_ties':         0,
                'mean_win_streak':           3, 'sd_win_streak':         1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    8,  'sd_kills':   4,   # Dom ≈ TDM low
                'mean_deaths':  15,  'sd_deaths':   5,
                'mean_assists': 2,   'sd_assists':   1.5,
                'mean_accuracy':0.15,'sd_accuracy':0.01,
                'mean_damage_missed': 4200, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.05, 'sd_headshot_accuracy':0.003,
                'mean_torso_accuracy':0.07,'sd_torso_accuracy':0.006,
                'mean_best_killstreak':3,   'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive': 70, 'sd_longest_time_alive': 30,
                'mean_contesting_kills':1,   'sd_contesting_kills':1,   # objective fights
                'mean_objective_time':       140, 'sd_objective_time':  40,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':250, 'sd_total_games_played': 60,
                'mean_total_wins':         120, 'sd_total_wins':        30,
                'mean_total_loses':        130, 'sd_total_loses':        35,
                'mean_total_ties':           0, 'sd_total_ties':         0,
                'mean_win_streak':           6, 'sd_win_streak':         2,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   20,  'sd_kills':   6,
                'mean_deaths':  15,  'sd_deaths':   5,
                'mean_assists': 3,   'sd_assists':   2,
                'mean_accuracy':0.23,'sd_accuracy':0.015,
                'mean_damage_missed': 6000, 'sd_damage_missed': 600,
                'mean_headshot_accuracy':0.07,'sd_headshot_accuracy':0.006,
                'mean_torso_accuracy':0.11,'sd_torso_accuracy':0.008,
                'mean_best_killstreak':5,   'sd_best_killstreak':2,
                
                # For GamePlayer:
                'mean_longest_time_alive': 90, 'sd_longest_time_alive': 35,
                'mean_contesting_kills':3,   'sd_contesting_kills':1,
                'mean_objective_time':       210, 'sd_objective_time': 50,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':1200,'sd_total_games_played':250,
                'mean_total_wins':         700, 'sd_total_wins':        120,
                'mean_total_loses':        500, 'sd_total_loses':        100,
                'mean_total_ties':           0, 'sd_total_ties':         0,
                'mean_win_streak':           8, 'sd_win_streak':         3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   35,  'sd_kills':  10,
                'mean_deaths':  10,  'sd_deaths':   4,
                'mean_assists': 4,   'sd_assists':   3,
                'mean_accuracy':0.33,'sd_accuracy':0.02,
                'mean_damage_missed': 6700, 'sd_damage_missed': 600,
                'mean_headshot_accuracy':0.14,'sd_headshot_accuracy':0.009,
                'mean_torso_accuracy':0.145,'sd_torso_accuracy':0.01,
                'mean_best_killstreak':8,   'sd_best_killstreak':3,
                
                # For GamePlayer:
                'mean_longest_time_alive': 100, 'sd_longest_time_alive': 45,
                'mean_contesting_kills':5,   'sd_contesting_kills':2,
                'mean_objective_time':       320, 'sd_objective_time': 60,
            }
        },
        rank_delta_weights = {
            "kills": 0.55,
            "deaths": 0.50,
            "assists": 0.10,
            "damage_dealt": 0.60,
            "damage_taken": 0.50,
            "damage_missed": 0.10,
            "headshot_damage_dealt": 0.40,
            "torso_damage_dealt": 0.35,
            "leg_damage_dealt": 0.20,
            "accuracy": 0.50,
            "headshot_accuracy": 0.40,
            "torso_accuracy": 0.35,
            "leg_accuracy": 0.20,
            "contesting_kills": 0.80,
            "objective_time": 1.00,
            "longest_time_alive": 0.40,
            "kills_per_minute": 0.50,
            "deaths_per_minute": 0.45,
            "assists_per_minute": 0.10,
            "damage_dealt_per_minute": 0.55,
            "damage_taken_per_minute": 0.45,
            "kill_death_ratio": 0.50,
            "damage_dealt_and_taken_ratio": 0.50,
            "killstreak": 0.45,
            "win_streak": 1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 1.00
        },
    ),
    GameMode(
        type = "BR_1V99", # Battle royale 1v99 (from Fortnite)
        team_size = 1,
        team_count = 100,
        time_limit_mean = 1200, # seconds or 20 minutes
        time_limit_variance = 180, # seconds or 3 minutes
        kill_cap = 99,
        base_k = 25.00,
        vp_weights = [0.63, 0.25, 0.13, 1.00, 0.00, 0.00, 0.13, 0.38, 0.00],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  20, 'sd_total_games_played':  5,
                'mean_total_wins':           1, 'sd_total_wins':          1,
                'mean_total_loses':         19, 'sd_total_loses':          5,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           1, 'sd_win_streak':          1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    1,  'sd_kills':   1,
                'mean_deaths':   1,  'sd_deaths':   1,
                'mean_assists':  0,  'sd_assists':  0,
                'mean_accuracy':0.10,'sd_accuracy':0.008,
                'mean_damage_missed': 600, 'sd_damage_missed': 400,
                'mean_headshot_accuracy':0.01, 'sd_headshot_accuracy':0.001,
                'mean_torso_accuracy':0.05,'sd_torso_accuracy':0.002,
                'mean_best_killstreak':1,  'sd_best_killstreak':0.5,
                
                # For GamePlayer:
                'mean_longest_time_alive':200,'sd_longest_time_alive': 160,
                'mean_contesting_kills':0, 'sd_contesting_kills':0,
                'mean_objective_time': 0, 'sd_objective_time':0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':100, 'sd_total_games_played': 20,
                'mean_total_wins':           8, 'sd_total_wins':          3,
                'mean_total_loses':         92, 'sd_total_loses':         20,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           3, 'sd_win_streak':          1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    3,  'sd_kills':   2,  # med ~3–5 kills
                'mean_deaths':   1,  'sd_deaths':   1,
                'mean_assists':  0,  'sd_assists':  0,
                'mean_accuracy':0.15,'sd_accuracy':0.01,
                'mean_damage_missed': 1000, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.04, 'sd_headshot_accuracy':0.002,
                'mean_torso_accuracy':0.07,'sd_torso_accuracy':0.006,
                'mean_best_killstreak':2,  'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':600,'sd_longest_time_alive':250,
                'mean_contesting_kills':0, 'sd_contesting_kills':0,
                'mean_objective_time': 0, 'sd_objective_time':0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':500,'sd_total_games_played':100,
                'mean_total_wins':          50, 'sd_total_wins':         10,
                'mean_total_loses':        450, 'sd_total_loses':        90,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           8, 'sd_win_streak':          3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    8,  'sd_kills':   3,  # high elite ~8–10
                'mean_deaths':   1,  'sd_deaths':   0,
                'mean_assists':  0,  'sd_assists':  0,
                'mean_accuracy':0.25,'sd_accuracy':0.015,
                'mean_damage_missed': 2000, 'sd_damage_missed': 700,
                'mean_headshot_accuracy':0.07,'sd_headshot_accuracy':0.006,
                'mean_torso_accuracy':0.10,'sd_torso_accuracy':0.008,
                'mean_best_killstreak':3,  'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':1200,'sd_longest_time_alive':100,
                'mean_contesting_kills':0,  'sd_contesting_kills':0,
                'mean_objective_time': 0,  'sd_objective_time':0,
            }
        },
        rank_delta_weights = {
            "kills": 0.70,
            "deaths": 0.10,
            "assists": 0.50,
            "damage_dealt": 0.70,
            "damage_taken": 0.50,
            "damage_missed": 0.20,
            "headshot_damage_dealt": 0.50,
            "torso_damage_dealt": 0.35,
            "leg_damage_dealt": 0.20,
            "accuracy": 0.60,
            "headshot_accuracy": 0.50,
            "torso_accuracy": 0.35,
            "leg_accuracy": 0.20,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.20,
            "deaths_per_minute": 0.00,
            "assists_per_minute": 0.10,
            "damage_dealt_per_minute": 0.20,
            "damage_taken_per_minute": 0.10,
            "kill_death_ratio": 0.00,
            "damage_dealt_and_taken_ratio": 0.15,
            "killstreak": 0.70,
            "win_streak": 1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 0.00
        },
    ),
    GameMode(
        type = "BR_4V96", # Battle royale 4v96 (from Fortnite)
        team_size = 4,
        team_count = 25,
        time_limit_mean = 1380, # seconds or 23 minutes
        time_limit_variance = 240, # seconds or 4 minutes
        kill_cap = 96,
        base_k = 25.00,
        vp_weights = [0.57, 0.57, 0.00, 1.00, 0.00, 0.00, 0.29, 0.43, 0.00],
        group_sizes = [2, 4],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  50, 'sd_total_games_played': 15,
                'mean_total_wins':           5, 'sd_total_wins':          3,
                'mean_total_loses':         45, 'sd_total_loses':         15,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           2, 'sd_win_streak':          1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    1, 'sd_kills':  1,
                'mean_deaths':   1, 'sd_deaths':  1,
                'mean_assists':  1, 'sd_assists':  1,
                'mean_accuracy':0.10,'sd_accuracy':0.008,
                'mean_damage_missed': 600, 'sd_damage_missed': 400,
                'mean_headshot_accuracy':0.01, 'sd_headshot_accuracy':0.001,
                'mean_torso_accuracy':0.05,'sd_torso_accuracy':0.002,
                'mean_best_killstreak':2, 'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':250,'sd_longest_time_alive':150,
                'mean_contesting_kills':0, 'sd_contesting_kills':0,
                'mean_objective_time': 0,  'sd_objective_time':0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':200, 'sd_total_games_played': 50,
                'mean_total_wins':          50, 'sd_total_wins':         10,
                'mean_total_loses':        150, 'sd_total_loses':         40,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           5, 'sd_win_streak':          2,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    3, 'sd_kills':  2,
                'mean_deaths':   1, 'sd_deaths':  1,
                'mean_assists':  2, 'sd_assists':  1,
                'mean_accuracy':0.15,'sd_accuracy':0.001,
                'mean_damage_missed': 1000, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.04, 'sd_headshot_accuracy':0.002,
                'mean_torso_accuracy':0.07,'sd_torso_accuracy':0.006,
                'mean_best_killstreak':3, 'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':650,'sd_longest_time_alive':250,
                'mean_contesting_kills':0, 'sd_contesting_kills':0,
                'mean_objective_time': 0,  'sd_objective_time':0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':800,'sd_total_games_played':150,
                'mean_total_wins':         400,'sd_total_wins':         80,
                'mean_total_loses':        350,'sd_total_loses':         70,
                'mean_total_ties':           0,'sd_total_ties':          0,
                'mean_win_streak':           8,'sd_win_streak':          3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    6, 'sd_kills':  3,  # high squads ~6–8 kills
                'mean_deaths':   1, 'sd_deaths':  1,
                'mean_assists':  4, 'sd_assists':  2,
                'mean_accuracy':0.25,'sd_accuracy':0.015,
                'mean_damage_missed': 1800, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.07,'sd_headshot_accuracy':0.006,
                'mean_torso_accuracy':0.10,'sd_torso_accuracy':0.008,
                'mean_best_killstreak':4, 'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':1200,'sd_longest_time_alive':100,
                'mean_contesting_kills':0, 'sd_contesting_kills':0,
                'mean_objective_time': 0,  'sd_objective_time':0,
            }
        },
        rank_delta_weights = {
            "kills": 0.70,
            "deaths": 0.10,
            "assists": 0.65,
            "damage_dealt": 0.70,
            "damage_taken": 0.50,
            "damage_missed": 0.30,
            "headshot_damage_dealt": 0.50,
            "torso_damage_dealt": 0.32,
            "leg_damage_dealt": 0.17,
            "accuracy": 0.60,
            "headshot_accuracy": 0.50,
            "torso_accuracy": 0.32,
            "leg_accuracy": 0.17,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.20,
            "deaths_per_minute": 0.00,
            "assists_per_minute": 0.15,
            "damage_dealt_per_minute": 0.20,
            "damage_taken_per_minute": 0.10,
            "kill_death_ratio": 0.00,
            "damage_dealt_and_taken_ratio": 0.15,
            "killstreak": 0.70,
            "win_streak": 1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 0.00
        },
    ),
    GameMode(
        type = "SAD", # Search and Destroy (from CS:GO)
        team_size = 5,
        team_count = 2,
        time_limit_mean = 1920, # seconds or 32 minutes
        time_limit_variance = 240, # seconds or 4 minutes
        winning_round_limit = 16, # for each team to win
        kill_cap = 109, # Average between 83 kills and 136 kills
        base_k = 30.00,
        vp_weights = [1.00, 0.57, 0.29, 0.00, 0.00, 0.00, 0.14, 0.29, 0.00],
        group_sizes = [2, 5],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':  80, 'sd_total_games_played': 20,
                'mean_total_wins':          20, 'sd_total_wins':          8,
                'mean_total_loses':         60, 'sd_total_loses':        15,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           3, 'sd_win_streak':          1,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':    8, 'sd_kills':  3,   # avg ~8–10 kills
                'mean_deaths':  16, 'sd_deaths':  4,
                'mean_assists': 3,  'sd_assists':  2,
                'mean_accuracy':0.12,'sd_accuracy':0.009,
                'mean_damage_missed': 5000, 'sd_damage_missed': 800,
                'mean_headshot_accuracy':0.03,'sd_headshot_accuracy':0.001,
                'mean_torso_accuracy':0.06,'sd_torso_accuracy':0.003,
                'mean_best_killstreak':3, 'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':  40, 'sd_longest_time_alive': 30,
                'mean_contesting_kills':1,  'sd_contesting_kills':1,
                'mean_objective_time':  0,  'sd_objective_time':0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':300,'sd_total_games_played': 75,
                'mean_total_wins':         120, 'sd_total_wins':        30,
                'mean_total_loses':        180, 'sd_total_loses':        45,
                'mean_total_ties':           0, 'sd_total_ties':          0,
                'mean_win_streak':           6, 'sd_win_streak':          2,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':   18, 'sd_kills': 4,   # avg ~15–18 kills
                'mean_deaths':  15, 'sd_deaths': 4,
                'mean_assists': 2,  'sd_assists': 2,
                'mean_accuracy':0.30,'sd_accuracy':0.02,
                'mean_damage_missed': 4000, 'sd_damage_missed': 500,
                'mean_headshot_accuracy':0.13,'sd_headshot_accuracy':0.009,
                'mean_torso_accuracy':0.11,'sd_torso_accuracy':0.008,
                'mean_best_killstreak':4, 'sd_best_killstreak':1,
                
                # For GamePlayer:
                'mean_longest_time_alive':  95, 'sd_longest_time_alive': 20,
                'mean_contesting_kills':1, 'sd_contesting_kills':1,
                'mean_objective_time':  0, 'sd_objective_time':0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                'mean_total_games_played':     800,  'sd_total_games_played':     150,
                'mean_total_wins':             500,  'sd_total_wins':             100,
                'mean_total_loses':            300,  'sd_total_loses':            75,
                'mean_total_ties':             0,    'sd_total_ties':             0,
                'mean_win_streak':             8,    'sd_win_streak':             3,

                #For both PlayerGameTypeStats and GamePlayer:
                'mean_kills':                  25,   'sd_kills':                  5, # elite ~25+ kills
                'mean_deaths':                 10,   'sd_deaths':                 3,
                'mean_assists':                1,    'sd_assists':                1,
                'mean_accuracy':               0.50, 'sd_accuracy':               0.025,
                'mean_damage_missed':          2000, 'sd_damage_missed':          400,
                'mean_headshot_accuracy':      0.30, 'sd_headshot_accuracy':      0.02,
                'mean_torso_accuracy':         0.15, 'sd_torso_accuracy':         0.01,
                'mean_best_killstreak':        5,    'sd_best_killstreak':        1,
                
                # For GamePlayer:
                'mean_longest_time_alive':     115,  'sd_longest_time_alive':     5,
                'mean_contesting_kills':       1,    'sd_contesting_kills':       1,
                'mean_objective_time':         0,    'sd_objective_time':         0,
            }
        },
        rank_delta_weights = {
            "kills": 0.90,
            "deaths": 0.90,
            "assists": 0.45,
            "damage_dealt": 0.30,
            "damage_taken": 0.30,
            "damage_missed": 0.40,
            "headshot_damage_dealt": 0.40,
            "torso_damage_dealt": 0.20,
            "leg_damage_dealt": 0.10,
            "accuracy": 0.90,
            "headshot_accuracy": 0.80,
            "torso_accuracy": 0.40,
            "leg_accuracy": 0.10,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.70,
            "deaths_per_minute": 0.70,
            "assists_per_minute": 0.35,
            "damage_dealt_per_minute": 0.20,
            "damage_taken_per_minute": 0.20,
            "kill_death_ratio": 0.80,
            "damage_dealt_and_taken_ratio": 0.30,
            "killstreak": 0.85,
            "win_streak":1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 1.00
        },
    ),
]

# --------------------------------------------------------------------
# Interpolation function for continuous scaling across rating ranges.
# We assume three anchor points:
#   - at rating 200: use low anchor,
#   - at rating 1300: use medium anchor,
#   - at rating 3000: use high anchor.
# For ratings below 200, we extrapolate downward using the same slope as from 200 to 1300.
# For ratings = 3000, we use the high anchor.
# For ratings above 3000, we extrapolate upward using the same slope as from 1300 to 3000.
def interpolate_stat(low_val, med_val, high_val, true_rating: float) -> int | float:
    if true_rating < 200:
        slope = abs(med_val - low_val) / 500.0
        result = low_val - (200 - true_rating) * slope
    elif true_rating == 200:
        result = low_val
    elif true_rating < 1300:
        t = (true_rating - 200) / 500.0
        result = low_val + t * abs(med_val - low_val)
    elif true_rating == 1300:
        result = med_val
    elif true_rating < 3000:
        t = (true_rating - 1300) / 500.0
        result = med_val + t * abs(high_val - med_val)
    elif true_rating == 3000:
        result = high_val
    elif true_rating > 3000:
        # Extrapolate with same slope as 1300->3000.
        slope = abs(high_val - med_val) / 500.0
        result = high_val + (true_rating - 3000) * slope
    return max(result, 0)

def interpolate_stats(low_stats: dict, med_stats: dict, high_stats: dict, true_rating: float) -> dict:
    result = {}

    result['mean_total_games_played'] = interpolate_stat(
        low_stats['mean_total_games_played'],
        med_stats['mean_total_games_played'],
        high_stats['mean_total_games_played'],
        true_rating
    )

    zero_exclude = {
        'mean_total_games_played', 'sd_total_games_played',
        'mean_total_wins', 'sd_total_wins',
        'mean_total_loses', 'sd_total_loses',
        'mean_total_ties',  'sd_total_ties',
        'mean_win_streak',  'sd_win_streak',
    }

    for key in low_stats: # low, medium and high have the same keys
        if result['mean_total_games_played'] == 0 and key in zero_exclude:
            result[key] = 0
        result[key] = interpolate_stat(low_stats[key], med_stats[key], high_stats[key], true_rating)
    return result

def get_stat_parameters(game_mode: GameMode, true_rating: float) -> dict:
    low_stats, med_stats, high_stats = (game_mode.adjustments["low"], game_mode.adjustments["med"], game_mode.adjustments["high"],)
    return interpolate_stats(low_stats, med_stats, high_stats, true_rating)

# Return a UTC‑aware datetime or return unchanged.
def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

# ------------------------
# CONSTANTS
# ------------------------
TOTAL_ATTRIBUTES = [
    ("kills", 1),
    ("deaths", -1),
    ("assists", 1),
    ("damage_dealt", 1),
    ("damage_taken", -1),
    ("damage_missed", -1),
    ("headshot_damage_dealt", 1),
    ("torso_damage_dealt", 1),
    ("leg_damage_dealt", 1),
    ("accuracy", 1),
    ("headshot_accuracy", 1),
    ("torso_accuracy", 1),
    ("leg_accuracy", 1),
    ("contesting_kills", 1),
    ("objective_time", 1),
    ("longest_time_alive", 1),
    ("kills_per_minute", 1),
    ("deaths_per_minute", -1),
    ("assists_per_minute", 1),
    ("damage_dealt_per_minute", 1),
    ("damage_taken_per_minute", -1),
]

RANK_AVERAGES = [
    ('kills', 1),
    ('deaths', -1),
    ('assists', 1),
    ('accuracy', 1),
    ('headshot_accuracy', 1),
    ('torso_accuracy', 1),
    ('longest_time_alive', 1),
    ('contesting_kills', 1),
    ('objective_time', 1),
  ]

RANK_DISTRIBUTION_WEIGHTS = [
    0.0280, 0.0462, 0.0771, 0.0714, 0.0614, 0.0509, 0.0545, 0.0568,
    0.0630, 0.0585, 0.0551, 0.0546, 0.0510, 0.0508, 0.0424, 0.0356,
    0.0317, 0.0263, 0.0234, 0.0168, 0.0126, 0.0097, 0.0067, 0.0052,
    0.0037, 0.0028, 0.0014, 0.0005, 0.0003, 0.0002, 0.0002, 0.0002,
    0.0002, 0.0002, 0.0002, 0.0002, 0.0002
]

TOTAL_PLAYERS = 40000
# TOTAL_PLAYERS = 1000

# FOR REFERENCE PLAYER ADJUSTMENT:
# Half and full team players with corresponding party names for each scenario
SCENARIO_PLAYER_PARTIES = [
    (range(5, 8), "linear_increase_decrease_half"),
    (range(8, 14), "linear_increase_decrease_full"),
    (range(14, 17), "increase_then_constant_half"),
    (range(17, 23), "increase_then_constant_full"),
    (range(23, 26), "skill_gap_half"),
    (range(26, 32), "skill_gap_full"),
    (range(32, 35), "huge_fall_then_jump_half"),
    (range(35, 41), "huge_fall_then_jump_full")
]


# TESTED_RATING_COEFS = [0.85, 0.89, 0.91, 1.0, 1.3]
"""
- linear increse in rank over 5000 games and then a linear decrease in 5000 games;

- linear increase for the first 2500 games and then a constant unchanging rank for the last 2500 games;

- linear increase for the first 1250 games, then a constant rank for 1250 games,
  then a pause in played games (last_time_played will be a month to create skill gap),
  then a constant rank for 2500 games;

- linear increase for the first 1250 games, then a huge fall in rank for 1250 games,
  then a huge jump in rank for 2500 games;
"""
REF_COEF_AND_GAMES = {
    "player_1": [(1.3, 1200, 1.0),(0.80, 1200, 1.0)],
    "player_2": [(1.3, 600, 1.0), (0.91, 600, 1.0)],
    "player_3": [(1.3, 300, 1.0), (0.91, 300, 1.0), (0.91, 600, 1.0)], #Need to implement gap here
    "player_4": [(1.3, 300, 1.0), (0.80, 300, 1.0), (1.5, 600, 1.0)],

    "player_5": [(1.3, 1200, 1.0),(0.80, 1200, 1.0)],
    "player_8": [(1.3, 600, 1.0), (0.91, 600, 1.0)],
    "player_14": [(1.3, 300, 1.0), (0.91, 300, 1.0), (0.91, 600, 1.0)], #Need to implement gap here
    "player_17": [(1.3, 300, 1.0), (0.80, 300, 1.0), (1.5, 600, 1.0)],

    "player_23": [(1.3, 1200, 1.0),(0.80, 1200, 1.0)],
    "player_26": [(1.3, 600, 1.0), (0.91, 600, 1.0)],
    "player_32": [(1.3, 300, 1.0), (0.91, 300, 1.0), (0.91, 600, 1.0)], #Need to implement gap here
    "player_35": [(1.3, 300, 1.0), (0.80, 300, 1.0), (1.5, 600, 1.0)],
}
# REF_COEF_AND_GAMES = {
#     "player_1": [(1.3, 100, 1.0),(0.80, 100, 1.0)],
#     "player_2": [(1.3, 50, 1.0), (0.91, 50, 1.0)],
#     "player_3": [(1.3, 25, 1.0), (0.91, 25, 1.0), (0.91, 50, 1.0)], #Need to implement gap here
#     "player_4": [(1.3, 25, 1.0), (0.80, 25, 1.0), (1.5, 50, 1.0)],

#     "player_5": [(1.3, 100, 1.0),(0.80, 100, 1.0)],
#     "player_8": [(1.3, 50, 1.0), (0.91, 50, 1.0)],
#     "player_14": [(1.3, 25, 1.0), (0.91, 25, 1.0), (0.91, 50, 1.0)], #Need to implement gap here
#     "player_17": [(1.3, 25, 1.0), (0.80, 25, 1.0), (1.5, 50, 1.0)],

#     "player_23": [(1.3, 100, 1.0),(0.80, 100, 1.0)],
#     "player_26": [(1.3, 50, 1.0), (0.91, 50, 1.0)],
#     "player_32": [(1.3, 25, 1.0), (0.91, 25, 1.0), (0.91, 50, 1.0)], #Need to implement gap here
#     "player_35": [(1.3, 25, 1.0), (0.80, 25, 1.0), (1.5, 50, 1.0)],
# }
# TDM games count = 300000, -> 1500 * 12
# FFA games count = 100000, -> 500 * 12
# Domination games count = 300000, -> 1500 * 12
# BR_1v99 games count = 100000, -> 500 * 12
# BR_4v96 games count = 300000, -> 1500 * 12
# SAD games count = 300000, -> 500 * 12
REF_INITIAL_TRUE_RATING = 500
REFERENCE_PLAYER_COUNT = 40

# Global start time for simulation (e.g., now)
GLOBAL_START_TIME = datetime.now(timezone.utc)

ONE_WEEK = timedelta(weeks=1)
ONE_YEAR = timedelta(days=365)
HALF_MINUTE = timedelta(seconds=30)

# Fixed gap between games (2 minutes)
GAME_GAP = timedelta(minutes=2)
