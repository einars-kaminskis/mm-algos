from src.simulation.data_simulation6 import simulate_all_modes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main6() -> None:
    logger.info("Starting full data simulation…")
    simulate_all_modes()
    logger.info("Data simulation complete!")

if __name__ == "__main__":
    main6()