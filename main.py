from src.config_loader import load_config, validate_config
from src.simulation import Simulation


def main():
    config = load_config(
        "data/simulation_config.json"
    )

    validate_config(config)

    simulation = Simulation(
        config=config
    )

    simulation.setup()
    simulation.run()


if __name__ == "__main__":
    main()