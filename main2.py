from src.simulation.data_simulation2 import simulate_all_modes
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main2() -> None:
    start_date = datetime.now(timezone.utc)
    logger.info("Starting full data simulation…")
    simulate_all_modes()
    logger.info("Data simulation complete!")
    end_date = datetime.now(timezone.utc)
    logger.info(f"Simulation ran for: {(end_date - start_date).total_seconds() / 60} minutes")

if __name__ == "__main__":
    main2()