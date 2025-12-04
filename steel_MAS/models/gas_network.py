"""
Unified Gas Network Model
Replaces scattered gas holder update logic with a centralized, extensible model.

All comments use ASCII-only characters to avoid encoding issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class GasNetworkState:
    """
    Complete state of the gas network.
    Encapsulates all gas holders in a single coherent state object.
    """
    # BFG (Blast Furnace Gas)
    soc_bfg: float  # State of Charge [0-1]
    p_bfg: float  # Pressure [kPa]
    bfg_level: float  # Physical level [0-1]
    
    # BOFG (Basic Oxygen Furnace Gas)
    soc_bofg: float
    p_bofg: float
    bofg_level: float
    
    # COG (Coke Oven Gas)
    soc_cog: float
    p_cog: float
    cog_level: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for environment state updates"""
        return {
            "soc_bfg": self.soc_bfg,
            "p_bfg": self.p_bfg,
            "soc_bofg": self.soc_bofg,
            "p_bofg": self.p_bofg,
            "soc_cog": self.soc_cog,
            "p_cog": self.p_cog
        }


class GasNetwork:
    """
    Unified model for all gas holders and energy network.
    
    Benefits:
    - Single source of truth for gas holder dynamics
    - Easy to add new gas types (e.g., H2, natural gas)
    - Centralizes coupling between different gas systems
    - Replaces scattered if/else logic in environment
    
    Future Extensions:
    - Energy coupling between gas types
    - Network flow constraints
    - Multi-site gas distribution
    - Gas quality tracking
    """
    
    def __init__(self, use_state_space_models: bool = True):
        """
        Initialize gas network with state-space models.
        
        Args:
            use_state_space_models: Whether to use detailed state-space models
        """
        self.use_state_space_models = use_state_space_models
        
        # Gas holder capacities (Nm^3) - UPDATED to realistic steel plant scale
        # BFG: increased from 100k to 400k (4x)
        # BOFG: increased from 50k to 150k (3x)
        # COG: increased from 30k to 100k (3.3x)
        self.capacities = {
            "bfg": 400000,   # Nm^3
            "bofg": 150000,  # Nm^3
            "cog": 100000    # Nm^3
        }
        
        # Pressure model parameters
        self.pressure_params = {
            "p_min": 8.0,    # kPa (minimum safe pressure)
            "p_range": 8.0   # kPa (8-16 kPa range)
        }
        
        # Initialize state-space models if available
        if self.use_state_space_models:
            self._init_state_space_models()
        
        # Initialize state
        self.state = GasNetworkState(
            soc_bfg=0.5, p_bfg=12.0, bfg_level=0.5,
            soc_bofg=0.5, p_bofg=12.0, bofg_level=0.5,
            soc_cog=0.5, p_cog=12.0, cog_level=0.5
        )
    
    def _init_state_space_models(self):
        """Initialize state-space models for gas holders"""
        try:
            from Digital_Twin.Gasholders.Gasholders import BFGH, BOFGH, COGH
            
            self.bfgh = BFGH(input_names=["gas_net_flow"], output_names=["level"])
            self.bofgh = BOFGH(input_names=["gas_net_flow"], output_names=["level"])
            self.cogh = COGH(input_names=["gas_net_flow"], output_names=["level"])
            
            print("Gas Network: State-space models loaded")
        except ImportError:
            print("Warning: Gas holder state-space models not available")
            self.use_state_space_models = False
    
    def update(
        self,
        gas_production: Dict[str, float],
        gas_demands: Dict[str, float],
        timestep: float = 1.0
    ) -> GasNetworkState:
        """
        Unified update for all gas holders.
        
        This replaces individual gas holder update logic scattered throughout the code.
        
        Args:
            gas_production: Production rates by gas type
                Example: {"bfg": 100000, "bofg": 30000, "cog": 15000} in Nm^3/h
            gas_demands: All consumption demands
                Example: {"bfg_to_pp": 50000, "bfg_to_heating": 30000, 
                         "bofg_to_pp": 20000, "cog_to_heating": 8000, ...}
            timestep: Time step in minutes
        
        Returns:
            Updated GasNetworkState
        """
        # Calculate net flows for each gas type
        bfg_net = self._calculate_net_flow("bfg", gas_production, gas_demands)
        bofg_net = self._calculate_net_flow("bofg", gas_production, gas_demands)
        cog_net = self._calculate_net_flow("cog", gas_production, gas_demands)
        
        # Update each gas holder
        self._update_holder("bfg", bfg_net, timestep)
        self._update_holder("bofg", bofg_net, timestep)
        self._update_holder("cog", cog_net, timestep)
        
        return self.state
    
    def _calculate_net_flow(
        self,
        gas_type: str,
        gas_production: Dict[str, float],
        gas_demands: Dict[str, float]
    ) -> float:
        """
        Calculate net flow for a specific gas type.
        
        Args:
            gas_type: 'bfg', 'bofg', or 'cog'
            gas_production: Production rates
            gas_demands: All consumption demands
        
        Returns:
            Net flow (Nm^3/h)
        """
        # Get production
        production = gas_production.get(gas_type, 0.0)
        
        # Sum all consumption for this gas type
        consumption = 0.0
        for key, value in gas_demands.items():
            if gas_type in key.lower():
                consumption += value
        
        return production - consumption
    
    def _update_holder(self, gas_type: str, net_flow: float, timestep: float):
        """
        Update a single gas holder using state-space model or simple integration.
        
        Args:
            gas_type: 'bfg', 'bofg', or 'cog'
            net_flow: Net gas flow (Nm^3/h)
            timestep: Time step (minutes)
        """
        # Select the appropriate model and state variables
        if gas_type == "bfg":
            model = self.bfgh if self.use_state_space_models else None
            soc_attr, p_attr, level_attr = "soc_bfg", "p_bfg", "bfg_level"
        elif gas_type == "bofg":
            model = self.bofgh if self.use_state_space_models else None
            soc_attr, p_attr, level_attr = "soc_bofg", "p_bofg", "bofg_level"
        else:  # cog
            model = self.cogh if self.use_state_space_models else None
            soc_attr, p_attr, level_attr = "soc_cog", "p_cog", "cog_level"
        
        # Get current SOC
        current_soc = getattr(self.state, soc_attr)
        
        # Update SOC using simple integration
        # dSOC/dt = net_flow / capacity
        capacity = self.capacities[gas_type]
        delta_soc = (net_flow / 3600) * timestep * 60 / capacity
        new_soc = current_soc + delta_soc
        
        # Apply safety limits
        new_soc = np.clip(new_soc, 0.05, 0.95)
        
        # Update pressure from SOC (linear model)
        new_p = self.pressure_params["p_min"] + new_soc * self.pressure_params["p_range"]
        
        # Call state-space model if available (for more accurate dynamics)
        if model is not None:
            try:
                output = model({"gas_net_flow": net_flow})
                level = output.get("level", new_soc)
            except Exception as e:
                # Fallback to simple integration
                level = new_soc
        else:
            level = new_soc
        
        # Update state
        setattr(self.state, soc_attr, new_soc)
        setattr(self.state, p_attr, new_p)
        setattr(self.state, level_attr, level)
    
    def reset(self):
        """Reset gas network to initial state"""
        self.state = GasNetworkState(
            soc_bfg=0.5, p_bfg=12.0, bfg_level=0.5,
            soc_bofg=0.5, p_bofg=12.0, bofg_level=0.5,
            soc_cog=0.5, p_cog=12.0, cog_level=0.5
        )
    
    def get_state_dict(self) -> Dict[str, float]:
        """Get state as dictionary for environment"""
        return self.state.to_dict()
    
    # =========================================================================
    # FUTURE EXTENSIONS
    # =========================================================================
    
    def add_gas_coupling(self, source_gas: str, target_gas: str, coupling_factor: float):
        """
        Add coupling between gas types (e.g., COG can supplement natural gas).
        Placeholder for future energy network coupling.
        """
        # TODO: Implement gas coupling logic
        pass
    
    def add_external_supply(self, gas_type: str, external_flow: float):
        """
        Add external gas supply (e.g., natural gas backup).
        Placeholder for multi-source gas systems.
        """
        # TODO: Implement external supply logic
        pass


if __name__ == "__main__":
    # Test gas network
    gas_network = GasNetwork(use_state_space_models=False)
    
    print("Initial state:")
    print(gas_network.state)
    
    # Simulate production and consumption
    gas_production = {"bfg": 100000, "bofg": 30000, "cog": 15000}
    gas_demands = {
        "bfg_to_pp": 50000,
        "bfg_to_heating": 30000,
        "bofg_to_pp": 20000,
        "cog_to_heating": 8000
    }
    
    # Update
    new_state = gas_network.update(gas_production, gas_demands, timestep=1.0)
    
    print("\nAfter update:")
    print(new_state)
