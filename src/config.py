from datetime import datetime, timedelta, timezone
from elote import EloCompetitor, GlickoCompetitor

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
        base_performance: float = None,
        group_sizes: list = None,
        adjustments: dict = None,
        vp_weights: dict = None,
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
        self.base_performance = base_performance
        self.vp_weights = vp_weights if vp_weights is not None else {}
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
        base_performance = 20.00,
        group_sizes = [3, 6],
        vp_weights = {
          'kills': 1.00,
          'deaths': 0.95,
          'killstreak': 0.78,
          'time_alive': 0.10,
          'contesting_kills': 0.00,
          'objective_time': 0.00,
          'accuracy': 0.80,
          'damage_dealt': 0.90,
          'damage_taken': 0.84,
        },
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
                'mean_kills':    8,  'sd_kills':   3,
                'mean_deaths':  10,  'sd_deaths':   3,
                'mean_assists': 1.0, 'sd_assists': 0.5,
                'mean_accuracy':0.18,'sd_accuracy':0.01,
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
                'mean_kills':   15, 'sd_kills':  5,
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
                'mean_kills':   25, 'sd_kills':  7,
                'mean_deaths':  19, 'sd_deaths':  6,
                'mean_assists': 2.0,'sd_assists': 1.0,
                'mean_accuracy':0.36,'sd_accuracy':0.02,
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
        base_performance = 20.00,
        vp_weights = {
          'kills': 1.00,
          'deaths': 0.95,
          'killstreak': 0.78,
          'time_alive': 0.10,
          'contesting_kills': 0.00,
          'objective_time': 0.00,
          'accuracy': 0.80,
          'damage_dealt': 0.90,
          'damage_taken': 0.84,
        },
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
                'mean_kills':    5, 'sd_kills':  3,
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
                'mean_kills':   13, 'sd_kills':  4,
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
                'mean_kills':   25, 'sd_kills':  8,
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
        base_performance = 20.00,
        vp_weights = {
          'kills': 0.54,
          'deaths': 0.48,
          'killstreak': 0.45,
          'time_alive': 0.40,
          'contesting_kills': 0.80,
          'objective_time': 1.00,
          'accuracy': 0.50,
          'damage_dealt': 0.59,
          'damage_taken': 0.47,
        },
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
                'mean_contesting_kills':1,   'sd_contesting_kills':1,
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
        base_performance = 20.00,
        vp_weights = {
          'kills': 0.70,
          'deaths': 0.10,
          'killstreak': 0.70,
          'time_alive': 1.00,
          'contesting_kills': 0.00,
          'objective_time': 0.00,
          'accuracy': 0.60,
          'damage_dealt': 0.68,
          'damage_taken': 0.50,
        },
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
                'mean_kills':    3,  'sd_kills':   2,
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
                'mean_kills':    8,  'sd_kills':   3,
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
            "kills": 0.90,
            "deaths": 0.10,
            "assists": 0.80,
            "damage_dealt": 0.90,
            "damage_taken": 0.30,
            "damage_missed": 0.20,
            "headshot_damage_dealt": 0.80,
            "torso_damage_dealt": 0.60,
            "leg_damage_dealt": 0.15,
            "accuracy": 0.60,
            "headshot_accuracy": 0.80,
            "torso_accuracy": 0.60,
            "leg_accuracy": 0.15,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.50,
            "deaths_per_minute": 0.00,
            "assists_per_minute": 0.40,
            "damage_dealt_per_minute": 0.50,
            "damage_taken_per_minute": 0.20,
            "kill_death_ratio": 0.00,
            "damage_dealt_and_taken_ratio": 0.35,
            "killstreak": 0.90,
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
        base_performance = 20.00,
        vp_weights = {
          'kills': 0.70,
          'deaths': 0.10,
          'killstreak': 0.70,
          'time_alive': 1.00,
          'contesting_kills': 0.00,
          'objective_time': 0.00,
          'accuracy': 0.60,
          'damage_dealt': 0.68,
          'damage_taken': 0.50,
        },
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
                'mean_kills':    6, 'sd_kills':  3,
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
            "kills": 0.90,
            "deaths": 0.10,
            "assists": 0.82,
            "damage_dealt": 0.90,
            "damage_taken": 0.80,
            "damage_missed": 0.20,
            "headshot_damage_dealt": 0.80,
            "torso_damage_dealt": 0.60,
            "leg_damage_dealt": 0.15,
            "accuracy": 0.60,
            "headshot_accuracy": 0.80,
            "torso_accuracy": 0.60,
            "leg_accuracy": 0.15,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.50,
            "deaths_per_minute": 0.00,
            "assists_per_minute": 0.42,
            "damage_dealt_per_minute": 0.50,
            "damage_taken_per_minute": 0.40,
            "kill_death_ratio": 0.00,
            "damage_dealt_and_taken_ratio": 0.45,
            "killstreak": 0.90,
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
        base_performance = 20.00,
        vp_weights = {
          'kills': 0.88,
          'deaths': 0.90,
          'killstreak': 0.85,
          'time_alive': 1.00,
          'contesting_kills': 0.00,
          'objective_time': 0.00,
          'accuracy': 0.89,
          'damage_dealt': 0.50,
          'damage_taken': 0.48,
        },
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
                'mean_kills':    8, 'sd_kills':  3,
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
                'mean_kills':   18, 'sd_kills': 4,
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
                'mean_kills':                  25,   'sd_kills':                  5,
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
            "kills": 0.95,
            "deaths": 0.95,
            "assists": 0.55,
            "damage_dealt": 0.50,
            "damage_taken": 0.50,
            "damage_missed": 0.60,
            "headshot_damage_dealt": 0.85,
            "torso_damage_dealt": 0.60,
            "leg_damage_dealt": 0.10,
            "accuracy": 0.95,
            "headshot_accuracy": 0.85,
            "torso_accuracy": 0.60,
            "leg_accuracy": 0.10,
            "contesting_kills": 0.00,
            "objective_time": 0.00,
            "longest_time_alive": 1.00,
            "kills_per_minute": 0.75,
            "deaths_per_minute": 0.75,
            "assists_per_minute": 0.45,
            "damage_dealt_per_minute": 0.40,
            "damage_taken_per_minute": 0.40,
            "kill_death_ratio": 0.85,
            "damage_dealt_and_taken_ratio": 0.50,
            "killstreak": 0.90,
            "win_streak":1.00,
            "win_loss_ratio": 1.00,
            "is_tie": 1.00
        },
    ),
]

# --------------------------------------------------------------------
# Interpolation function for continuous scaling across rating ranges.
# We assume three anchor points:
#   - at rating 200: uses low skill metrics,
#   - at rating 1300: uses medium skill metrics,
#   - at rating 3000: uses high skill metrics.
# --------------------------------------------------------------------
def interpolate_stat(low_val, med_val, high_val, true_rating: float) -> int | float:
    if true_rating <= 200.0:
        # extrapolate below 200 at slope₁
        slope = (med_val - low_val) / (1300.0 - 200.0)
        result = low_val + (true_rating - 200.0) * slope

    elif true_rating <= 1300.0:
        # interpolate between 200 and 1300
        slope = (med_val - low_val) / (1300.0 - 200.0)
        result = low_val + (true_rating - 200.0) * slope

    elif true_rating <= 3000.0:
        # interpolate between 1300 and 3000
        slope = (high_val - med_val) / (3000.0 - 1300.0)
        result = med_val + (true_rating - 1300.0) * slope

    else:
        # extrapolate above 3000 at slope₂
        slope = (high_val - med_val) / (3000.0 - 1300.0)
        result = high_val + (true_rating - 3000.0) * slope
    
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

# Returns a UTC‑aware datetime or returns unchanged datetime.
def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def roundInt(number) -> int:
    return int(round(number, 0))

# ------------------------
# CONSTANTS
# ------------------------
STAT_ATTRS = [
    'kills',
    'deaths',
    'killstreak',
    'longest_time_alive',
    'contesting_kills',
    'objective_time',
    'accuracy',
    'damage_dealt',
    'damage_taken',
]

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

# If matchmaking testing and player sorting ever gets created, this is a 
# rating distribution taken from Counter Strike 2 Premier games in 2025: https://csstats.gg/leaderboards
# RANK_DISTRIBUTION_WEIGHTS = [
#     0.0280, 0.0462, 0.0771, 0.0714, 0.0614, 0.0509, 0.0545, 0.0568,
#     0.0630, 0.0585, 0.0551, 0.0546, 0.0510, 0.0508, 0.0424, 0.0356,
#     0.0317, 0.0263, 0.0234, 0.0168, 0.0126, 0.0097, 0.0067, 0.0052,
#     0.0037, 0.0028, 0.0014, 0.0005, 0.0003, 0.0002, 0.0002, 0.0002,
#     0.0002, 0.0002, 0.0002, 0.0002, 0.0002
# ]

# This is better for testing, because we will look at many reference players
# and they need players in their rating level to get games.
RANK_DISTRIBUTION_WEIGHTS = [
    2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027,
    2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027,
    2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027,
    2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027, 2.7027,
    2.7027, 2.7027, 2.7027, 2.7027, 2.7027
]

TOTAL_PLAYERS = 2000 # took 2 minutes to build 5000 players (40000 would technically be 16 minutes) For testing (TODO: CHANGE TO 40_000)

DISTRIBUTION = int(TOTAL_PLAYERS / 24)

# Half and full team players with corresponding party names for each scenario
SCENARIO_PLAYER_PARTIES = [
    # (range(5, 8), "linear_increase_decrease_half"),
    # (range(8, 14), "linear_increase_decrease_full"),
    # (range(14, 17), "increase_then_constant_half"),
    # (range(17, 23), "increase_then_constant_full"),
    # (range(23, 26), "skill_gap_half"),
    # (range(26, 32), "skill_gap_full"),
    # (range(32, 35), "huge_fall_then_jump_half"),
    # (range(35, 41), "huge_fall_then_jump_full")
]

REF_INITIAL_TRUE_RATING = 600
REFERENCE_PLAYER_COUNT = 8

# Time constants
GLOBAL_START_TIME = datetime.now(timezone.utc) # Global start time for simulation

ONE_WEEK = timedelta(weeks=1)
ONE_YEAR = timedelta(days=365)
HALF_MINUTE = timedelta(seconds=30)
GAME_GAP = timedelta(minutes=2) # Fixed gap between games

# Test algorithm constants
TOTAL_PLAYERS = 100000
DISTRIBUTION_COUNT = 40
DISTRIBUTION = int(TOTAL_PLAYERS / DISTRIBUTION_COUNT)

ELO_K_FACTOR = 20
GLICKO_MAX_RD = 350.0
GLICKO_MIN_RD = 30.0
MAX_RANK = DISTRIBUTION_COUNT * 100 / 2
TS_MAX_SIGMA = MAX_RANK / 6 # Cover 3 standard deviations worth of the rating in both directions.
TS_MIN_SIGMA = MAX_RANK / 60 # 10 times lower deviation for certain games
BASE_BETA = TS_MAX_SIGMA / 2 # As per trueskill package initial values
BASE_TAU = TS_MAX_SIGMA / 100 # As per trueskill package initial values

# Monkey patch, because the creators of the elote elo and glicko system didn't think that minimum_rating should be changable.
class ZeroFloorElo(EloCompetitor):
    _minimum_rating = 0
class ZeroFloorGlicko(GlickoCompetitor):
    _minimum_rating = 0

# "player_number": [(ref_skill_coeficient, ref_games_count, party_coeficient, time_gap, k_factor), ...]
REF_COEF_AND_GAMES = {
    "player_1": [(1.2, 400, 1.0, 0, ELO_K_FACTOR),(0.3, 400, 1.0, 0, ELO_K_FACTOR)],
    "player_2": [(0.75, 800, 1.0, 0, ELO_K_FACTOR)],
    "player_3": [(0.82, 1, 1.0, 14, ELO_K_FACTOR) for _ in range(800)],
    "player_4": [(0.82, 1, 1.0, 30, ELO_K_FACTOR) for _ in range(800)],
    "player_5": [
        (1.7, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.7, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.7, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.7, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
    ],
    "player_6": [(1.2, 300, 1.0, 0, ELO_K_FACTOR), (0.75, 500, 1.0, 0, ELO_K_FACTOR)],
    "player_7": [(1.2, 300, 1.0, 0, 32), (0.75, 500, 1.0, 0, 32)],
    "player_8": [(1.2, 300, 1.0, 0, 10), (0.75, 500, 1.0, 0, 10)],
}
