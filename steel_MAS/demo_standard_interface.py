"""
Demonstration of Standard Interface System

Shows how to use the new StandardState/Action interfaces with:
1. State creation and manipulation
2. Action specification
3. Transition recording with rewards
4. Data export and analysis

This demo runs without full Twin integration for quick testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.standard_interfaces import (
    StandardState, StandardAction,
    GasHolderState, ProductionState, DemandState,
    GasAllocation, ProductionControl,
    create_default_state, create_default_action
)
from models.reward_calculation import calculate_reward, calculate_episode_metrics
from models.enhanced_recorder import EnhancedDataRecorder
import numpy as np


def demo_standard_interfaces():
    """Demonstrate basic usage of standard interfaces"""
    
    print("=" * 70)
    print("Demo 1: Creating and Using StandardState")
    print("=" * 70)
    
    # Create state using helper function
    state = create_default_state(time=0)
    
    print(f"\nDefault State at t=0:")
    print(f"  Gas Holder SOC: BFG={state.gas_holder.soc_bfg:.2f}, " 
          f"BOFG={state.gas_holder.soc_bofg:.2f}, COG={state.gas_holder.soc_cog:.2f}")
    print(f"  Production: BFG Supply={state.production.bf_bfg_supply:.0f} Nm³/h")
    print(f"  Demand: PowerPlant={state.demand.power_plant_demand:.0f} Nm³/h")
    
    # Convert to dict for logging
    state_dict = state.to_dict()
    print(f"\nState as dict has {len(state_dict)} top-level keys: {list(state_dict.keys())}")
    
    print("\n" + "=" * 70)
    print("Demo 2: Creating and Using StandardAction")
    print("=" * 70)
    
    # Create action
    action = create_default_action()
    
    print(f"\nDefault Action:")
    print(f"  Gas Allocation:")
    print(f"    BFG to PowerPlant: {action.gas_allocation.bfg_to_power_plant:.0f} Nm³/h")
    print(f"    BFG to Heating: {action.gas_allocation.bfg_to_heating:.0f} Nm³/h")
    print(f"  Production Control:")
    print(f"    BF Wind Volume: {action.production_control.bf_wind_volume:.0f} Nm³/min")
    print(f"    BF PCI: {action.production_control.bf_pci:.1f} kg/tHM")
    
    print("\n" + "=" * 70)
    print("Demo 3: Simulating State Transitions with Rewards")
    print("=" * 70)
    
    # Simulate a few state transitions
    recorder = EnhancedDataRecorder()
    
    current_state = create_default_state(time=0)
    
    print(f"\nSimulating 10 transitions...")
    
    for step in range(10):
        # Create action (simplified - just perturb defaults)
        action = create_default_action()
        
        # Add some variation to actions
        action.production_control.bf_wind_volume = 4000 + np.random.normal(0, 100)
        action.production_control.bf_pci = 150 + np.random.normal(0, 10)
        
        # Simulate next state (simplified physics)
        next_state = simulate_next_state(current_state, action, step + 1)
        
        # Calculate reward
        reward = calculate_reward(current_state, action, next_state)
        
        # Record transition
        recorder.record_transition(
            state=current_state,
            action=action,
            next_state=next_state,
            reward=reward,
            done=(step == 9)
        )
        
        if step < 3 or step >= 7:  # Print first 3 and last 3
            print(f"\n  Step {step}:")
            print(f"    SOC_BFG: {current_state.gas_holder.soc_bfg:.3f} -> {next_state.gas_holder.soc_bfg:.3f}")
            print(f"    Reward: {reward.total:.3f} (Prod={reward.production_score:.2f}, "
                  f"Stab={reward.stability_score:.2f}, Eff={reward.efficiency_score:.2f})")
        elif step == 3:
            print(f"\n  ... (steps 3-6 omitted for brevity)")
        
        current_state = next_state
    
    print("\n" + "=" * 70)
    print("Demo 4: Episode Metrics and Data Export")
    print("=" * 70)
    
    # Get episode metrics
    print(f"\n{recorder.get_summary()}")
    
    # Export transitions
    output_file = "output/demo_transitions.json"
    os.makedirs("output", exist_ok=True)
    recorder.export_transitions(output_file)
    
    print("\n" + "=" * 70)
    print("Demo 5: Analyzing Reward Components")
    print("=" * 70)
    
    # Analyze reward components
    rewards = recorder.get_reward_history()
    
    production_scores = [r.production_score for r in rewards]
    stability_scores = [r.stability_score for r in rewards]
    efficiency_scores = [r.efficiency_score for r in rewards]
    
    print(f"\nReward Component Analysis:")
    print(f"  Production: Mean={np.mean(production_scores):.3f}, Std={np.std(production_scores):.3f}")
    print(f"  Stability:  Mean={np.mean(stability_scores):.3f}, Std={np.std(stability_scores):.3f}")
    print(f"  Efficiency: Mean={np.mean(efficiency_scores):.3f}, Std={np.std(efficiency_scores):.3f}")
    
    print("\n" + "=" * 70)
    print("[OK] All demos completed successfully!")
    print("=" * 70)


def simulate_next_state(
    current_state: StandardState,
    action: StandardAction,
    next_time: int
) -> StandardState:
    """
    Simple physics simulation for demo (not using real Twins).
    
    In real system, this would be replaced by Twin execution.
    """
    # Extract current values
    soc_bfg = current_state.gas_holder.soc_bfg
    soc_bofg = current_state.gas_holder.soc_bofg
    soc_cog = current_state.gas_holder.soc_cog
    
    # Simplified production (depends on wind)
    wind = action.production_control.bf_wind_volume
    bf_bfg_supply = 0.4 * wind * 60 + 20000  # Same formula as real Twin
    
    # Simplified consumption
    total_consumption = (
        action.gas_allocation.bfg_to_power_plant +
        action.gas_allocation.bfg_to_heating
    )
    
    # Update SOC (simplified dynamics)
    # delta_soc = (supply - consumption) / capacity
    BFG_CAPACITY = 400000  # Nm³
    delta_soc_bfg = (bf_bfg_supply - total_consumption) / BFG_CAPACITY
    new_soc_bfg = np.clip(soc_bfg + delta_soc_bfg * 0.01, 0, 1)  # Scale down
    
    # Other SOCs have slower dynamics
    new_soc_bofg = np.clip(soc_bofg + np.random.normal(0, 0.01), 0, 1)
    new_soc_cog = np.clip(soc_cog + np.random.normal(0, 0.01), 0, 1)
    
    # Create next state
    return StandardState(
        time=next_time,
        gas_holder=GasHolderState(
            soc_bfg=new_soc_bfg,
            soc_bofg=new_soc_bofg,
            soc_cog=new_soc_cog,
            p_bfg=12.0 + (new_soc_bfg - 0.5) * 4,  # Pressure correlates with SOC
            p_bofg=12.0,
            p_cog=12.0
        ),
        production=ProductionState(
            bf_bfg_supply=bf_bfg_supply,
            bf_t_hot_metal=1500.0,
            bf_si_content=0.45,
            bof_bofg_supply=10000,
            coke_cog_supply=20000
        ),
        demand=DemandState(
            power_plant_demand=50000,
            heating_demand=20000,
            priority_level=0.5
        )
    )


if __name__ == "__main__":
    demo_standard_interfaces()
