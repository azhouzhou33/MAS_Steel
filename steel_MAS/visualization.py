"""
MAS Visualization Module

Provides visualization capabilities for Multi-Agent Steel production system:
1. Animated data flows (gas production, consumption, SOC, pressure)
2. Agent-twin response plots showing action → response correlations
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from typing import Dict, List, Optional, Any
import os


class DataRecorder:
    """
    Records MAS simulation data for visualization and analysis.
    
    Captures time-series data for:
    - Gas production and consumption
    - Gas holder states (SOC, pressure)
    - Agent actions
    - Twin outputs
    """
    
    def __init__(self):
        self.timesteps: List[int] = []
        
        # Gas flows
        self.gas_production: Dict[str, List[float]] = {
            "BFG": [],
            "BOFG": [],
            "COG": []
        }
        
        self.gas_consumption: Dict[str, List[float]] = {
            "BFG_to_PowerPlant": [],
            "BFG_to_BF": [],
            "COG_to_BF": [],
            "BOFG_to_PowerPlant": [],
            "COG_to_Heater": []
        }
        
        # Gas holder states
        self.gas_holder_soc: Dict[str, List[float]] = {
            "BFG": [],
            "BOFG": [],
            "COG": []
        }
        
        self.gas_holder_pressure: Dict[str, List[float]] = {
            "BFG": [],
            "BOFG": [],
            "COG": []
        }
        
        # Agent actions
        self.agent_actions: Dict[str, List[float]] = {
            "wind_volume": [],
            "O2_enrichment": [],
            "PCI": [],
            "BOF_oxygen": [],
            "COG_heating": []
        }
        
        # Twin outputs
        self.twin_outputs: Dict[str, List[float]] = {
            "bfg_supply": [],
            "T_hot_metal": [],
            "Si": [],
            "pig_iron": [],
            "liquid_steel": []
        }
    
    def record_step(
        self, 
        step: int, 
        env_state: Dict[str, Any],
        agent_actions: Dict[str, Dict[str, float]],
        twin_outputs: Dict[str, Dict[str, float]]
    ):
        """
        Record one simulation timestep.
        
        Args:
            step: Current timestep number
            env_state: Environment state dictionary
            agent_actions: Dict of agent_name -> action_dict
            twin_outputs: Dict of twin_name -> output_dict
        """
        self.timesteps.append(step)
        
        # Record gas production
        self.gas_production["BFG"].append(env_state.get("bfg_supply", 0))
        self.gas_production["BOFG"].append(env_state.get("bofg_supply", 0))
        self.gas_production["COG"].append(env_state.get("cog_supply", 0))
        
        # Record gas consumption
        self.gas_consumption["BFG_to_PowerPlant"].append(
            env_state.get("bfg_to_power_plant", 0)
        )
        self.gas_consumption["BFG_to_BF"].append(
            env_state.get("bfg_to_bf", 0)
        )
        self.gas_consumption["COG_to_BF"].append(
            env_state.get("cog_to_bf", 0)
        )
        self.gas_consumption["BOFG_to_PowerPlant"].append(
            env_state.get("bofg_to_power_plant", 0)
        )
        self.gas_consumption["COG_to_Heater"].append(
            env_state.get("cog_to_heater", 0)
        )
        
        # Record gas holder states
        self.gas_holder_soc["BFG"].append(env_state.get("SOC_bfg", 0.5))
        self.gas_holder_soc["BOFG"].append(env_state.get("SOC_bofg", 0.5))
        self.gas_holder_soc["COG"].append(env_state.get("SOC_cog", 0.5))
        
        self.gas_holder_pressure["BFG"].append(env_state.get("P_bfg", 12.0))
        self.gas_holder_pressure["BOFG"].append(env_state.get("P_bofg", 12.0))
        self.gas_holder_pressure["COG"].append(env_state.get("P_cog", 12.0))
        
        # Record agent actions
        bf_actions = agent_actions.get("BF", {})
        self.agent_actions["wind_volume"].append(bf_actions.get("wind_volume", 4000))
        self.agent_actions["O2_enrichment"].append(bf_actions.get("O2_enrichment", 3.5))
        self.agent_actions["PCI"].append(bf_actions.get("PCI", 150))
        
        bof_actions = agent_actions.get("BOF", {})
        self.agent_actions["BOF_oxygen"].append(bof_actions.get("oxygen", 45000))
        
        coke_actions = agent_actions.get("Coke", {})
        self.agent_actions["COG_heating"].append(coke_actions.get("heating_gas_input", 15000))
        
        # Record twin outputs
        bf_output = twin_outputs.get("BF", {})
        self.twin_outputs["bfg_supply"].append(bf_output.get("bf_gas_total_flow", 0))
        self.twin_outputs["T_hot_metal"].append(bf_output.get("T_hot_metal", 1500))
        self.twin_outputs["Si"].append(bf_output.get("Si", 0.5))
        self.twin_outputs["pig_iron"].append(bf_output.get("pig_iron_steelworks", 0))
        
        bof_output = twin_outputs.get("BOF", {})
        self.twin_outputs["liquid_steel"].append(bof_output.get("liquid_steel", 0))
    
    def get_data_summary(self) -> str:
        """Return summary statistics of recorded data"""
        summary = f"DataRecorder Summary:\n"
        summary += f"  Timesteps recorded: {len(self.timesteps)}\n"
        summary += f"  Time range: {self.timesteps[0] if self.timesteps else 0} to {self.timesteps[-1] if self.timesteps else 0}\n"
        
        if self.gas_production["BFG"]:
            summary += f"  BFG production: {np.mean(self.gas_production['BFG']):.0f} ± {np.std(self.gas_production['BFG']):.0f} m³/h\n"
        if self.gas_holder_soc["BFG"]:
            summary += f"  BFG SOC: {np.mean(self.gas_holder_soc['BFG']):.2f} ± {np.std(self.gas_holder_soc['BFG']):.2f}\n"
        
        return summary


class AnimatedFlowVisualizer:
    """
    Creates animated visualizations of gas network dynamics.
    
    Generates multi-panel animations showing:
    - Gas production over time
    - Gas consumption by destination
    - Gas holder SOC
    - Gas holder pressure
    """
    
    def __init__(self):
        self.colors = {
            "BFG": "#1f77b4",  # Blue
            "BOFG": "#2ca02c",  # Green
            "COG": "#ff7f0e"   # Orange
        }
    
    def create_animation(
        self, 
        data_recorder: DataRecorder, 
        output_file: str = "mas_animation.mp4",
        fps: int = 5,  # Reduced from 10 to 5 for slower, clearer viewing
        dpi: int = 100
    ):
        """
        Create animated visualization of MAS dynamics.
        
        Args:
            data_recorder: DataRecorder with simulation history
            output_file: Output filename (.mp4 or .gif)
            fps: Frames per second
            dpi: Resolution
        """
        if len(data_recorder.timesteps) == 0:
            raise ValueError("No data recorded - cannot create animation")
        
        # Create figure with 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('MAS Gas Network Dynamics', fontsize=16, fontweight='bold')
        
        ax_production = axes[0, 0]
        ax_consumption = axes[0, 1]
        ax_soc = axes[1, 0]
        ax_pressure = axes[1, 1]
        
        # Initialize plots
        self._setup_production_plot(ax_production)
        self._setup_consumption_plot(ax_consumption)
        self._setup_soc_plot(ax_soc)
        self._setup_pressure_plot(ax_pressure)
        
        # Animation update function
        def animate(frame):
            # Clear all axes
            ax_production.clear()
            ax_consumption.clear()
            ax_soc.clear()
            ax_pressure.clear()
            
            # Get data up to current frame
            t = data_recorder.timesteps[:frame+1]
            
            # Panel 1: Gas Production
            self._update_production_plot(ax_production, data_recorder, frame)
            
            # Panel 2: Gas Consumption
            self._update_consumption_plot(ax_consumption, data_recorder, frame)
            
            # Panel 3: SOC
            self._update_soc_plot(ax_soc, data_recorder, frame)
            
            # Panel 4: Pressure
            self._update_pressure_plot(ax_pressure, data_recorder, frame)
            
            return ax_production, ax_consumption, ax_soc, ax_pressure
        
        # Create animation
        num_frames = len(data_recorder.timesteps)
        anim = FuncAnimation(
            fig, 
            animate, 
            frames=num_frames,
            interval=1000//fps,  # ms per frame
            blit=False,
            repeat=True
        )
        
        # Save animation
        print(f"Generating animation with {num_frames} frames...")
        
        if output_file.endswith('.mp4'):
            try:
                writer = FFMpegWriter(fps=fps, bitrate=1800)
                anim.save(output_file, writer=writer, dpi=dpi)
                print(f"✅ Animation saved to {output_file}")
            except Exception as e:
                print(f"⚠️  FFmpeg not available: {e}")
                print("Falling back to GIF format...")
                gif_file = output_file.replace('.mp4', '.gif')
                writer = PillowWriter(fps=fps)
                anim.save(gif_file, writer=writer, dpi=dpi)
                print(f"✅ Animation saved to {gif_file}")
        elif output_file.endswith('.gif'):
            writer = PillowWriter(fps=fps)
            anim.save(output_file, writer=writer, dpi=dpi)
            print(f"✅ Animation saved to {output_file}")
        else:
            raise ValueError("Output file must be .mp4 or .gif")
        
        plt.close(fig)
    
    def _setup_production_plot(self, ax):
        """Setup gas production subplot"""
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Production (m³/h)')
        ax.set_title('Gas Production')
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _update_production_plot(self, ax, recorder: DataRecorder, frame: int):
        """Update gas production plot"""
        t = recorder.timesteps[:frame+1]
        
        for gas_type in ["BFG", "BOFG", "COG"]:
            data = recorder.gas_production[gas_type][:frame+1]
            ax.plot(t, data, label=gas_type, color=self.colors[gas_type], linewidth=2)
            
            # Show current value
            if data:
                ax.text(
                    0.98, 0.95 - 0.05 * list(self.colors.keys()).index(gas_type),
                    f"{gas_type}: {data[-1]:.0f}",
                    transform=ax.transAxes,
                    ha='right',
                    va='top',
                    fontsize=10,
                    bbox=dict(boxstyle='round', facecolor=self.colors[gas_type], alpha=0.3)
                )
        
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Production (m³/h)')
        ax.set_title('Gas Production')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
    
    def _setup_consumption_plot(self, ax):
        """Setup gas consumption subplot"""
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Consumption (m³/h)')
        ax.set_title('Gas Consumption by Destination')
        ax.grid(True, alpha=0.3)
    
    def _update_consumption_plot(self, ax, recorder: DataRecorder, frame: int):
        """Update gas consumption plot"""
        t = recorder.timesteps[:frame+1]
        
        # Stacked area plot
        consumption_data = []
        labels = []
        
        for key in recorder.gas_consumption.keys():
            data = recorder.gas_consumption[key][:frame+1]
            if data and np.sum(data) > 0:  # Only show if there's consumption
                consumption_data.append(data)
                labels.append(key.replace("_", " "))
        
        if consumption_data:
            ax.stackplot(t, *consumption_data, labels=labels, alpha=0.7)
        
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Consumption (m³/h)')
        ax.set_title('Gas Consumption by Destination')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=8)
    
    def _setup_soc_plot(self, ax):
        """Setup SOC subplot"""
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('SOC (%)')
        ax.set_title('Gas Holder State of Charge')
        ax.grid(True, alpha=0.3)
    
    def _update_soc_plot(self, ax, recorder: DataRecorder, frame: int):
        """Update SOC plot"""
        t = recorder.timesteps[:frame+1]
        
        # Safety zone (25% - 85%)
        if t:
            ax.axhspan(0.25, 0.85, color='green', alpha=0.1, label='Safe Zone')
            ax.axhline(0.85, color='red', linestyle='--', alpha=0.5, label='Upper Limit')
            ax.axhline(0.25, color='red', linestyle='--', alpha=0.5, label='Lower Limit')
        
        for gas_type in ["BFG", "BOFG", "COG"]:
            data = recorder.gas_holder_soc[gas_type][:frame+1]
            ax.plot(t, data, label=gas_type, color=self.colors[gas_type], linewidth=2, marker='o', markersize=3)
        
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('SOC (fraction)')
        ax.set_ylim(0, 1)
        ax.set_title('Gas Holder State of Charge')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
    
    def _setup_pressure_plot(self, ax):
        """Setup pressure subplot"""
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Pressure (kPa)')
        ax.set_title('Gas Holder Pressure')
        ax.grid(True, alpha=0.3)
    
    def _update_pressure_plot(self, ax, recorder: DataRecorder, frame: int):
        """Update pressure plot"""
        t = recorder.timesteps[:frame+1]
        
        # Safety zone (9-14 kPa)
        if t:
            ax.axhspan(9, 14, color='green', alpha=0.1, label='Safe Zone')
            ax.axhline(14, color='red', linestyle='--', alpha=0.5, label='Upper Limit')
            ax.axhline(9, color='red', linestyle='--', alpha=0.5, label='Lower Limit')
        
        for gas_type in ["BFG", "BOFG", "COG"]:
            data = recorder.gas_holder_pressure[gas_type][:frame+1]
            ax.plot(t, data, label=gas_type, color=self.colors[gas_type], linewidth=2, marker='s', markersize=3)
        
        ax.set_xlabel('Time (steps)')
        ax.set_ylabel('Pressure (kPa)')
        ax.set_ylim(5, 18)
        ax.set_title('Gas Holder Pressure')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')


class AgentResponseVisualizer:
    """
    Visualizes agent actions and system responses.
    
    Creates multi-panel plots showing:
    - Agent actions over time
    - Twin outputs in response
    - Gas network state changes
    """
    
    def plot_action_response(
        self, 
        data_recorder: DataRecorder, 
        output_file: str = "action_response.png",
        dpi: int = 150
    ):
        """
        Create agent action-response visualization.
        
        Args:
            data_recorder: DataRecorder with simulation history
            output_file: Output PNG filename
            dpi: Resolution
        """
        if len(data_recorder.timesteps) == 0:
            raise ValueError("No data recorded - cannot create plot")
        
        # Create 3-row figure
        fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
        fig.suptitle('Agent Actions and System Responses', fontsize=16, fontweight='bold')
        
        t = np.array(data_recorder.timesteps)
        
        # Row 1: Agent Actions
        ax1 = axes[0]
        self._plot_agent_actions(ax1, t, data_recorder)
        
        # Row 2: Twin Outputs
        ax2 = axes[1]
        self._plot_twin_outputs(ax2, t, data_recorder)
        
        # Row 3: Gas Network State
        ax3 = axes[2]
        self._plot_gas_network_state(ax3, t, data_recorder)
        
        plt.xlabel('Time (steps)', fontsize=12)
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
        print(f"✅ Action-response plot saved to {output_file}")
        plt.close(fig)
    
    def _plot_agent_actions(self, ax, t, recorder: DataRecorder):
        """Plot agent actions"""
        ax2 = ax.twinx()
        ax3 = ax.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        
        # Plot wind volume
        wind = np.array(recorder.agent_actions["wind_volume"])
        ax.plot(t, wind, 'b-', label='Wind Volume', linewidth=2)
        ax.set_ylabel('Wind (Nm³/min)', color='b')
        ax.tick_params(axis='y', labelcolor='b')
        
        # Plot O2 enrichment
        o2 = np.array(recorder.agent_actions["O2_enrichment"])
        ax2.plot(t, o2, 'g-', label='O2 Enrichment', linewidth=2)
        ax2.set_ylabel('O2 Enrichment (%)', color='g')
        ax2.tick_params(axis='y', labelcolor='g')
        
        # Plot PCI
        pci = np.array(recorder.agent_actions["PCI"])
        ax3.plot(t, pci, 'r-', label='PCI', linewidth=2)
        ax3.set_ylabel('PCI (kg/t HM)', color='r')
        ax3.tick_params(axis='y', labelcolor='r')
        
        ax.set_title('BF Agent Actions', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
    
    def _plot_twin_outputs(self, ax, t, recorder: DataRecorder):
        """Plot twin outputs"""
        ax2 = ax.twinx()
        ax3 = ax.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        
        # Plot BFG supply
        bfg = np.array(recorder.twin_outputs["bfg_supply"])
        ax.plot(t, bfg, 'b-', label='BFG Supply', linewidth=2)
        ax.set_ylabel('BFG (m³/h)', color='b')
        ax.tick_params(axis='y', labelcolor='b')
        
        # Plot T_hot_metal
        T = np.array(recorder.twin_outputs["T_hot_metal"])
        ax2.plot(t, T, 'orange', label='T_hot_metal', linewidth=2)
        ax2.set_ylabel('Temperature (°C)', color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')
        
        # Plot Si
        Si = np.array(recorder.twin_outputs["Si"])
        ax3.plot(t, Si, 'purple', label='Si Content', linewidth=2)
        ax3.set_ylabel('Si (%)', color='purple')
        ax3.tick_params(axis='y', labelcolor='purple')
        
        ax.set_title('BF Twin Outputs', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
    
    def _plot_gas_network_state(self, ax, t, recorder: DataRecorder):
        """Plot gas network state"""
        # Plot SOC for all gas types
        colors = {"BFG": "#1f77b4", "BOFG": "#2ca02c", "COG": "#ff7f0e"}
        
        for gas_type, color in colors.items():
            soc = np.array(recorder.gas_holder_soc[gas_type])
            ax.plot(t, soc, color=color, label=f'{gas_type} SOC', linewidth=2)
        
        # Safety zones
        ax.axhspan(0.25, 0.85, color='green', alpha=0.1, label='Safe Zone')
        ax.axhline(0.85, color='red', linestyle='--', alpha=0.5)
        ax.axhline(0.25, color='red', linestyle='--', alpha=0.5)
        
        ax.set_ylabel('SOC (fraction)')
        ax.set_ylim(0, 1)
        ax.set_title('Gas Network State (SOC)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')


# Utility function for quick visualization
def visualize_simulation(data_recorder: DataRecorder, output_dir: str = "output"):
    """
    Quick visualization of simulation results.
    
    Creates both animation and action-response plot.
    
    Args:
        data_recorder: DataRecorder with simulation history
        output_dir: Output directory for files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{data_recorder.get_data_summary()}")
    
    # Create animations
    print("\nGenerating visualizations...")
    
    flow_viz = AnimatedFlowVisualizer()
    flow_viz.create_animation(
        data_recorder, 
        output_file=os.path.join(output_dir, "mas_flows.mp4")
    )
    
    response_viz = AgentResponseVisualizer()
    response_viz.plot_action_response(
        data_recorder,
        output_file=os.path.join(output_dir, "action_response.png")
    )
    
    print(f"\n✅ All visualizations saved to {output_dir}/")
