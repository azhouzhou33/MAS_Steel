"""
Standard Interfaces for Twin-Agent Interaction

This module defines standardized data structures for:
- State representation (StandardState)
- Action representation (StandardAction)
- Reward structure (Reward)
- Transition recording (Transition)

Purpose: Create uniform interface for all Twin-Agent interactions,
         enabling easy extension and RL integration in the future.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class GasHolderState:
    """Gas holder state representation"""
    soc_bfg: float      # State of charge BFG [0-1]
    soc_bofg: float     # State of charge BOFG [0-1]
    soc_cog: float      # State of charge COG [0-1]
    p_bfg: float        # Pressure BFG [kPa]
    p_bofg: float       # Pressure BOFG [kPa]
    p_cog: float        # Pressure COG [kPa]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for logging/serialization"""
        return {
            "soc_bfg": self.soc_bfg,
            "soc_bofg": self.soc_bofg,
            "soc_cog": self.soc_cog,
            "p_bfg": self.p_bfg,
            "p_bofg": self.p_bofg,
            "p_cog": self.p_cog,
        }


@dataclass
class ProductionState:
    """Production units state representation"""
    # Blast Furnace
    bf_bfg_supply: float        # BFG production [Nm³/h]
    bf_t_hot_metal: float       # Hot metal temperature [°C]
    bf_si_content: float        # Silicon content [%]
    
    # BOF
    bof_bofg_supply: float      # BOFG production [Nm³/h]
    
    # Coke Oven
    coke_cog_supply: float      # COG production [Nm³/h]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "bf_bfg_supply": self.bf_bfg_supply,
            "bf_t_hot_metal": self.bf_t_hot_metal,
            "bf_si_content": self.bf_si_content,
            "bof_bofg_supply": self.bof_bofg_supply,
            "coke_cog_supply": self.coke_cog_supply,
        }


@dataclass
class DemandState:
    """Demand/consumption state representation"""
    # Current demands
    power_plant_demand: float   # Power plant gas demand [Nm³/h]
    heating_demand: float       # Heating furnace demand [Nm³/h]
    
    # Priority/scheduling (0-1, higher = more urgent)
    priority_level: float       # Overall system priority
    
    # Note: Economic signals (electricity_price, gas_price) 
    #       will be added in future RL phase
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "power_plant_demand": self.power_plant_demand,
            "heating_demand": self.heating_demand,
            "priority_level": self.priority_level,
        }


@dataclass
class StandardState:
    """
    Unified state representation for the entire steel production system
    
    This is the core interface between environment and agents.
    All agents receive this standardized state.
    """
    time: int                           # Simulation step
    gas_holder: GasHolderState          # Gas storage states
    production: ProductionState         # Production unit states
    demand: DemandState                 # Demand/consumption states
    
    # Extensibility: Additional fields can be added here in future
    # e.g., economic_state: EconomicState (prices, costs)
    #       maintenance_state: MaintenanceState (equipment status)
    
    metadata: Dict[str, Any] = field(default_factory=dict)  # For custom data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire state to nested dictionary"""
        return {
            "time": self.time,
            "gas_holder": self.gas_holder.to_dict(),
            "production": self.production.to_dict(),
            "demand": self.demand.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class GasAllocation:
    """Gas distribution decisions"""
    # BFG allocation
    bfg_to_power_plant: float   # [Nm³/h]
    bfg_to_heating: float       # [Nm³/h]
    
    # BOFG allocation
    bofg_to_power_plant: float  # [Nm³/h]
    
    # COG allocation
    cog_to_bf: float            # COG to blast furnace [Nm³/h]
    cog_to_heating: float       # COG to heating [Nm³/h]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "bfg_to_power_plant": self.bfg_to_power_plant,
            "bfg_to_heating": self.bfg_to_heating,
            "bofg_to_power_plant": self.bofg_to_power_plant,
            "cog_to_bf": self.cog_to_bf,
            "cog_to_heating": self.cog_to_heating,
        }


@dataclass
class ProductionControl:
    """Production control parameters"""
    # Blast Furnace controls
    bf_wind_volume: float       # Blast air volume [Nm³/min]
    bf_pci: float               # Pulverized coal injection [kg/tHM]
    bf_o2_enrichment: float     # Oxygen enrichment [%]
    
    # BOF controls
    bof_oxygen: float           # Oxygen flow [Nm³/h]
    bof_scrap_steel: float      # Scrap steel ratio [t/h]
    
    # Coke Oven controls
    coke_pushing_rate: float    # Pushing rate [ovens/h]
    coke_heating_gas: float     # Heating gas input [Nm³/h]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "bf_wind_volume": self.bf_wind_volume,
            "bf_pci": self.bf_pci,
            "bf_o2_enrichment": self.bf_o2_enrichment,
            "bof_oxygen": self.bof_oxygen,
            "bof_scrap_steel": self.bof_scrap_steel,
            "coke_pushing_rate": self.coke_pushing_rate,
            "coke_heating_gas": self.coke_heating_gas,
        }


@dataclass
class StandardAction:
    """
    Unified action representation for agent decisions
    
    Combines gas allocation and production control into single structure.
    """
    gas_allocation: GasAllocation       # How to distribute gases
    production_control: ProductionControl  # How to control production
    
    # Extensibility: Additional control types can be added
    # e.g., maintenance_action: MaintenanceAction
    #       market_action: MarketAction (for energy trading)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to nested dictionary"""
        return {
            "gas_allocation": self.gas_allocation.to_dict(),
            "production_control": self.production_control.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class Reward:
    """
    Multi-objective reward structure
    
    Tracks different aspects of system performance for evaluation and RL.
    """
    # Individual reward components
    production_score: float     # Production output (0-1)
    stability_score: float      # System stability (0-1)
    efficiency_score: float     # Resource utilization (0-1)
    
    # Weighted total reward
    total: float
    
    # Detailed breakdown (optional, for debugging)
    breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "production_score": self.production_score,
            "stability_score": self.stability_score,
            "efficiency_score": self.efficiency_score,
            "total": self.total,
            "breakdown": self.breakdown,
        }


@dataclass
class Transition:
    """
    Complete state transition for RL training
    
    Records (state, action, next_state, reward) tuple for each step.
    Essential for replaying experiences and training RL agents.
    """
    state: StandardState
    action: StandardAction
    next_state: StandardState
    reward: Reward
    step: int
    
    # Optional: terminal flag for episodic training
    done: bool = False
    
    # Optional: additional info (e.g., which agent made decision)
    info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "step": self.step,
            "state": self.state.to_dict(),
            "action": self.action.to_dict(),
            "next_state": self.next_state.to_dict(),
            "reward": self.reward.to_dict(),
            "done": self.done,
            "info": self.info,
        }


# ===== Helper Functions =====

def create_default_state(time: int = 0) -> StandardState:
    """Create a default StandardState for initialization"""
    return StandardState(
        time=time,
        gas_holder=GasHolderState(
            soc_bfg=0.5, soc_bofg=0.5, soc_cog=0.5,
            p_bfg=12.0, p_bofg=12.0, p_cog=12.0
        ),
        production=ProductionState(
            bf_bfg_supply=0.0,
            bf_t_hot_metal=1500.0,
            bf_si_content=0.45,
            bof_bofg_supply=0.0,
            coke_cog_supply=0.0
        ),
        demand=DemandState(
            power_plant_demand=50000.0,
            heating_demand=20000.0,
            priority_level=0.5
        )
    )


def create_default_action() -> StandardAction:
    """Create a default StandardAction"""
    return StandardAction(
        gas_allocation=GasAllocation(
            bfg_to_power_plant=30000.0,
            bfg_to_heating=20000.0,
            bofg_to_power_plant=10000.0,
            cog_to_bf=5000.0,
            cog_to_heating=3000.0
        ),
        production_control=ProductionControl(
            bf_wind_volume=4000.0,
            bf_pci=150.0,
            bf_o2_enrichment=3.5,
            bof_oxygen=20000.0,
            bof_scrap_steel=20.0,
            coke_pushing_rate=1.2,
            coke_heating_gas=15000.0
        )
    )
