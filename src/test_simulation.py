# RPM-EE Test Script
# Runs simulation and displays summary statistics

from simulation import RPMEESimulation
import json

def main():
    print("Starting RPM-EE Simulation Test...")
    print("=" * 60)
    
    sim = RPMEESimulation()
    sim.run(episodes=100)
    
    print("\n" + "=" * 60)
    print("SIMULATION SUMMARY")
    print("=" * 60)
    
    # Analyze logs
    total_events = sum(log["num_events"] for log in sim.logs)
    total_matched = sum(log["num_matched"] for log in sim.logs)
    total_simulations = sum(log["num_simulations"] for log in sim.logs)
    
    # Count actions
    action_counts = {}
    success_counts = {"success": 0, "failure": 0}
    for log in sim.logs:
        action = log.get("action", "none")
        action_counts[action] = action_counts.get(action, 0) + 1
        if log.get("action_success"):
            success_counts["success"] += 1
        else:
            success_counts["failure"] += 1
    
    # Mode distribution
    mode_counts = {}
    for log in sim.logs:
        mode = log.get("replay_mode", "unknown")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    print(f"\nTotal Episodes: {len(sim.logs)}")
    print(f"Total Events Generated: {total_events}")
    print(f"Total Matched Events: {total_matched}")
    print(f"Total Simulations: {total_simulations}")
    print(f"Match Rate: {total_matched/max(total_events, 1)*100:.1f}%")
    
    print(f"\nAction Distribution:")
    for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action}: {count} ({count/len(sim.logs)*100:.1f}%)")
    
    print(f"\nAction Success Rate:")
    total_actions = success_counts["success"] + success_counts["failure"]
    print(f"  Successes: {success_counts['success']} ({success_counts['success']/max(total_actions,1)*100:.1f}%)")
    print(f"  Failures: {success_counts['failure']} ({success_counts['failure']/max(total_actions,1)*100:.1f}%)")
    
    print(f"\nReplay Mode Distribution:")
    for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {mode}: {count} ({count/len(sim.logs)*100:.1f}%)")
    
    # Final system state
    print(f"\nFinal System State:")
    print(f"  Stress: {sim.system_state['stress']:.3f}")
    print(f"  Prediction Error: {sim.system_state['prediction_error']:.3f}")
    print(f"  Emotion Volatility: {sim.system_state['emotion_volatility']:.3f}")
    
    # Sample logs
    print(f"\nSample Log Entries (first 5):")
    for log in sim.logs[:5]:
        print(f"  Clock {log['clock']}: {log['state']} | "
              f"Events:{log['num_events']} Matched:{log['num_matched']} Sims:{log['num_simulations']} | "
              f"Mode:{log['replay_mode']} Action:{log['action']} Success:{log['action_success']}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
