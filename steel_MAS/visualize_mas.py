"""
Standalone MAS Visualization Script

Runs a 100-step MAS simulation and generates comprehensive visualizations:
1. Animated gas flow dynamics (MP4/GIF)
2. Agent action-response plots (PNG)

Usage:
    python visualize_mas.py --steps 50 --format gif
"""

import sys
import os
import argparse
import numpy as np

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)
sys.path.append(os.path.dirname(parent_dir))

from visualization import DataRecorder, visualize_simulation

# Import MAS components
from agents.bf_agent import BF_Agent
from agents.bof_agent import BOF_Agent
from agents.coke_oven_agent import CokeOven_Agent
from agents.gas_holder_agent import GasHolder_Agent

# Import twins
import importlib.util


def load_twins():
    """Load digital twin modules"""
    digital_twin_dir = os.path.join(os.path.dirname(parent_dir), "Digital_Twin")
    
    # Load BF Twin
    bf_path = os.path.join(digital_twin_dir, "Blast Furnace", "Blast_Furnace_Twin_to_share.py")
    spec = importlib.util.spec_from_file_location("BlastFurnaceTwin", bf_path)
    bf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bf_module)
    BlastFurnaceTwin = bf_module.BlastFurnaceTwin
    
    # Load BOF Twin
    bof_path = os.path.join(digital_twin_dir, "BOF", "BOF_Twin.py")
    spec = importlib.util.spec_from_file_location("BOFTwin", bof_path)
    bof_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bof_module)
    BOFTwin = bof_module.BOFTwin
    
    # Load Coke Oven Twin
    co_path = os.path.join(digital_twin_dir, "Coke Oven", "Coke_Oven_Twin.py")
    spec = importlib.util.spec_from_file_location("CokeOvenTwin", co_path)
    co_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(co_module)
    CokeOvenTwin = co_module.CokeOvenTwin
    
    return BlastFurnaceTwin, BOFTwin, CokeOvenTwin


class SimpleEnvironment:
    """Simplified environment for standalone visualization"""
    
    def __init__(self):
        self.state = {
            "SOC_bfg": 0.5,
            "SOC_bofg": 0.5,
            "SOC_cog": 0.5,
            "P_bfg": 12.0,
            "P_bofg": 12.0,
            "P_cog": 12.0,
            "bfg_supply": 0,
            "bofg_supply": 0,
            "cog_supply": 0,
            # Gas consumption by destination (for visualization)
            "bfg_to_power_plant": 0,
            "bfg_to_bf": 0,
            "cog_to_bf": 0,
            "bofg_to_power_plant": 0,
            "cog_to_heater": 0,
            "Si": 0.45,
            "T_hot_metal": 1500,
            "COG_available": 20000,
            "O2_available": 50000,
            "peak_electricity": False
        }
    
    def get_state(self):
        return self.state.copy()
    
    def step(self, twin_outputs):
        """Update environment state based on twin outputs"""
        # Update gas production
        if "BF" in twin_outputs:
            bf_out = twin_outputs["BF"]
            self.state["bfg_supply"] = bf_out.get("bf_gas_total_flow [m³/h]", 0)
            self.state["T_hot_metal"] = bf_out.get("T_hot_metal [°C]", 1500)
            self.state["Si"] = bf_out.get("Si [%]", 0.5)
        
        if "BOF" in twin_outputs:
            bof_out = twin_outputs["BOF"]
            self.state["bofg_supply"] = bof_out.get("bof_gas [Nm³/h]", 0)
        
        if "Coke" in twin_outputs:
            coke_out = twin_outputs["Coke"]
            self.state["cog_supply"] = coke_out.get("cog_production [Nm³/h]", 0)
        
        # Calculate gas consumption (simplified realistic distribution)
        # BFG: 50% to power plant, 30% internal use
        bfg_prod = self.state["bfg_supply"]
        self.state["bfg_to_power_plant"] = bfg_prod * 0.50
        self.state["bfg_to_bf"] = bfg_prod * 0.30
        
        # BOFG: mostly to power plant
        bofg_prod = self.state["bofg_supply"]
        self.state["bofg_to_power_plant"] = bofg_prod * 0.80
        
        # COG: split between BF and heater
        cog_prod = self.state["cog_supply"]
        self.state["cog_to_bf"] = cog_prod * 0.60
        self.state["cog_to_heater"] = cog_prod * 0.30
        
        # Gas holder dynamics (accumulation)
        dt = 1.0  # hour
        capacity_bfg = 400000  # m³ (realistic steel plant scale)
        capacity_bofg = 150000
        capacity_cog = 100000
        
        # BFG balance
        bfg_cons = self.state["bfg_to_power_plant"] + self.state["bfg_to_bf"]
        bfg_net = (bfg_prod - bfg_cons) * dt
        self.state["SOC_bfg"] = np.clip(self.state["SOC_bfg"] + bfg_net / capacity_bfg, 0, 1)
        
        # BOFG balance
        bofg_cons = self.state["bofg_to_power_plant"]
        bofg_net = (bofg_prod - bofg_cons) * dt
        self.state["SOC_bofg"] = np.clip(self.state["SOC_bofg"] + bofg_net / capacity_bofg, 0, 1)
        
        # COG balance
        cog_cons = self.state["cog_to_bf"] + self.state["cog_to_heater"]
        cog_net = (cog_prod - cog_cons) * dt
        self.state["SOC_cog"] = np.clip(self.state["SOC_cog"] + cog_net / capacity_cog, 0, 1)
        
        # Update pressures (proportional to SOC)
        self.state["P_bfg"] = 8 + 8 * self.state["SOC_bfg"]
        self.state["P_bofg"] = 8 + 8 * self.state["SOC_bofg"]
        self.state["P_cog"] = 8 + 8 * self.state["SOC_cog"]
        
        # Update gas availability
        self.state["COG_available"] = self.state["cog_supply"]


def run_simulation_with_visualization(num_steps=50, output_dir="output", format="mp4"):
    """
    Run MAS simulation and generate visualizations.
    
    Args:
        num_steps: Number of simulation steps
        output_dir: Output directory for visualizations
        format: Animation format ('mp4' or 'gif')
    """
    print("=" * 80)
    print("  MAS Simulation with Visualization")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Simulation steps: {num_steps}")
    print(f"  Output directory: {output_dir}")
    print(f"  Animation format: {format}")
    
    # Load twins
    print("\nLoading digital twins...")
    try:
        BlastFurnaceTwin, BOFTwin, CokeOvenTwin = load_twins()
        print("✅ Digital twins loaded")
    except Exception as e:
        print(f"❌ Failed to load twins: {e}")
        return
    
    # Initialize agents
    print("\nInitializing agents...")
    bf_agent = BF_Agent("BF1")
    bof_agent = BOF_Agent("BOF1")
    coke_agent = CokeOven_Agent("Coke1")
    gh_agent = GasHolder_Agent("GasHolder")
    
    # Initialize twins
    bf_twin = BlastFurnaceTwin()
    bof_twin = BOFTwin()
    coke_twin = CokeOvenTwin()
    
    # Initialize environment
    env = SimpleEnvironment()
    
    # Initialize data recorder
    recorder = DataRecorder()
    
    print(f"\n{'=' * 80}")
    print("  Running Simulation")
    print("=" * 80)
    
    # Run simulation
    for step in range(num_steps):
        if step % 10 == 0:
            print(f"Step {step}/{num_steps}...", end="\r")
        
        # Get current state
        env_state = env.get_state()
        
        # Agents observe and decide
        bf_state = bf_agent.step(env_state)
        bof_state = bof_agent.step(env_state)
        coke_state = coke_agent.step(env_state)
        
        # Prepare twin inputs
        bf_inputs = {
            "ore [t/h]": 50,
            "pellets [t/h]": 100,
            "sinter [t/h]": 100,
            "coke_mass_flow_bf4 [t/h]": bf_state["PCI"] / 1.5,
            "coke_gas_coke_plant_bf4 [m³/h]": max(min(env_state["COG_available"] * 0.3, 8000), 1000),  # Min 1000, max 8000
            "calorific_value_coke_gas_bf4 [MJ/m³]": 18.0,  # Realistic COG heating value
            "power [kWh/h]": 50000,
            "wind_volume [Nm³/min]": bf_state["wind_volume"],
            "oxygen_enrichment [Nm³/h]": 0,
            "intern BF_GAS_PERCENTAGE [%]": 50,
            "power plant BF_GAS_PERCENTAGE [%]": 20,
            "slab heat furnace BF_GAS_PERCENTAGE [%]": 20,
            "coke plant BF_GAS_PERCENTAGE [%]": 10
        }
        
        bof_inputs = {
            "pig_iron [t/h]": 80,
            "scrap_steel [t/h]": bof_state["scrap_steel"],
            "oxygen [Nm³/h]": bof_state["oxygen"],
            "lime [t/h]": 5,
            "power [kWh/h]": 5000
        }
        
        coke_inputs = {
            "coal_input [t/h]": 100,
            "heating_gas [Nm³/h]": coke_state["heating_gas_input"],
            "heating_gas_calorific_value [MJ/Nm³]": 4.5,
            "steam [t/h]": 2,
            "power [kWh/h]": 3000
        }
        
        # Run twins
        bf_output = bf_twin(bf_inputs)
        bof_output = bof_twin(bof_inputs)
        coke_output = coke_twin(coke_inputs)
        
        twin_outputs = {
            "BF": bf_output,
            "BOF": bof_output,
            "Coke": coke_output
        }
        
        # Update environment
        env.step(twin_outputs)
        
        # Record data
        agent_actions = {
            "BF": bf_state,
            "BOF": bof_state,
            "Coke": coke_state
        }
        
        recorder.record_step(step, env.get_state(), agent_actions, twin_outputs)
    
    print(f"\n✅ Simulation completed: {num_steps} steps")
    
    # Generate visualizations
    print(f"\n{'=' * 80}")
    print("  Generating Visualizations")
    print("=" * 80)
    
    visualize_simulation(recorder, output_dir)
    
    print(f"\n{'=' * 80}")
    print("  ✅ Visualization Complete")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  📊 Animation: {output_dir}/mas_flows.{format}")
    print(f"  📈 Response plot: {output_dir}/action_response.png")


def main():
    parser = argparse.ArgumentParser(
        description="Run MAS simulation and generate visualizations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of simulation steps (default: 50)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for visualizations"
    )
    
    parser.add_argument(
        "--format",
        choices=["mp4", "gif"],
        default="mp4",
        help="Animation format"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run simulation
    run_simulation_with_visualization(
        num_steps=args.steps,
        output_dir=args.output_dir,
        format=args.format
    )


if __name__ == "__main__":
    main()
