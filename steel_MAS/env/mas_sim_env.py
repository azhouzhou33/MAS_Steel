"""
Multi-Agent Simulation Environment
Coordinates agents with digital twins - REFACTORED ARCHITECTURE
"""

import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(parent_dir))

import numpy as np
from typing import Dict, Any, List, Optional
from protocols.gas_request import MessageBus
from models import GasNetwork
from translators import TwinTranslator

# Import twins with proper path handling
import importlib.util
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
digital_twin_dir = os.path.join(parent_dir, "Digital_Twin")

try:
    # Import BlastFurnaceTwin
    bf_path = os.path.join(digital_twin_dir, "Blast Furnace", "Blast_Furnace_Twin_to_share.py")
    spec = importlib.util.spec_from_file_location("BlastFurnaceTwin", bf_path)
    bf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bf_module)
    BlastFurnaceTwin = bf_module.BlastFurnaceTwin
    
    # Import BOFTwin
    bof_path = os.path.join(digital_twin_dir, "BOF", "BOF_Twin.py")
    spec = importlib.util.spec_from_file_location("BOFTwin", bof_path)
    bof_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bof_module)
    BOFTwin = bof_module.BOFTwin
    
    # Import CokeOvenTwin
    co_path = os.path.join(digital_twin_dir, "Coke Oven", "Coke_Oven_Twin.py")
    spec = importlib.util.spec_from_file_location("CokeOvenTwin", co_path)
    co_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(co_module)
    CokeOvenTwin = co_module.CokeOvenTwin
    
    TWINS_AVAILABLE = True
except Exception as e:
    TWINS_AVAILABLE = False
    print(f"Warning: Could not import digital twins - {e}")


class MAS_SimEnv:
    """
    Simulation environment for Multi-Agent System - REFACTORED
    
    New Architecture Features:
    1. Unified MessageBus - Single source of truth for communication
    2. TwinTranslator - Centralized physical mappings
    3. GasNetwork - Unified gas holder management
    4. Typed Data Models - Replace bare dictionaries
    5. Clean Separation - Pure orchestration, no physics or control logic
    """
    
    def __init__(self, use_twins: bool = True):
        """
        Initialize environment.
        
        Args:
            use_twins: Whether to use Digital Twin models (vs simple dynamics)
        """
        # ===== UNIFIED MESSAGE BUS =====
        # Env owns the single MessageBus - agents access via get_message_bus()
        self.message_bus = MessageBus()
        
        # ===== CONFIGURATION =====
        self.use_twins = use_twins and TWINS_AVAILABLE
        self.time = 0.0  # Simulation time in minutes
        self.timestep = 1.0  # 1 minute per step
        
        # ===== NEW COMPONENTS =====
        # Translator handles all physical mappings
        self.translator = TwinTranslator()
        
        # Gas Network manages all gas holders
        self.gas_network = GasNetwork(use_state_space_models=self.use_twins)
        
        # ===== TWIN MODELS =====
        if self.use_twins:
            self._init_twins()
        
        # ===== ENVIRONMENT STATE =====
        # State is purely for observations - no control logic here!
        self.state = {
            # BF state (from Twin outputs)
            "Si": 0.45,
            "T_hot_metal": 1500,
            "pig_iron_production": 200,
            
            # BOF state (from Twin outputs)
            "T_steel": 1650,
            "liquid_steel": 95,
            
            # Coke Oven state (from Twin outputs)
            "T_furnace": 1200,
            "coke_production": 72,
            
            # Gas network state (delegated to GasNetwork)
            "soc_bfg": 0.5,
            "p_bfg": 12.0,
            "bfg_supply": 100000,  # Nm³/h
            
            "soc_bofg": 0.5,
            "p_bofg": 12.0,
            "bofg_supply": 30000,
            
            "soc_cog": 0.5,
            "p_cog": 12.0,
            "cog_supply": 15000,
            
            # Resources
            "COG_available": 15000,
            "O2_available": 50000,
            "peak_electricity": False,
        }
    
    def _init_twins(self):
        """Initialize digital twins"""
        try:
            self.bf_twin = BlastFurnaceTwin()
            self.bof_twin = BOFTwin()
            self.co_twin = CokeOvenTwin()
            
            print("✅ Digital twins initialized in MAS_SimEnv")
        except Exception as e:
            print(f"Error initializing twins: {e}")
            self.use_twins = False
    
    def get_message_bus(self) -> MessageBus:
        """
        Provide access to the unified message bus.
        Agents call this to access communication infrastructure.
        
        Returns:
            The single MessageBus instance
        """
        return self.message_bus
    
    def step(self, agent_actions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute one simulation step.
        
        Architecture:
        1. Update time and message bus
        2. Call twins with translated inputs (physics simulation)
        3. Update gas network (energy system dynamics)
        4. Update environment state from outputs
        5. Return observations to agents
        
        Args:
            agent_actions: Dict of {agent_name: action_dict}
                - "BF": BF agent actions
                - "BOF": BOF agent actions
                - "CokeOven": Coke oven agent actions
                - "GasHolder": Gas holder agent actions
        
        Returns:
            observations: Updated observations for all agents
        """
        # Update time
        self.time += self.timestep
        self.message_bus.update_time(self.time)
        
        # Extract actions
        bf_action = agent_actions.get("BF", {})
        bof_action = agent_actions.get("BOF", {})
        co_action = agent_actions.get("CokeOven", {})
        gh_action = agent_actions.get("GasHolder", {})
        
        # Run environment step
        if self.use_twins:
            self._step_with_twins(bf_action, bof_action, co_action, gh_action)
        else:
            self._step_simple_dynamics(bf_action, bof_action, co_action, gh_action)
        
        # Return observations
        return self.get_observations()
    
    def _step_with_twins(self, bf_action, bof_action, co_action, gh_action):
        """
        Step with digital twin models.
        
        NEW ARCHITECTURE:
        - Uses TwinTranslator for all mappings
        - Uses typed data models
        - Delegates gas network to GasNetwork class
        - No physics simulation here - twins handle everything!
        """
        
        # ========== 1. BLAST FURNACE TWIN ==========
        # Translate agent action to typed input
        bf_input = self.translator.bf_action_to_twin_input(bf_action, self.state)
        
        # Validate
        if not bf_input.validate():
            print("Warning: Invalid BF input, using defaults")
        
        # Call twin (convert typed input to legacy dict format)
        bf_output_dict = self.bf_twin(bf_input.to_twin_dict())
        
        # Convert output to typed model
        from models.twin_data import BFOutput
        bf_output = BFOutput.from_twin_dict(bf_output_dict)
        
        # Update state using translator
        state_updates = self.translator.bf_output_to_env_state(bf_output)
        self.state.update(state_updates)
        
        # ========== 2. BOF TWIN ==========
        bof_input = self.translator.bof_action_to_twin_input(bof_action, self.state)
        
        if bof_input.validate():
            bof_output_dict = self.bof_twin(bof_input.to_twin_dict())
            from models.twin_data import BOFOutput
            bof_output = BOFOutput.from_twin_dict(bof_output_dict)
            state_updates = self.translator.bof_output_to_env_state(bof_output)
            self.state.update(state_updates)
        
        # ========== 3. COKE OVEN TWIN ==========
        co_input = self.translator.coke_oven_action_to_twin_input(co_action, self.state)
        
        if co_input.validate():
            co_output_dict = self.co_twin(co_input.to_twin_dict())
            from models.twin_data import CokeOvenOutput
            co_output = CokeOvenOutput.from_twin_dict(co_output_dict)
            state_updates = self.translator.coke_oven_output_to_env_state(co_output)
            self.state.update(state_updates)
        
        # ========== 4. GAS NETWORK (UNIFIED) ==========
        # Prepare production and demand data
        gas_production = {
            "bfg": self.state.get("bfg_supply", 100000),
            "bofg": self.state.get("bofg_supply", 30000),
            "cog": self.state.get("cog_supply", 15000)
        }
        
        # Update gas network (replaces scattered gas holder updates!)
        gas_network_state = self.gas_network.update(
            gas_production=gas_production,
            gas_demands=gh_action,
            timestep=self.timestep
        )
        
        # Update environment state from gas network
        self.state.update(gas_network_state.to_dict())
        
        # NO random walks, NO physics here - twins handle everything!
    
    def _step_simple_dynamics(self, bf_action, bof_action, co_action, gh_action):
        """
        Simple dynamics without twins (for testing).
        Even here, we use GasNetwork for consistency!
        """
        # Simplified production calculations
        wind = bf_action.get("wind_volume", 4000)
        self.state["pig_iron_production"] = wind / 20
        self.state["bfg_supply"] = wind * 25
        
        # Update gas network (unified!)
        gas_production = {
            "bfg": self.state["bfg_supply"],
            "bofg": self.state.get("bofg_supply", 30000),
            "cog": self.state.get("cog_supply", 15000)
        }
        
        gas_network_state = self.gas_network.update(
            gas_production=gas_production,
            gas_demands=gh_action,
            timestep=self.timestep
        )
        
        self.state.update(gas_network_state.to_dict())
        
        # Simple Si dynamics (in real system, Twin would handle this)
        self.state["Si"] += np.random.normal(0, 0.01)
        self.state["Si"] = np.clip(self.state["Si"], 0.3, 0.6)
    
    def get_observations(self) -> Dict[str, Any]:
        """Get current observations for all agents"""
        return self.state.copy()
    
    def reset(self) -> Dict[str, Any]:
        """Reset environment to initial state"""
        self.time = 0.0
        self.message_bus.clear()
        
        # Reset gas network
        self.gas_network.reset()
        
        # Reset state
        self.state["soc_bfg"] = 0.5
        self.state["soc_bofg"] = 0.5
        self.state["soc_cog"] = 0.5
        self.state["Si"] = 0.45
        self.state["T_hot_metal"] = 1500
        self.state["T_steel"] = 1650
        
        return self.get_observations()


if __name__ == "__main__":
    # Test new architecture
    print("Testing refactored MAS_SimEnv...")
    
    env = MAS_SimEnv(use_twins=True)
    
    print(f"\n✅ MessageBus ID: {id(env.get_message_bus())}")
    print(f"✅ Translator: {env.translator}")
    print(f"✅ GasNetwork: {env.gas_network}")
    
    # Dummy actions
    actions = {
        "BF": {"wind_volume": 4000, "O2_enrichment": 3.5, "PCI": 150},
        "BOF": {"oxygen": 45000, "scrap_steel": 20},
        "CokeOven": {"heating_gas_input": 15000},
        "GasHolder": {"bfg_to_pp": 50000, "bfg_to_heating": 30000}
    }
    
    obs = env.step(actions)
    print(f"\n✅ Observations after step:")
    print(f"  SOC_BFG: {obs['soc_bfg']:.3f}")
    print(f"  P_BFG: {obs['p_bfg']:.1f} kPa")
    print(f"  Pig Iron: {obs['pig_iron_production']:.1f} t/h")
    
    print("\n✅ Refactored environment test complete!")
