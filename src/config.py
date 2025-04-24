import os
import datetime
from dotenv import load_dotenv

load_dotenv()  # This will load variables from a .env file in your root directory

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
        simulated_games_count: int = 0,
        group_sizes: list = None,
        adjustments: dict = None,
        vp_weights: list = None, # Valuable player weight order:
                                 # [kills, deaths, killstreak, time_alive, contesting_kills,
                                 # objective_time, accuracy, damage_dealt, damage_taken]
    ) -> None:
        self.type = type
        self.team_size = team_size
        self.team_count = team_count
        self.time_limit_mean = time_limit_mean
        self.time_limit_variance = time_limit_variance
        self.kill_cap = kill_cap
        self.point_limit = point_limit
        self.winning_round_limit = winning_round_limit
        self.simulated_games_count = simulated_games_count
        self.vp_weights = vp_weights if vp_weights is not None else []
        self.group_sizes = group_sizes if group_sizes is not None else []
        self.adjustments = adjustments if adjustments is not None else {}

GAME_TYPES = [
    GameMode(
        type = "TDM", # Team deathmatch (from Call of Duty)
        team_size = 6,
        team_count = 2,
        time_limit_mean = 480, # seconds or 8 minutes
        time_limit_variance = 60, # seconds or 1 minutes
        kill_cap = 50,
        simulated_games_count = 200000,
        vp_weights = [1.00, 0.67, 0.50, 0.33, 0.00, 0.00, 0.33, 0.50, 0.00],
        group_sizes = [3, 6],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 40, "pgts_sd_total_wins": 15,
                "pgts_mean_total_loses": 60, "pgts_sd_total_loses": 15,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 8, "sd_kills": 3,
                "mean_deaths": 12, "sd_deaths": 3,
                "mean_assists": 2, "sd_assists": 1,
                "mean_accuracy": 12.0, "sd_accuracy": 4.0,
                "mean_headshot_accuracy": 300, "sd_headshot_accuracy": 100,
                "mean_torso_and_arm_accuracy": 350, "sd_torso_and_arm_accuracy": 120,
                "mean_best_killstreak": 3, "sd_best_killstreak": 1,

                # For GamePlayer:
                "mean_longest_time_alive": 30, "sd_longest_time_alive": 10,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 50, "pgts_sd_total_wins": 15,
                "pgts_mean_total_loses": 50, "pgts_sd_total_loses": 15,
                "pgts_mean_total_ties": 10, "pgts_sd_total_ties": 3,
                "pgts_mean_win_streak": 3, "pgts_sd_win_streak": 1.5,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 13, "sd_kills": 4,
                "mean_deaths": 13, "sd_deaths": 4,
                "mean_assists": 2, "sd_assists": 1,
                "mean_accuracy": 18.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 500, "sd_headshot_accuracy": 150,
                "mean_torso_and_arm_accuracy": 400, "sd_torso_and_arm_accuracy": 120,
                "mean_best_killstreak": 5, "sd_best_killstreak": 2,

                # For GamePlayer:
                "mean_longest_time_alive": 45, "sd_longest_time_alive": 15,
                "mean_contesting_kills": 2, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 70, "pgts_sd_total_wins": 15,
                "pgts_mean_total_loses": 30, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 6, "pgts_sd_win_streak": 2,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 22, "sd_kills": 5,
                "mean_deaths": 8, "sd_deaths": 3,
                "mean_assists": 1, "sd_assists": 1,
                "mean_accuracy": 25.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 900, "sd_headshot_accuracy": 200,
                "mean_torso_and_arm_accuracy": 650, "sd_torso_and_arm_accuracy": 150,
                "mean_best_killstreak": 8, "sd_best_killstreak": 2,
                
                # For GamePlayer:
                "mean_longest_time_alive": 60, "sd_longest_time_alive": 20,
                "mean_contesting_kills": 3, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            }
        },
    ),
    GameMode(
        type = "FFA", # Free-for-All (from Call of Duty)
        team_size = 1,
        team_count = 12,
        time_limit_mean = 480, # seconds or 8 minutes
        time_limit_variance = 60, # seconds or 1 minutes
        kill_cap = 50,
        simulated_games_count = 20000,
        vp_weights = [1.00, 0.13, 0.38, 0.38, 0.00, 0.00, 0.25, 0.38, 0.00],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 30, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 70, "pgts_sd_total_loses": 15,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 0, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 3, "sd_kills": 2,
                "mean_deaths": 15, "sd_deaths": 4,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 12.0, "sd_accuracy": 4.0,
                "mean_headshot_accuracy": 150, "sd_headshot_accuracy": 50,
                "mean_torso_and_arm_accuracy": 175, "sd_torso_and_arm_accuracy": 60,
                "mean_best_killstreak": 2, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 20, "sd_longest_time_alive": 8,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 50, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 40, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 2, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 10, "sd_kills": 4,
                "mean_deaths": 10, "sd_deaths": 4,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 18.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 300, "sd_headshot_accuracy": 100,
                "mean_torso_and_arm_accuracy": 350, "sd_torso_and_arm_accuracy": 120,
                "mean_best_killstreak": 4, "sd_best_killstreak": 1.5,
                
                # For GamePlayer:
                "mean_longest_time_alive": 35, "sd_longest_time_alive": 10,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 60, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 30, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 4, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 20, "sd_kills": 5,
                "mean_deaths": 6, "sd_deaths": 3,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 25.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 500, "sd_headshot_accuracy": 150,
                "mean_torso_and_arm_accuracy": 700, "sd_torso_and_arm_accuracy": 150,
                "mean_best_killstreak": 6, "sd_best_killstreak": 2,
                
                # For GamePlayer:
                "mean_longest_time_alive": 50, "sd_longest_time_alive": 15,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            }
        },
    ),
    GameMode(
        type = "Domination", # Domination (from Call of Duty)
        team_size = 6,
        team_count = 2,
        time_limit_mean = 498, # seconds or 8,3 minutes
        time_limit_variance = 55, # seconds
        point_limit = 200, # 1 point per 5 seconds for each of the 3 zones
        simulated_games_count = 200000,
        vp_weights = [0.14, 0.00, 0.00, 0.00, 0.14, 1.00, 0.07, 0.07, 0.00],
        group_sizes = [3, 6],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 35, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 65, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 8, "sd_kills": 4,
                "mean_deaths": 15, "sd_deaths": 5,
                "mean_assists": 2, "sd_assists": 2,
                "mean_accuracy": 12.0, "sd_accuracy": 4.0,
                "mean_headshot_accuracy": 300, "sd_headshot_accuracy": 100,
                "mean_torso_and_arm_accuracy": 350, "sd_torso_and_arm_accuracy": 120,
                "mean_best_killstreak": 3, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 30, "sd_longest_time_alive": 10,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 30, "sd_objective_time": 20,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 45, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 55, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 6, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 3, "pgts_sd_win_streak": 1.5,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 20, "sd_kills": 6,
                "mean_deaths": 15, "sd_deaths": 5,
                "mean_assists": 3, "sd_assists": 2,
                "mean_accuracy": 18.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 400, "sd_headshot_accuracy": 120,
                "mean_torso_and_arm_accuracy": 400, "sd_torso_and_arm_accuracy": 120,
                "mean_best_killstreak": 4, "sd_best_killstreak": 1.5,
                
                # For GamePlayer:
                "mean_longest_time_alive": 45, "sd_longest_time_alive": 15,
                "mean_contesting_kills": 2, "sd_contesting_kills": 1,
                "mean_objective_time": 60, "sd_objective_time": 30,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 55, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 40, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 4, "pgts_sd_total_ties": 1,
                "pgts_mean_win_streak": 5, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 35, "sd_kills": 10,
                "mean_deaths": 10, "sd_deaths": 4,
                "mean_assists": 4, "sd_assists": 3,
                "mean_accuracy": 25.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 800, "sd_headshot_accuracy": 200,
                "mean_torso_and_arm_accuracy": 600, "sd_torso_and_arm_accuracy": 150,
                "mean_best_killstreak": 6, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 60, "sd_longest_time_alive": 20,
                "mean_contesting_kills": 3, "sd_contesting_kills": 1,
                "mean_objective_time": 90, "sd_objective_time": 30,
            }
        },
    ),
    GameMode(
        type = "BR_1V99", # Battle royale 1v99 (from Fortnite)
        team_size = 1,
        team_count = 100,
        time_limit_mean = 1320, # seconds or 22 minutes
        time_limit_variance = 160, # seconds or 2,67 minutes
        kill_cap = 99,
        simulated_games_count = 20000,
        vp_weights = [0.63, 0.25, 0.13, 1.00, 0.00, 0.00, 0.13, 0.38, 0.00],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 20, "pgts_sd_total_wins": 8,
                "pgts_mean_total_loses": 80, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 0, "pgts_sd_total_ties": 0,
                "pgts_mean_win_streak": 0, "pgts_sd_win_streak": 0,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 1, "sd_kills": 1,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 10.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 50, "sd_headshot_accuracy": 20,
                "mean_torso_and_arm_accuracy": 70, "sd_torso_and_arm_accuracy": 30,
                "mean_best_killstreak": 1, "sd_best_killstreak": 0.5,
                
                # For GamePlayer:
                "mean_longest_time_alive": 20, "sd_longest_time_alive": 8,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 30, "pgts_sd_total_wins": 8,
                "pgts_mean_total_loses": 70, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 0, "pgts_sd_total_ties": 0,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 3, "sd_kills": 2,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 15.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 150, "sd_headshot_accuracy": 50,
                "mean_torso_and_arm_accuracy": 200, "sd_torso_and_arm_accuracy": 60,
                "mean_best_killstreak": 2, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 30, "sd_longest_time_alive": 8,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 20, "pgts_sd_total_wins": 8,
                "pgts_mean_total_loses": 80, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 0, "pgts_sd_total_ties": 0,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 8, "sd_kills": 4,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 0, "sd_assists": 0,
                "mean_accuracy": 25.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 300, "sd_headshot_accuracy": 80,
                "mean_torso_and_arm_accuracy": 400, "sd_torso_and_arm_accuracy": 100,
                "mean_best_killstreak": 3, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 30, "sd_longest_time_alive": 10,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            }
        },
    ),
    GameMode(
        type = "BR_4V96", # Battle royale 4v96 (from Fortnite)
        team_size = 4,
        team_count = 25,
        time_limit_mean = 1620, # seconds or 27 minutes
        time_limit_variance = 180, # seconds or 3 minutes
        kill_cap = 96,
        simulated_games_count = 140000,
        vp_weights = [0.57, 0.57, 0.00, 1.00, 0.00, 0.00, 0.29, 0.43, 0.00],
        group_sizes = [2, 4],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 25, "pgts_sd_total_wins": 8,
                "pgts_mean_total_loses": 75, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 3, "pgts_sd_total_ties": 1,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 1, "sd_kills": 1,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 2, "sd_assists": 2,
                "mean_accuracy": 10.0, "sd_accuracy": 4.0,
                "mean_headshot_accuracy": 90, "sd_headshot_accuracy": 30,
                "mean_torso_and_arm_accuracy": 105, "sd_torso_and_arm_accuracy": 40,
                "mean_best_killstreak": 2, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 200, "sd_longest_time_alive": 80,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 40, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 60, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 4, "pgts_sd_total_ties": 1,
                "pgts_mean_win_streak": 2, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 3, "sd_kills": 2,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 2, "sd_assists": 2,
                "mean_accuracy": 15.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 210, "sd_headshot_accuracy": 70,
                "mean_torso_and_arm_accuracy": 245, "sd_torso_and_arm_accuracy": 80,
                "mean_best_killstreak": 3, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 360, "sd_longest_time_alive": 120,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 50, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 40, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 4, "pgts_sd_total_ties": 1,
                "pgts_mean_win_streak": 3, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 6, "sd_kills": 3,
                "mean_deaths": 1, "sd_deaths": 0,
                "mean_assists": 1, "sd_assists": 1,
                "mean_accuracy": 22.0, "sd_accuracy": 6.0,
                "mean_headshot_accuracy": 390, "sd_headshot_accuracy": 120,
                "mean_torso_and_arm_accuracy": 455, "sd_torso_and_arm_accuracy": 130,
                "mean_best_killstreak": 4, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 720, "sd_longest_time_alive": 180,
                "mean_contesting_kills": 0, "sd_contesting_kills": 0,
                "mean_objective_time": 0, "sd_objective_time": 0,
            }
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
        simulated_games_count = 160000,
        vp_weights = [1.00, 0.57, 0.29, 0.00, 0.00, 0.00, 0.14, 0.29, 0.00],
        group_sizes = [2, 5],
        adjustments = {
            # Low skill
            "low": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 30, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 70, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 5, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 1, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 8, "sd_kills": 3,
                "mean_deaths": 16, "sd_deaths": 4,
                "mean_assists": 3, "sd_assists": 2,
                "mean_accuracy": 12.0, "sd_accuracy": 4.0,
                "mean_headshot_accuracy": 240, "sd_headshot_accuracy": 80,
                "mean_torso_and_arm_accuracy": 280, "sd_torso_and_arm_accuracy": 90,
                "mean_best_killstreak": 3, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 25, "sd_longest_time_alive": 8,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # Medium skill
            "med": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 40, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 50, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 6, "pgts_sd_total_ties": 2,
                "pgts_mean_win_streak": 3, "pgts_sd_win_streak": 1.5,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 15, "sd_kills": 4,
                "mean_deaths": 15, "sd_deaths": 4,
                "mean_assists": 2, "sd_assists": 2,
                "mean_accuracy": 18.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 450, "sd_headshot_accuracy": 120,
                "mean_torso_and_arm_accuracy": 525, "sd_torso_and_arm_accuracy": 130,
                "mean_best_killstreak": 4, "sd_best_killstreak": 1.5,
                
                # For GamePlayer:
                "mean_longest_time_alive": 35, "sd_longest_time_alive": 10,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            },
            # High skill
            "high": {
                # For PlayerGameTypeStats:
                "pgts_mean_total_games_played": 100, "pgts_sd_total_games_played": 20,
                "pgts_mean_total_wins": 45, "pgts_sd_total_wins": 10,
                "pgts_mean_total_loses": 40, "pgts_sd_total_loses": 10,
                "pgts_mean_total_ties": 4, "pgts_sd_total_ties": 1,
                "pgts_mean_win_streak": 4, "pgts_sd_win_streak": 1,

                #For both PlayerGameTypeStats and GamePlayer:
                "mean_kills": 25, "sd_kills": 5,
                "mean_deaths": 10, "sd_deaths": 3,
                "mean_assists": 1, "sd_assists": 1,
                "mean_accuracy": 20.0, "sd_accuracy": 5.0,
                "mean_headshot_accuracy": 625, "sd_headshot_accuracy": 150,
                "mean_torso_and_arm_accuracy": 750, "sd_torso_and_arm_accuracy": 150,
                "mean_best_killstreak": 5, "sd_best_killstreak": 1,
                
                # For GamePlayer:
                "mean_longest_time_alive": 40, "sd_longest_time_alive": 15,
                "mean_contesting_kills": 1, "sd_contesting_kills": 1,
                "mean_objective_time": 0, "sd_objective_time": 0,
            }
        },
    ),
]

# --------------------------------------------------------------------
# Interpolation function for continuous scaling across rating ranges.
# We assume three anchor points:
#   - at rating 1000: use low anchor,
#   - at rating 1500: use medium anchor,
#   - at rating 2000: use high anchor.
# For ratings below 1000, we extrapolate downward using the same slope as from 1000 to 1500.
# For ratings = 2000, we use the high anchor.
# For ratings above 2000, we extrapolate upward using the same slope as from 1500 to 2000.
def interpolate_stat(low_val, med_val, high_val, true_rating):
    if true_rating < 1000:
        slope = (med_val - low_val) / 500.0
        return low_val - (1000 - true_rating) * slope
    elif true_rating < 1500:
        t = (true_rating - 1000) / 500.0
        return low_val + t * (med_val - low_val)
    elif true_rating < 2000:
        t = (true_rating - 1500) / 500.0
        return med_val + t * (high_val - med_val)
    elif true_rating == 2000:
        return high_val
    elif true_rating > 2000:
        # Extrapolate with same slope as 1500->2000.
        slope = (high_val - med_val) / 500.0
        return high_val + (true_rating - 2000) * slope

def interpolate_stats(low_stats: dict, med_stats: dict, high_stats: dict, true_rating: int) -> dict:
    result = {}
    # Assume all dictionaries have the same keys.
    for key in low_stats:
        result[key] = interpolate_stat(low_stats[key], med_stats[key], high_stats[key], true_rating)
    return result

def get_stat_parameters(game_mode: GameMode, true_rating: int) -> dict:
    low, med, high = (game_mode.adjustments["low"], game_mode.adjustments["med"], game_mode.adjustments["high"],)
    return interpolate_stats(low, med, high, true_rating)


TOTAL_PLAYERS = 40000
REFERENCE_PLAYER_COUNT = 40

# Global start time for simulation (e.g., now)
GLOBAL_START_TIME = datetime.datetime.now(datetime.timezone.utc)

# Fixed gap between games (2 minutes)
GAME_GAP = datetime.timedelta(minutes=2)
"""
Simulēto datu info:
  - Apskatīt dažādus game modes:
    - Team deathmatch;
    - Free-for-All;
    - Domination;
    - Battle royale 1v99;
    - Battle royale 4v96;
    - Search and Destroy;
  - Apstrādāt dažādu spēlētāju skaitu:
    - 100 cilvēki;
    - 500 cilvēki;
    - 1000 cilvēki;
    - 10000 cilvēki;
  - Spēlēšana vienam pašam un grupā (party):
    - Apskatot spēlētāju, kas ir grupā un cīnās pret citiem spēlētājiem:
      - Grupa sastāda pusi komandas;
      - Grupa sastāda visu komandu;
    - Apskatot spēlētāju, kas spēlē viens un cīnās pret citiem spēlētājiem.
  - Apejamības iespējas algoritmiem (lai gūtu negodīgu advantage):
    - Spēja adaptēties uz vienmērīgu pieaugumu statistikā spēlētājam;
    - Spēja adaptēties uz vienmērīgu kritumu statistikā spēlētājam;
    - Spēja adaptēties uz vienmērīgu pieaugumu un tad konstantu statistiku spēlētājam;
    - Spēja adaptēties uz ilgu pauzi spēlētājam, veidojot skill gap;
    - Spēja adaptēties uz strauju kritumu un tad pieaugumu statistikā spēlētājam (smurfing);
"""

"""
Team deathmatch:
  - 40000 players;
  - 300000 games;
  - 40 reference players:
    - 4 individual reference players:
      - linear increse in rank over 5000 games and then a linear decrease in 5000 games;
      - linear increase for the first 2500 games and then a constant unchanging rank for the last 2500 games;
      - linear increase for the first 1250 games, then a constant rank for 1250 games,
        then a pause in played games (last_time_played will be a month to create skill gap),
        then a constant rank for 2500 games;
      - linear increase for the first 1250 games, then a huge fall in rank for 1250 games,
        then a huge jump in rank for 2500 games;
    - 4 reference parties:
      - a 3 player party:
        - same rank changing scenarios.
      - a 6 player party:
        - same rank changing scenarios.
Domination:
  - 40000 players;
  - 300000 games;
  - 40 reference players:
    - 4 individual reference players:
      - same rank changing scenarios.
    - 4 reference parties:
      - a 3 player party:
        - same rank changing scenarios.
      - a 6 player party:
        - same rank changing scenarios.
Free-for-All:
  - 40000 players;
  - 100000 games;
  - 4 reference players:
    - 4 individual reference players:
      - same rank changing scenarios.
Battle royale 1v99:
  - 40000 players;
  - 100000 games;
  - 4 reference players:
    - 4 individual reference players:
      - same rank changing scenarios.
Battle royale 4v96:
  - 40000 players;
  - 300000 games;
  - 28 reference players:
    - 4 individual reference players:
      - same rank changing scenarios.
    - 4 reference parties:
      - a 2 player party:
        - same rank changing scenarios.
      - a 4 player party:
        - same rank changing scenarios.
Search and Destroy:
  - 40000 players;
  - 300000 games;
  - 32 reference players:
    - 4 individual reference players:
      - same rank changing scenarios.
    - 4 reference parties:
      - a 2 player party:
        - same rank changing scenarios.
      - a 5 player party:
        - same rank changing scenarios.


All together:
  - 40000 total players;
  - 40 reference players - Player_1 to Player_40 - starting with fresh ranks;
  - Rest of the players start with random ranks and stats for each game type;
  - 1400000 games in total - theoretical maximum.
  - Worst case all players playing at the same time occupies 2036 players in all game modes.
"""

"""
Rank distribution in Counter strike 2 Season 2 premier:
  0 - 99 = 0.0280 (2.80%),
  100 - 199 = 0.0462 (4.62%),
  200 - 299 = 0.0771 (7.71%),
  300 - 399 = 0.0714 (7.14%),
  400 - 499 = 0.0614 (6.14%),
  500 - 599 = 0.0509 (5.09%),
  600 - 699 = 0.0545 (5.45%),
  700 - 799 = 0.0568 (5.68%),
  800 - 899 = 0.0630 (6.30%),
  900 - 999 = 0.0585 (5.85%),
  1000 - 1099 = 0.0551 (5.51%),
  1100 - 1199 = 0.0546 (5.46%),
  1200 - 1299 = 0.0510 (5.10%),
  1300 - 1399 = 0.0508 (5.08%),
  1400 - 1499 = 0.0424 (4.24%),
  1500 - 1599 = 0.0356 (3.56%),
  1600 - 1699 = 0.0317 (3.17%),
  1700 - 1799 = 0.0263 (2.63%),
  1800 - 1899 = 0.0234 (2.34%),
  1900 - 1999 = 0.0168 (1.68%),
  2000 - 2099 = 0.0126 (1.26%),
  2100 - 2199 = 0.0097 (0.97%),
  2200 - 2299 = 0.0067 (0.67%),
  2300 - 2399 = 0.0052 (0.52%),
  2400 - 2499 = 0.0037 (0.37%),
  2500 - 2599 = 0.0028 (0.28%),
  2600 - 2699 = 0.0014 (0.14%),
  2700 - 2799 = 0.0005 (0.05%),
  2800 - 2899 = 0.0003 (0.03%),
  2900 - 2999 = 0.0002 (0.02%),
  3000 - 3099 = 0.0002 (0.02%),
  3100 - 3199 = 0.0002 (0.02%),
  3200 - 3299 = 0.0002 (0.02%),
  3300 - 3399 = 0.0002 (0.02%),
  3400 - 3499 = 0.0002 (0.02%),
  3500 - 3599 = 0.0002 (0.02%),
  3600 - 3699 = 0.0002 (0.02%)
  3700+ = <0.0002 (<0.02%)
"""

"""
Simulation Information Summary

===============================================
Game Modes (Based on config.py & Simulation Logic)
===============================================
0. Rules across all game modes for simplicity:
   - Each player has 100 HP;
   - Each player has an automatic weapon that does equal damage to any body part;
   - Every player has the same and a stable connection to the game and ping and connection are not a part of the simulation;
   - Different regions don't matter, since we don't look at connection and ping;
   - Every player plays during the game, there are no AFK players and no early leavers as well as no missing players from team;
   - We don't look at how skill in one game mode impacts the skill in some other game mode;
   - If a player has a part_name and there are other players with the same party_name,
     then they must play each match together in one team;
   - Simulation:
     - Every game mode uses the same set of 40 reference players, since each game_mode has separate ranking;
     - Some game modes have less players in a party than some other ones,
       so in those game modes we would just remove one player and the same one every time from the party throughout the simulation for that game mode.
     - Results of a game go from top to bottom:
       - We first get the duration of the game;
       - We then put the reference player or party of reference players in one team;
       - We then look at the current scenario we have to fullfil in order to simulate data correctly;
       - We then set up the GamePlayer stats of the reference players based on the scenario we want to fullfil;
       - After that we set the GamePlayer stats for other players to fullfil the scenario we want;
       - Then we update the overall stats of every player that participated in that certain game and cycle through like this until we are done with the scenario.
     - Not all table attributes can be applied in every game mode;
     - Every applicable attribute should be consistent with every other attribute as well as other players in the game,
       as well as the game itself and as well as the player's stats. This means that there are no situations,
       where a players somehow gets way less/more kills or way less/more objective time or way less/more of any other attribute.
     - Average skill stats for every attribute for a GamePlayer during a game should come from real life average data for every skill level.
       Currently a ref_skill is used to give some random adjustment for some arbitrary calculation,
       but that is meant to be a prototype calculation and needs to be changed from info from scraped data. 
     - 300,000 game simulations are calculated like so (miscalculation from previous 140,000, 160,000 and 200,000 supposed games for game modes):
       - 1 scenario * 10000 games * 4 players = 40,000 games;
       - 3 scenarios * 5000 games * 4 players = 60,000 games;
       - 1 scenario * 10000 games * 4 (four 3-player parties) = 40,000 games;
       - 3 scenarios * 5000 games * 4 (four 3-player parties) = 60,000 games;
       - 1 scenario * 10000 games * 4 (four 6-player parties) = 40,000 games;
       - 3 scenarios * 5000 games * 4 (four 6-player parties) = 60,000 games;
     - 100,000 game simulations are calculated like so (miscalculation from previous 20,000 supposed games for game modes):
       - 1 scenario * 10000 games * 4 players = 40,000 games;
       - 3 scenarios * 5000 games * 4 players = 60,000 games;
     - 

1. Team Deathmatch (TDM):
   - Players per team: 6
   - Teams: 2
   - Win condition: First team to reach 50 kills or highest kills when time expires.
   - This game mode is meant to be a simulation of Call of Duty's Team Deathmatch game mode.
   - Simulation:
     - 300,000 games simulated;
     - Reference parties include 3-player and 6-player parties.
     - GamePlayer attributes ignored for this mode:
       * contesting_kills - no objective to contest.
       * objective_time - no objective to be on.
       * character_class - no separate classes for this mode.
       * domination_points - no objectives, so no domination points for this mode. This is also not domination mode.
       * rounds_won - Tehcnically 1 round in this game mode, but that is the same as having no rounds and just a single game.
       * rounds_lost - same as rounds_won.

2. Free-for-All (FFA):
   - Players per match: 12 (solo players)
   - Win condition: First player to reach 50 kills or highest kills when time expires.
   - This game mode is meant to be a simulation of Call of Duty's deathmatch game mode but, where everyone is against each other instead of in a team.
   - Simulation:
     - 100,000 games simulated;
     - Only individual reference players.
     - GamePlayer attributes ignored for this mode:
       * party_name - in real life you can be in a party and play against each other, but we don't do this in this simulation.
       * assists - no assists in a solo game mode.
       * assists_per_minute - no assists in a solo game mode.
       * avg_assists_delta - no assists in a solo game mode.
       * Rest of them are the same as TDM game mode.

3. Domination:
   - Players per team: 6
   - Teams: 2
   - Win condition: Teams gain points (e.g., 1 point per 5 seconds per controlled zone), first to 200 points wins.
   - This game mode is meant to be a simulation of Call of Duty's game mode, where there are 3 points to constantly capture - A, B and C.
   - Simulation:
     - 300,000 games simulated;
     - Reference parties include 3-player and 6-player parties.
     - GamePlayer attributes ignored for this mode:
       * character_class - no separate classes for this mode.
       * rounds_won - Tehcnically 1 round in this game mode, but that is the same as having no rounds and just a single game.
       * rounds_lost - same as rounds_won.

4. Battle Royale 1v99 (BR_1V99):
   - Players per match: 100 (solo players)
   - Win condition: Last player standing.
   - This game mode is meant to be a simulation of Fortnite in solos.
   - Simulation:
     - 100,000 games simulated;
     - Only individual reference players.
     - Physically impossible to get over 99 kills, but it is also very unlikely to get over 30 as well.
     - GamePlayer attributes ignored for this mode:
       * party_name - you can't be in a party in a solo battle royale.
       * is_tie - there are no ties in this game mode.
       * assists - no assists in a solo game mode.
       * assists_per_minute - no assists in a solo game mode.
       * avg_assists_delta - no assists in a solo game mode.
       * Rest of them are the same as TDM game mode.

5. Battle Royale 4v96 (BR_4V96):
   - Players per team: 4
   - Teams: 25
   - Win condition: Last team standing.
   - This game mode is meant to be a simulation of Fortnite in squads of 4 players.
   - Physically impossible to get over 96 kills, but it is also very unlikely to get over 40 as well for the whole team.
   - Simulation:
     - 300,000 games simulated;
     - Reference parties include 2-player and 4-player parties.
     - GamePlayer attributes ignored for this mode:
       * Same as BR_1V99 game mode, but you can be in a party, so party_name is not ignored.

7. Search and Destroy (SAD):
   - Players per team: 5
   - Teams: 2
   - Win condition: First team to win 16 rounds (there is no time limit technically);
   - This game mode is meant to be a simulation of Counter-strike: Global offensive or Counter-strike 2.
   - Time for this game mode each round is 2 minutes and then another 40 seconds added, if the bomb gets planted,
     but a game can end quicker by killing the enemy team before a bomb is planted or by defusing the bomb, if it is planted.
     This game mode might need the time parameters adjusted maybe, because right now it has the average whole game time, not each round time.
   - Only one team plants the bomb. For them, they win a round, if they kill the enemy team.
   - The team that has to defuse the bomb can either kill the enemy team before they plant the bomb or by defusing the bomb.
   - Physically impossible to get over 5 * 30 kills, but it is also very unlikely to get more than 1-3 constantly every single round.
   - Simulation:
     - 300,000 games simulated;
     - Reference parties include 2-player and 5-player parties.
     - Adjustments include round-based win/loss modifications.

===============================================
Database Models (Based on models.py)
===============================================

1. Player:
   - id: Unique identifier for the player.
   - created_at: Timestamp when the player record was created.
   - name: Player’s unique name.
   - party_name: Name of the party the player is in (this is not the same as a team in game,
                 it is like a friend group played together, so they join a party together).
   - Relationships:
       * game_players: List of GamePlayer records (per-game stats) for the player.
       * game_type_stats: Aggregated stats for each game mode for the player.

2. Game:
   - id: Unique game ID.
   - created_at: Timestamp when the game started.
   - type: The game mode (TDM, FFA, Domination, BR_1V99, BR_4V96 or SAD).
   - playtime: Duration of the game (in seconds).
   - team_count: Number of teams in the game.
   - team_size: Number of players per team.
   - kill_cap: Maximum number of kills for TDM and FFA.
   - point_limit: Point limit for Domination game mode.
   - winning_round_limit: Rounds needed to win in SAD game mode.
   - player_count: Total number of players in the game (team_count * team_size).
   - Relationships:
       * game_players: List of GamePlayer records associated with the game.

3. GamePlayer:
   - game_id: Foreign key to the Game.
   - player_id: Foreign key to the Player.
   - id: Unique identifier for the game player record.
   - created_at: Timestamp when the game player record was created.
   - team: The team to which the player belonged in that game (if solo, he will be alone in a team).
   - party_name: The party name (no longer unique) assigned to the player indicating, with which players this player played during the game.
   - team_placement: The player's (if a solo team) or team's placement in the game (this is not a rank, this is just the placement based on the game mode's win condition).
   - is_tie: Boolean indicating if the game was a tie (that means, if 2 teams in the game have the same placement, they are tied).
             In FFA specifically, a tie is only considered, if a player placed 1st with another player. Any other placement means you lose.
   - true_rating_before_game: The player's rating before the game. Taken from player_game_type_stats table.
   - true_rating_after_game: The player's rating after the game. Based on the scenario needed to be fullfilled for reference players,
                             the stats of the GamePlayer should be configured, so that the rating goes the way the scenario needs it.
                             For the rest of the players, this should be also based on their performance from all metrics,
                             but considering the edge cases and limitations with their each atrribute + with other players, + with their overall stats from player_game_type_stats.
   - is_most_valuable_player / is_least_valuable_player: Flags indicating MVP/least valuable status based on how much they contributed for the win conditions,
                                                         which not only include the core attributes, but also supporting ones like damage and kills, etc.
   - Kills, deaths, assists: Combat statistics for the game.
   - longest_time_alive: The longest duration the player stayed alive until death.
   - headshot_damage_dealt, torso_and_arm_damage_dealt, leg_damage_dealt: Damage breakdown.
   - damage_taken: Total damage received.
   - contesting_kills: Kills done near objectives or in them.
   - objective_time: Time spent in/on any objective.
   - domination_points: Points earned in domination by keeping an objective as captured by your team (doesn't mean objective time,
                        because in Call of Duty you can just leave it be or protect it near the objective).
   - accuracy, headshot_accuracy, torso_accuracy, leg_accuracy: Accuracy metrics.
   - damage_missed: Total damage missed.
   - avg_damage_missed_delta: Change in average damage missed compared to overall average damage missed from player_game_type_stats.
   - kills_per_minute, deaths_per_minute, assists_per_minute, damage_dealt_per_minute, damage_taken_per_minute: Per-minute metrics.
   - damage_dealt_and_taken_ratio: Ratio of damage dealt to damage taken.
   - kill_death_ratio: Ratio of kills to deaths.
   - avg_damage_dealt_delta, avg_damage_taken_delta, avg_kills_delta, avg_deaths_delta, avg_assists_delta: Changes in averages compared to overall averages from player_game_type_stats
   - best_killstreak: Highest kill streak in the game.
   - rounds_won, rounds_lost: Round results for modes like SAD.
   - Relationships:
       * game: The parent Game record.
       * player: The parent Player record.

4. PlayerGameTypeStats:
   - player_id: Foreign key to the Player.
   - id: Unique identifier for the aggregated stats record.
   - created_at: Timestamp when the stats record was created.
   - game_type: The game mode these stats pertain to.
   - true_rating: The current overall true rating for the player in that game mode.
   - total_headshot_damage, total_torso_and_arm_damage, total_leg_damage: Aggregated damage stats.
   - total_kills, total_deaths, total_assists: Aggregated combat stats.
   - total_damage_taken, total_damage_dealt, total_damage_missed: Aggregated damage metrics.
   - win_streak: Current win streak. Resets after a loss or tie, if ties are applicable.
   - total_games_played: Number of games played in that mode.
   - last_time_played: Last timestamp the player participated in this mode.
   - avg_damage_dealt, avg_damage_taken, avg_damage_missed: Average damage metrics per game.
   - total_accuracy, headshot_accuracy, torso_accuracy, leg_accuracy: Overall accuracy metrics.
   - avg_kills, avg_deaths, avg_assists: Average combat stats per game.
   - total_kill_death_ratio: Overall kill/death ratio.
   - total_wins, total_loses, total_ties: Aggregated win/loss/tie counts.
   - best_killstreak: Highest kill streak achieved across games.
   - win_loss_ratio: Overall win/loss ratio.
   - Relationships:
       * player: The associated Player record.

===============================================
Additional Simulation Information:
===============================================
- The simulation targets a maximum of 40,000 players and 1,400,000 games in total.
- There are 40 reference players with fresh ranks; the remaining players start with random ranks and stats distributed close to the rank_weights from data_simulation.py.
- For each game mode, the simulation models different gameplay dynamics, such as:
   * Linear rank increase or decrease over time.
   * Constant rank after a period.
   * Pauses in play (to create skill gaps).
   * Abrupt falls and subsequent jumps (to simulate smurfing).
- The simulation also considers playing solo and in a party and varying team sizes per game mode.
- The rank distribution and dynamic adjustments are designed to mimic realistic scenarios found in games like Call of Duty, Counter-strike: Global offensive, Counter-strike 2, Fortnite.

===============================================
End of Simulation Information
===============================================
"""
