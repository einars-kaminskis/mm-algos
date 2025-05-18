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
ELO_K_FACTOR = 20
GLICKO_C_CONSTANT = 47.97 # sqrt((350^2 - 50^2)/(365/7)) as per Glickman's paper, if period_days is 7 and adjusted to my scenarios, where longest time away can be a year
GLICKO_MAX_RD = 350.0
GLICKO_MIN_RD = 50.0
MAX_RANK = 4000.0
TS_MAX_SIGMA = MAX_RANK / 8 # 8 standard deviations (3 to each side) should cover all the ranks
TS_MIN_SIGMA = MAX_RANK / 80
BASE_BETA = TS_MAX_SIGMA / 2
BASE_TAU = TS_MAX_SIGMA / 100

# Monkey patch, because the creators of the elote elo and glicko system didn't think that minimum_rating should be changable.
class ZeroFloorElo(EloCompetitor):
    _minimum_rating = 0
class ZeroFloorGlicko(GlickoCompetitor):
    _c = GLICKO_C_CONSTANT # sqrt((350^2 - 50^2)/t) as per Glickman's paper
    _rating_period_days = 7.0
    _minimum_rating = 0

TOTAL_PLAYERS = 100000

DISTRIBUTION = int(TOTAL_PLAYERS / 40)

SCENARIO_PLAYER_PARTIES = []

REF_COEF_AND_GAMES = {
    "player_1": [(1.3, 500, 1.0, 0),(0.5, 500, 1.0, 0)],
    "player_2": [(1.3, 500, 1.0, 0), (0.9, 500, 1.0, 0)],
    "player_3": [(1.3, 330, 1.0, 0), (0.9, 330, 1.0, 0)] + [(0.9, 3, 1.0, 40) for _ in range(110)],
    "player_4": [(1.3, 330, 1.0, 0), (0.001, 330, 1.0, 0), (1.7, 330, 1.0, 0)],
    "player_5": [(1.3, 500, 1.0, 0),(0.5, 500, 1.0, 0)],
    "player_6": [(1.3, 500, 1.0, 0), (0.9, 500, 1.0, 0)],
    "player_7": [(1.3, 330, 1.0, 0), (0.9, 330, 1.0, 0)] + [(0.9, 3, 1.0, 40) for _ in range(110)],
    "player_8": [(1.3, 330, 1.0, 0), (0.001, 330, 1.0, 0), (1.7, 330, 1.0, 0)],
}

REF_INITIAL_TRUE_RATING = 600
REFERENCE_PLAYER_COUNT = 8
