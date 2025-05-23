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

GLOBAL_START_TIME = datetime.now(timezone.utc) # Global start time for simulation

ONE_WEEK = timedelta(weeks=1)
ONE_YEAR = timedelta(days=365)
HALF_MINUTE = timedelta(seconds=30)
GAME_GAP = timedelta(minutes=2) # Fixed gap between games

# Test algorithm constants
TOTAL_PLAYERS = 10000
DISTRIBUTION_COUNT = 30
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

SCENARIO_PLAYER_PARTIES = []

# "player_number": [(ref_skill_coeficient, ref_games_count, party_coeficient, time_gap, k_factor), ...]
REF_COEF_AND_GAMES = {
    "player_1": [(1.7, 400, 1.0, 0, ELO_K_FACTOR),(0.34, 400, 1.0, 0, ELO_K_FACTOR)],
    "player_2": [(0.75, 800, 1.0, 0, ELO_K_FACTOR)],
    "player_3": [(0.7, 1, 1.0, 14, ELO_K_FACTOR) for _ in range(800)],
    "player_4": [(0.7, 1, 1.0, 30, ELO_K_FACTOR) for _ in range(800)],
    "player_5": [
        (1.875, 100, 1.0, 0, ELO_K_FACTOR),
        (0.1, 100, 1.0, 0, ELO_K_FACTOR),
        (1.875, 100, 1.0, 0, ELO_K_FACTOR),
        (0.1, 100, 1.0, 0, ELO_K_FACTOR),
        (1.875, 100, 1.0, 0, ELO_K_FACTOR),
        (0.1, 100, 1.0, 0, ELO_K_FACTOR),
        (1.875, 100, 1.0, 0, ELO_K_FACTOR),
        (0.1, 100, 1.0, 0, ELO_K_FACTOR),
    ],
    "player_6": [(1.65, 300, 1.0, 0, ELO_K_FACTOR), (0.88, 500, 1.0, 0, ELO_K_FACTOR)],
    "player_7": [(1.66, 300, 1.0, 0, 32), (0.88, 500, 1.0, 0, 32)],
    "player_8": [(1.65, 300, 1.0, 0, 10), (0.89, 500, 1.0, 0, 10)],
}

REF_INITIAL_TRUE_RATING = 600
REFERENCE_PLAYER_COUNT = 8
STARTING_PLAYER = 1
