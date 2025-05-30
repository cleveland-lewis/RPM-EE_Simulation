from src.simulation import run_simulation

logs = run_simulation(total_ticks=2)  # or use the default
print(logs[0])  # Print the first log packet