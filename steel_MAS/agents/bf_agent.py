"""
Blast Furnace Agent
Implements multi-level rule-based control for blast furnace
"""

import sys
sys.path.append('..')

from typing import Dict, Any, Optional
from solvers.rule_based import RuleBasedController, SafetyLimits
from protocols.gas_request import GasRequest, MessageBus


class BF_Agent:
    """
    Blast Furnace Agent with multi-level rule hierarchy:
    - Level 1: Safety (hard constraints)
    - Level 2: Process stability (Si control, temperature)
    - Level 3: Energy coordination (gas holder, COG, O2 coupling)
    - Level 4: Economic optimization
    """
    
    def __init__(self, agent_id: str = "BF1"):
        self.agent_id = agent_id
        self.controller = RuleBasedController()
        
        # Internal state
        self.state = {
            "wind_volume": 4000,  # Nm³/min
            "O2_enrichment": 3.5,  # %
            "PCI": 150,  # kg/t HM
            "COG_ratio": 0.2,  # fraction of heating gas
            "Si_target": 0.45,  # %
            "T_target": 1500,  # °C
        }
        
        # Hysteresis states
        self.hysteresis_states = {
            "gh_full_action_active": False,
            "gh_empty_action_active": False,
            "si_high_action_active": False,
            "si_low_action_active": False,
        }
        
        # Parameters
        self.Si_band = 0.03  # hysteresis band
        self.SOC_high = 0.85
        self.SOC_low = 0.25
        self.P_high = 14.0  # kPa
        self.P_low = 9.0    # kPa
        
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
            observations: Current observations from environment/twin
                - Si: Silicon content [%]
                - T_hot_metal: Hot metal temperature [°C]
                - SOC_bfg: BFG gas holder SOC [0-1]
                - P_bfg: BFG pressure [kPa]
                - COG_available: COG available [Nm³/h]
                - COG_required: COG required [Nm³/h]
                - O2_available: O2 available [Nm³/h]
                - peak_electricity: Boolean, is it peak hours
            
        Returns: Action dictionary
        """
        # Extract observations
        Si = observations.get("Si", 0.45)
        T_hot_metal = observations.get("T_hot_metal", 1500)
        SOC_bfg = observations.get("SOC_bfg", 0.5)
        P_bfg = observations.get("P_bfg", 12.0)
        COG_available = observations.get("COG_available", 10000)
        COG_required = observations.get("COG_required", 8000)
        O2_available = observations.get("O2_available", 50000)
        peak_electricity = observations.get("peak_electricity", False)
        
        # Apply rules in priority order
        self._apply_safety_rules(Si, T_hot_metal, O2_available)
        self._apply_process_rules(Si)
        self._apply_energy_rules(SOC_bfg, P_bfg, COG_available, COG_required, O2_available)
        self._apply_economic_rules(peak_electricity)
        
        return self.get_state()
    
    def _apply_safety_rules(self, Si: float, T_hot_metal: float, O2_available: float):
        """Level 1: Safety rules (highest priority)"""
        
        # Hard limits on wind volume
        self.state["wind_volume"] = self.controller.clamp(
            self.state["wind_volume"],
            SafetyLimits.BF_WIND_MIN,
            SafetyLimits.BF_WIND_MAX
        )
        
        # Hard limits on O2 enrichment
        self.state["O2_enrichment"] = self.controller.clamp(
            self.state["O2_enrichment"],
            0.0,
            SafetyLimits.BF_O2_MAX
        )
        
        # Temperature protection
        if T_hot_metal > SafetyLimits.BF_TEMP_MAX:
            # Emergency: reduce heat input (fast response)
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "decrease", step_size=0.20
            )
            self.state["O2_enrichment"] = self.controller.incremental_adjust(
                self.state["O2_enrichment"], "decrease", step_size=0.20
            )
        
        # Si protection
        if Si > SafetyLimits.BF_SI_MAX:
            # High Si: reduce PCI
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "decrease", step_size=0.05
            )
    
    def _apply_process_rules(self, Si: float):
        """Level 2: Process stability rules"""
        
        Si_target = self.state["Si_target"]
        
        # Si too high - increase reduction/decrease heat fluctuation
        if Si > Si_target + self.Si_band:
            self.hysteresis_states["si_high_action_active"] = True
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "decrease", step_size=0.10  # Increased from 0.02
            )
            self.state["O2_enrichment"] = self.controller.incremental_adjust(
                self.state["O2_enrichment"], "decrease", step_size=0.10  # Increased from 0.02
            )
        elif Si < Si_target + self.Si_band/2:
            self.hysteresis_states["si_high_action_active"] = False
        
        # Si too low - increase PCI or wind
        if Si < Si_target - self.Si_band:
            self.hysteresis_states["si_low_action_active"] = True
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "increase", step_size=0.10,  # Increased from 0.02
                max_val=SafetyLimits.BF_PCI_MAX
            )
            self.state["wind_volume"] = self.controller.incremental_adjust(
                self.state["wind_volume"], "increase", step_size=0.10,  # Increased from 0.01
                max_val=SafetyLimits.BF_WIND_MAX
            )
        elif Si > Si_target - self.Si_band/2:
            self.hysteresis_states["si_low_action_active"] = False
    
    def _apply_energy_rules(
        self,
        SOC_bfg: float,
        P_bfg: float,
        COG_available: float,
        COG_required: float,
        O2_available: float
    ):
        """Level 3: Energy coordination rules"""
        
        # Gas holder too full - reduce BFG production (fast response needed!)
        if SOC_bfg > self.SOC_high or P_bfg > self.P_high:
            self.hysteresis_states["gh_full_action_active"] = True
            self.state["wind_volume"] = self.controller.incremental_adjust(
                self.state["wind_volume"], "decrease", step_size=0.15,  # Increased from 0.05
                min_val=SafetyLimits.BF_WIND_MIN
            )
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "decrease", step_size=0.12  # Increased from 0.03
            )
            self.state["O2_enrichment"] = self.controller.incremental_adjust(
                self.state["O2_enrichment"], "decrease", step_size=0.15  # Increased from 0.05
            )
        elif SOC_bfg < 0.75 and P_bfg < 13.0:
            self.hysteresis_states["gh_full_action_active"] = False
        
        # Gas holder too empty - increase BFG production (fast response needed!)
        if SOC_bfg < self.SOC_low or P_bfg < self.P_low:
            self.hysteresis_states["gh_empty_action_active"] = True
            self.state["wind_volume"] = self.controller.incremental_adjust(
                self.state["wind_volume"], "increase", step_size=0.15,  # Increased from 0.05
                max_val=SafetyLimits.BF_WIND_MAX
            )
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "increase", step_size=0.12,  # Increased from 0.03
                max_val=SafetyLimits.BF_PCI_MAX
            )
        elif SOC_bfg > 0.30 and P_bfg > 10.0:
            self.hysteresis_states["gh_empty_action_active"] = False
        
        # COG shortage - reduce COG usage, compensate with PCI
        if COG_available < COG_required:
            self.state["COG_ratio"] = self.controller.incremental_adjust(
                self.state["COG_ratio"], "decrease", step_size=0.10,
                min_val=0.0
            )
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "increase", step_size=0.05,
                max_val=SafetyLimits.BF_PCI_MAX
            )
        
        # O2 shortage - reduce O2, increase PCI
        O2_required = self.state["O2_enrichment"] * self.state["wind_volume"] / 100
        if O2_available < O2_required:
            self.state["O2_enrichment"] = self.controller.incremental_adjust(
                self.state["O2_enrichment"], "decrease", step_size=0.10
            )
            self.state["PCI"] = self.controller.incremental_adjust(
                self.state["PCI"], "increase", step_size=0.04,
                max_val=SafetyLimits.BF_PCI_MAX
            )
    
    def _apply_economic_rules(self, peak_electricity: bool):
        """Level 4: Economic optimization (lowest priority)"""
        
        # During peak electricity hours, reduce wind volume (blower power)
        if peak_electricity:
            self.state["wind_volume"] = self.controller.incremental_adjust(
                self.state["wind_volume"], "decrease", step_size=0.05,
                min_val=SafetyLimits.BF_WIND_MIN
            )


if __name__ == "__main__":
    # Simple test
    agent = BF_Agent("BF1")
    
    # Test scenario: gas holder full
    obs = {
        "Si": 0.45,
        "T_hot_metal": 1500,
        "SOC_bfg": 0.90,  # Too full!
        "P_bfg": 15.0,    # Too high!
        "COG_available": 10000,
        "COG_required": 8000,
        "O2_available": 50000,
        "peak_electricity": False
    }
    
    print("Initial state:", agent.get_state())
    action = agent.step(obs)
    print("After step (GH full):", action)
