"""
Main entry point for Steel Production Multi-Agent System
Step 4: Complete simulation loop with agent-twin coordination
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add paths
sys.path.append(os.path.dirname(__file__))

from agents.bf_agent import BF_Agent
from agents.bof_agent import BOF_Agent
from agents.coke_oven_agent import CokeOven_Agent
from agents.gas_holder_agent import GasHolder_Agent
from env.mas_sim_env import MAS_SimEnv
from protocols.gas_request import MessageBus


def run_mas_simulation(num_steps: int = 100, visualize: bool = True):
    """
    Run Multi-Agent System simulation - REFACTORED ARCHITECTURE
    
    Args:
        num_steps: Number of simulation steps
        visualize: Whether to plot results
    """
    print("=" * 70)
    print("Steel Production Multi-Agent System Simulation - REFACTORED")
    print("=" * 70)
    
    # ===== INITIALIZE ENVIRONMENT (owns MessageBus) =====
    env = MAS_SimEnv(use_twins=True)
    
    # ===== REMOVED: message_bus = MessageBus() =====
    # Env now owns the single MessageBus instance!
    
    # ===== INITIALIZE AGENTS =====
    # Agents can optionally receive env reference for MessageBus access
    bf_agent = BF_Agent("BF1")
    bof_agent = BOF_Agent("BOF1")
    co_agent = CokeOven_Agent("CO1")
    gh_agent = GasHolder_Agent("GH1")
    
    print(f"\nInitialized 4 agents:")
    print(f"  - {bf_agent.agent_id}: Blast Furnace Agent")
    print(f"  - {bof_agent.agent_id}: BOF Agent")
    print(f"  - {co_agent.agent_id}: Coke Oven Agent")
    print(f"  - {gh_agent.agent_id}: Gas Holder Agent")
    
    print(f"\nArchitecture:")
    print(f"  - Unified MessageBus ID: {id(env.get_message_bus())}")
    print(f"  - Translator: {env.translator.__class__.__name__}")
    print(f"  - GasNetwork: {env.gas_network.__class__.__name__}")

    
    # Storage for history
    history = {
        "time": [],
        "soc_bfg": [],
        "soc_bofg": [],
        "soc_cog": [],
        "p_bfg": [],
        "Si": [],
        "wind_volume": [],
        "bfg_to_pp": [],
        "bfg_to_heating": [],
    }
    
    # Reset environment
    obs = env.reset()
    
    print(f"\nRunning simulation for {num_steps} steps...")
    print("-" * 70)
    
    # Simulation loop
    for step in range(num_steps):
        # ===== CLEAR MESSAGES via Env's MessageBus =====
        env.get_message_bus().clear()
        
        # ===== AGENTS DECIDE =====
        # Agents can access message_bus from env if needed for communication
        bf_action = bf_agent.step(obs)
        bof_action = bof_agent.step(obs)
        co_action = co_agent.step(obs)
        gh_action = gh_agent.step(obs)
        
        # Combine actions
        actions = {
            "BF": bf_action,
            "BOF": bof_action,
            "CokeOven": co_action,
            "GasHolder": gh_action
        }
        
        # Environment step
        obs = env.step(actions)
        
        # Record history
        history["time"].append(env.time)
        history["soc_bfg"].append(obs["soc_bfg"])
        history["soc_bofg"].append(obs["soc_bofg"])
        history["soc_cog"].append(obs["soc_cog"])
        history["p_bfg"].append(obs["p_bfg"])
        history["Si"].append(obs["Si"])
        history["wind_volume"].append(bf_action["wind_volume"])
        history["bfg_to_pp"].append(gh_action["bfg_to_pp"])
        history["bfg_to_heating"].append(gh_action["bfg_to_heating"])
        
        # Print status every 20 steps
        if (step + 1) % 20 == 0 or step == 0:
            print(f"Step {step+1:3d}: "
                  f"SOC_BFG={obs['soc_bfg']:.3f}, "
                  f"P_BFG={obs['p_bfg']:.1f} kPa, "
                  f"Si={obs['Si']:.3f}%, "
                  f"Wind={bf_action['wind_volume']:.0f}")
    
    print("-" * 70)
    print(f"Simulation completed!")
    
    # Visualization
    if visualize:
        plot_results(history)
    
    return history


def plot_results(history):
    """Plot simulation results"""
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    fig.suptitle('Multi-Agent System Simulation Results', fontsize=16)
    
    time = history["time"]
    
    # 1. Gas Holder SOCs
    ax = axes[0, 0]
    ax.plot(time, history["soc_bfg"], label='BFG', linewidth=2)
    ax.plot(time, history["soc_bofg"], label='BOFG', linewidth=2)
    ax.plot(time, history["soc_cog"], label='COG', linewidth=2)
    ax.axhline(y=0.85, color='r', linestyle='--', alpha=0.5, label='High limit')
    ax.axhline(y=0.25, color='r', linestyle='--', alpha=0.5, label='Low limit')
    ax.set_ylabel('SOC []')
    ax.set_title('Gas Holder State of Charge')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # 2. BFG Pressure
    ax = axes[0, 1]
    ax.plot(time, history["p_bfg"], color='tab:blue', linewidth=2)
    ax.axhline(y=14, color='r', linestyle='--', alpha=0.5, label='High limit')
    ax.axhline(y=9, color='r', linestyle='--', alpha=0.5, label='Low limit')
    ax.set_ylabel('Pressure [kPa]')
    ax.set_title('BFG Pressure')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. BF Wind Volume
    ax = axes[1, 0]
    ax.plot(time, history["wind_volume"], color='tab:green', linewidth=2)
    ax.set_ylabel('Wind [Nm³/min]')
    ax.set_title('BF Wind Volume (Agent Action)')
    ax.grid(True, alpha=0.3)
    
    # 4. Si Content
    ax = axes[1, 1]
    ax.plot(time, history["Si"], color='tab:orange', linewidth=2)
    ax.axhline(y=0.45, color='b', linestyle='--', alpha=0.5, label='Target')
    ax.set_ylabel('Si [%]')
    ax.set_title('Silicon Content')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. BFG Distribution
    ax = axes[2, 0]
    ax.plot(time, history["bfg_to_pp"], label='To Power Plant', linewidth=2)
    ax.plot(time, history["bfg_to_heating"], label='To Heating', linewidth=2)
    ax.set_ylabel('Gas Flow [Nm³/h]')
    ax.set_xlabel('Time [min]')
    ax.set_title('BFG Distribution (Gas Holder Actions)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Total BFG Usage
    ax = axes[2, 1]
    total_usage = [pp + heat for pp, heat in zip(history["bfg_to_pp"], history["bfg_to_heating"])]
    ax.plot(time, total_usage, color='tab:purple', linewidth=2)
    ax.set_ylabel('Total Gas Flow [Nm³/h]')
    ax.set_xlabel('Time [min]')
    ax.set_title('Total BFG Consumption')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_path = 'mas_simulation_results.png'
    plt.savefig(output_path, dpi=150)
    print(f"\nResults plotted and saved to: {output_path}")
    plt.show()


def demonstrate_scenarios():
    """Demonstrate specific scenarios"""
    
    print("\n" + "=" * 70)
    print("Scenario Demonstration: Gas Holder Full → Agent Response")
    print("=" * 70)
    
    env = MAS_SimEnv(use_twins=False)
    bf_agent = BF_Agent("BF1")
    gh_agent = GasHolder_Agent("GH1")
    
    # Scenario: BFG holder is too full
    obs = env.reset()
    obs["soc_bfg"] = 0.90  # Force high SOC
    obs["p_bfg"] = 15.0    # Force high pressure
    
    print(f"\nInitial state:")
    print(f"  SOC_BFG = {obs['soc_bfg']:.2f} (Too full!)")
    print(f"  P_BFG = {obs['p_bfg']:.1f} kPa (Too high!)")
    
    print(f"\nAgent actions:")
    bf_action = bf_agent.step(obs)
    print(f"  BF Agent: Reduces wind_volume to {bf_action['wind_volume']:.0f} Nm³/min")
    
    gh_action = gh_agent.step(obs)
    print(f"  GH Agent: Increases bfg_to_pp to {gh_action['bfg_to_pp']:.0f} Nm³/h")
    print(f"  GH Agent: Increases bfg_to_heating to {gh_action['bfg_to_heating']:.0f} Nm³/h")
    
    print(f"\n→ System Response: Coordinately reduces production and increases consumption!")


if __name__ == "__main__":
    # Run main simulation
    history = run_mas_simulation(num_steps=100, visualize=True)
    
    # Demonstrate specific scenario
    demonstrate_scenarios()
    
    print("\n" + "="*70)
    print("Multi-Agent System Demo Complete!")
    print("="*70)
