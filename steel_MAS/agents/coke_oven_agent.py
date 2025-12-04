"""
Coke Oven Agent
Implements rule-based control for coke oven temperature and pushing rate
"""

import sys
sys.path.append('..')

from typing import Dict, Any, Optional
from solvers.rule_based import RuleBasedController, SafetyLimits
from protocols.gas_request import MessageBus


class CokeOven_Agent:
    """
    Coke Oven Agent with multi-level rules:
    - Level 1: Safety (temperature limits)
    - Level 2: Process (temperature control, pushing rate)
    - Level 3: Energy coordination (COG production vs demand)
    """
    
    def __init__(self, agent_id: str = "CO1"):
        self.agent_id = agent_id
        self.controller = RuleBasedController()
        
        # Internal state
        self.state = {
            "heating_gas_input": 15000,  # Nm³/h
            "pushing_rate": 1.0,  # Relative to nominal
            "T_target": 1200,  # °C
        }
        
        # Parameters
        self.T_band = 20  # °C hysteresis band
        
    def get_state(self) -> Dict[str, Any]:
        """Return current state"""
        return self.state.copy()
    
    def step(
        self,
        observations: Dict[str, Any],
        message_bus: Optional[MessageBus] = None
    ) -> Dict[str, Any]:
        """
        Execute one control step
        
        Args:
            observations:
                - T_furnace: Furnace temperature [°C]
                - SOC_cog: COG gas holder SOC
                - COG_demand: COG demand [Nm³/h]
        """
        T_furnace = observations.get("T_furnace", 1200)
        SOC_cog = observations.get("SOC_cog", 0.5)
        COG_demand = observations.get("COG_demand", 10000)
        
        # Apply rules
        self._apply_safety_rules(T_furnace)
        self._apply_process_rules(T_furnace)
        self._apply_energy_rules(SOC_cog)
        
        return self.get_state()
    
    def _apply_safety_rules(self, T_furnace: float):
        """Level 1: Safety rules"""
        
        # Emergency temperature protection
        if T_furnace > SafetyLimits.CO_TEMP_MAX:
            self.state["heating_gas_input"] = self.controller.incremental_adjust(
                self.state["heating_gas_input"], "decrease", step_size=0.10,
                min_val=5000
            )
        
        if T_furnace < SafetyLimits.CO_TEMP_MIN:
            self.state["heating_gas_input"] = self.controller.incremental_adjust(
                self.state["heating_gas_input"], "increase", step_size=0.10,
                max_val=25000
            )
    
    def _apply_process_rules(self, T_furnace: float):
        """Level 2: Process stability"""
        
        T_target = self.state["T_target"]
        
        # Temperature control with hysteresis
        if T_furnace < T_target - self.T_band:
            # Too cold: increase heating gas
            self.state["heating_gas_input"] = self.controller.incremental_adjust(
                self.state["heating_gas_input"], "increase", step_size=0.03,
                max_val=25000
            )
        elif T_furnace > T_target + self.T_band:
            # Too hot: decrease heating gas
            self.state["heating_gas_input"] = self.controller.incremental_adjust(
                self.state["heating_gas_input"], "decrease", step_size=0.03,
                min_val=5000
            )
    
    def _apply_energy_rules(self, SOC_cog: float):
        """Level 3: Energy coordination"""
        
        # COG holder too full - slow down pushing
        if SOC_cog > 0.85:
            self.state["pushing_rate"] = self.controller.incremental_adjust(
                self.state["pushing_rate"], "decrease", step_size=0.05,
                min_val=0.7  # Don't go below 70% rate
            )
        elif SOC_cog < 0.75:
            # Normal operation
            self.state["pushing_rate"] = min(1.0, self.state["pushing_rate"] * 1.02)
        
        # COG holder too empty - speed up pushing
        if SOC_cog < 0.25:
            self.state["pushing_rate"] = self.controller.incremental_adjust(
                self.state["pushing_rate"], "increase", step_size=0.03,
                max_val=1.2  # Don't exceed 120% rate
            )
        elif SOC_cog > 0.35:
            # Return to normal
            if self.state["pushing_rate"] > 1.0:
                self.state["pushing_rate"] = max(1.0, self.state["pushing_rate"] * 0.98)


if __name__ == "__main__":
    # Simple test
    agent = CokeOven_Agent("CO1")
    
    obs = {
        "T_furnace": 1250,  # Slightly high
        "SOC_cog": 0.90,  # Too full
        "COG_demand": 10000
    }
    
    print("Initial state:", agent.get_state())
    action = agent.step(obs)
    print("After step (high T, full GH):", action)
