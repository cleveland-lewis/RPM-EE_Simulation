# RPM-EE v1.1.0 Main Simulation Entry Point

from src.simulation import RPMEESimulation


def main():
    sim = RPMEESimulation()
    sim.run(episodes=1000)


if __name__ == "__main__":
    main()
