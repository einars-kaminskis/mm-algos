from src.simulation.data_simulation import simulate_all_modes
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main() -> None:
    logger.info("Starting full data simulation…")
    simulate_all_modes()
    logger.info("Data simulation complete!")

if __name__ == "__main__":
    main()