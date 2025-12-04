"""
Gas Holder Agent
Manages BFG, BOFG, and COG gasholders with priority-based allocation
"""

import sys
sys.path.append('..')

from typing import Dict, Any, Optional
from solvers.rule_based import RuleBasedController, SafetyLimits
from protocols.gas_request import MessageBus, MessageType


class GasHolder_Agent:
    """
    Gas Holder Agent managing three types of gas holders:
    - BFGH (Blast Furnace Gas Holder)
    - BOFGH (BOF Gas Holder)
    - COGH (Coke Oven Gas Holder)
    
    Multi-level rules:
    - Level 1: Safety (over-pressure, prevent empty)
    - Level 2: SOC/Pressure control
    - Level 3: Surge coordination
    - Level 4: Priority allocation
    """
    
    def __init__(self, agent_id: str = "GH1"):
        self.agent_id = agent_id
        self.controller = RuleBasedController()
        
        # State for each gas holder
        self.state = {
            # BFG
            "bfg_to_pp": 50000,  # to power plant [Nm³/h]
            "bfg_to_heating": 30000,  # to heating [Nm³/h]
            
            # BOFG  
            "bofg_to_pp": 20000,
            "bofg_to_heating": 10000,
            
            # COG
            "cog_to_heating": 8000,
            "cog_to_bf": 5000,  # to BF for injection
        }
        
        # Hysteresis states
        self.surge_warning_active = False
        
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
            observations: Current gas holder states
                - soc_bfg, p_bfg: BFG SOC and pressure
                - soc_bofg, p_bofg: BOFG SOC and pressure
                - soc_cog, p_cog: COG SOC and pressure
                - bfg_supply, bofg_supply, cog_supply: Production rates
                - pp_demand, heating_demand: Demand from consumers
        """
        # Extract observations
        soc_bfg = observations.get("soc_bfg", 0.5)
        p_bfg = observations.get("p_bfg", 12.0)
        soc_bofg = observations.get("soc_bofg", 0.5)
        p_bofg = observations.get("p_bofg", 12.0)
        soc_cog = observations.get("soc_cog", 0.5)
        p_cog = observations.get("p_cog", 12.0)
        
        # Check for surge warnings
        if message_bus:
            surge_warnings = message_bus.get_messages(
                self.agent_id,
                MessageType.BOFG_SURGE_WARNING
            )
            if surge_warnings:
                self.surge_warning_active = True
        
        # Apply rules to each gas holder
        self._control_bfgh(soc_bfg, p_bfg)
        self._control_bofgh(soc_bofg, p_bofg, self.surge_warning_active)
        self._control_cogh(soc_cog, p_cog)
        
        # Reset surge warning after handling
        self.surge_warning_active = False
        
        return self.get_state()
    
    def _control_bfgh(self, soc: float, p: float):
        """Control BFG holder"""
        
        # Level 1: Safety - Emergency over-pressure
        if p > SafetyLimits.GH_P_EMERGENCY:
            # Emergency: maximize outflow
            self.state["bfg_to_pp"] = self.controller.incremental_adjust(
                self.state["bfg_to_pp"], "increase", step_size=0.20,
                max_val=80000
            )
            self.state["bfg_to_heating"] = self.controller.incremental_adjust(
                self.state["bfg_to_heating"], "increase", step_size=0.10,
                max_val=50000
            )
            return  # Skip other rules
        
        # Level 1: Safety - Prevent empty
        if soc < SafetyLimits.GH_SOC_MIN:
            # Reduce all outflows
            self.state["bfg_to_pp"] = self.controller.incremental_adjust(
                self.state["bfg_to_pp"], "decrease", step_size=0.20,
                min_val=10000
            )
            self.state["bfg_to_heating"] = self.controller.incremental_adjust(
                self.state["bfg_to_heating"], "decrease", step_size=0.20,
                min_val=5000
            )
            return
        
        # Level 2: SOC/Pressure control
        # Too full
        if soc > 0.85 or p > 14:
            self.state["bfg_to_pp"] = self.controller.incremental_adjust(
                self.state["bfg_to_pp"], "increase", step_size=0.10,
                max_val=80000
            )
            self.state["bfg_to_heating"] = self.controller.incremental_adjust(
                self.state["bfg_to_heating"], "increase", step_size=0.05,
                max_val=50000
            )
        
        # Too empty
        elif soc < 0.25 or p < 9:
            self.state["bfg_to_pp"] = self.controller.incremental_adjust(
                self.state["bfg_to_pp"], "decrease", step_size=0.10,
                min_val=10000
            )
            self.state["bfg_to_heating"] = self.controller.incremental_adjust(
                self.state["bfg_to_heating"], "decrease", step_size=0.08,
                min_val=5000
            )
        
        # Normal range: slowly return to nominal
        elif 0.35 < soc < 0.75 and 10 < p < 13:
            # Trend back to nominal values
            nominal_pp = 50000
            nominal_heating = 30000
            
            if self.state["bfg_to_pp"] > nominal_pp:
                self.state["bfg_to_pp"] *= 0.98
            elif self.state["bfg_to_pp"] < nominal_pp:
                self.state["bfg_to_pp"] *= 1.02
            
            if self.state["bfg_to_heating"] > nominal_heating:
                self.state["bfg_to_heating"] *= 0.98
            elif self.state["bfg_to_heating"] < nominal_heating:
                self.state["bfg_to_heating"] *= 1.02
    
    def _control_bofgh(self, soc: float, p: float, surge_warning: bool):
        """Control BOFG holder"""
        
        # Level 3: Surge preparation
        if surge_warning:
            # Pre-emptively make room for surge
            self.state["bofg_to_pp"] = self.controller.incremental_adjust(
                self.state["bofg_to_pp"], "decrease", step_size=0.20,
                min_val=5000
            )
            self.state["bofg_to_heating"] = self.controller.incremental_adjust(
                self.state["bofg_to_heating"], "decrease", step_size=0.15,
                min_val=3000
            )
            return
        
        # Level 1: Safety
        if p > SafetyLimits.GH_P_EMERGENCY:
            self.state["bofg_to_pp"] = self.controller.incremental_adjust(
                self.state["bofg_to_pp"], "increase", step_size=0.20,
                max_val=40000
            )
            return
        
        if soc < SafetyLimits.GH_SOC_MIN:
            self.state["bofg_to_pp"] = self.controller.incremental_adjust(
                self.state["bofg_to_pp"], "decrease", step_size=0.20,
                min_val=5000
            )
            return
        
        # Level 2: SOC/Pressure control (similar to BFG)
        if soc > 0.85 or p > 14:
            self.state["bofg_to_pp"] = self.controller.incremental_adjust(
                self.state["bofg_to_pp"], "increase", step_size=0.10,
                max_val=40000
            )
        elif soc < 0.25 or p < 9:
            self.state["bofg_to_pp"] = self.controller.incremental_adjust(
                self.state["bofg_to_pp"], "decrease", step_size=0.10,
                min_val=5000
            )
    
    def _control_cogh(self, soc: float, p: float):
        """Control COG holder"""
        
        # Level 1: Safety
        if p > SafetyLimits.GH_P_EMERGENCY:
            self.state["cog_to_heating"] = self.controller.incremental_adjust(
                self.state["cog_to_heating"], "increase", step_size=0.20,
                max_val=15000
            )
            return
        
        if soc < SafetyLimits.GH_SOC_MIN:
            self.state["cog_to_heating"] = self.controller.incremental_adjust(
                self.state["cog_to_heating"], "decrease", step_size=0.20,
                min_val=2000
            )
            self.state["cog_to_bf"] = self.controller.incremental_adjust(
                self.state["cog_to_bf"], "decrease", step_size=0.20,
                min_val=1000
            )
            return
        
        # Level 2: SOC/Pressure control
        if soc > 0.85 or p > 14:
            self.state["cog_to_heating"] = self.controller.incremental_adjust(
                self.state["cog_to_heating"], "increase", step_size=0.10,
                max_val=15000
            )
            self.state["cog_to_bf"] = self.controller.incremental_adjust(
                self.state["cog_to_bf"], "increase", step_size=0.05,
                max_val=10000
            )
        elif soc < 0.25 or p < 9:
            self.state["cog_to_heating"] = self.controller.incremental_adjust(
                self.state["cog_to_heating"], "decrease", step_size=0.10,
                min_val=2000
            )
            self.state["cog_to_bf"] = self.controller.incremental_adjust(
                self.state["cog_to_bf"], "decrease", step_size=0.08,
                min_val=1000
            )


if __name__ == "__main__":
    # Simple test
    agent = GasHolder_Agent("GH1")
    
    obs = {
        "soc_bfg": 0.90,  # Too full
        "p_bfg": 15.0,    # Too high
        "soc_bofg": 0.5,
        "p_bofg": 12.0,
        "soc_cog": 0.5,
        "p_cog": 12.0
    }
    
    print("Initial state:", agent.get_state())
    action = agent.step(obs)
    print("After step (BFG full):", action)
