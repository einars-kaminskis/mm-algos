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
TOTAL_PLAYERS = 25000
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
    "player_1": [(1.02, 400, 1.0, 0, ELO_K_FACTOR),(0.1, 400, 1.0, 0, ELO_K_FACTOR)],
    "player_2": [(0.83, 800, 1.0, 0, ELO_K_FACTOR)],
    "player_3": [(0.81, 1, 1.0, 14, ELO_K_FACTOR) for _ in range(800)],
    "player_4": [(0.80, 1, 1.0, 30, ELO_K_FACTOR) for _ in range(800)],
    "player_5": [
        (1.06, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.06, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.06, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
        (1.06, 100, 1.0, 0, ELO_K_FACTOR),
        (0.001, 100, 1.0, 0, ELO_K_FACTOR),
    ],
    "player_6": [(0.9975, 300, 1.0, 0, ELO_K_FACTOR), (0.837, 500, 1.0, 0, ELO_K_FACTOR)],
    "player_7": [(0.9975, 300, 1.0, 0, 32), (0.837, 500, 1.0, 0, 32)],
    "player_8": [(0.9976, 300, 1.0, 0, 10), (0.837, 500, 1.0, 0, 10)],
}

REF_INITIAL_TRUE_RATING = 600
REFERENCE_PLAYER_COUNT = 8
STARTING_PLAYER = 1
