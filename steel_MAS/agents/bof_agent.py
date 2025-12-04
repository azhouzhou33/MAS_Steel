"""
BOF (Basic Oxygen Furnace) Agent
Implements rule-based control for BOF with surge warning capability
"""

import sys
sys.path.append('..')

from typing import Dict, Any, Optional
from solvers.rule_based import RuleBasedController, SafetyLimits
from protocols.gas_request import BOFGSurgeWarning, MessageBus


class BOF_Agent:
    """
    BOF Agent with multi-level rules:
    - Level 1: Safety (O2 limits, pressure)
    - Level 2: Process (temperature control)
    - Level 3: Energy coordination (BOFG surge management)
    """
    
    def __init__(self, agent_id: str = "BOF1"):
        self.agent_id = agent_id
        self.controller = RuleBasedController()
        
        # Internal state
        self.state = {
            "oxygen": 45000,  # Nm³/h
            "scrap_steel": 20,  # t/batch
            "T_target": 1650,  # °C
            "blow_time": 0,  # minutes into blow
            "blow_duration": 18,  # typical blow duration
        }
        
        # Blow cycle tracking
        self.time_to_next_blow = 30.0  # minutes
        
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
                - T_steel: Steel temperature [°C]
                - P_bof_gas: BOF gas pressure [kPa]
                - bof_gas_current: Current BOFG production [Nm³/h]
                - SOC_bofg: BOFG gas holder SOC
                - P_bofg: BOFG pressure [kPa]
        """
        T_steel = observations.get("T_steel", 1650)
        P_bof_gas = observations.get("P_bof_gas", 12.0)
        bof_gas_current = observations.get("bof_gas_current", 30000)
        SOC_bofg = observations.get("SOC_bofg", 0.5)
        P_bofg = observations.get("P_bofg", 12.0)
        
        # Apply rules
        self._apply_safety_rules(P_bof_gas)
        self._apply_process_rules(T_steel)
        self._apply_energy_rules(bof_gas_current, SOC_bofg, P_bofg, message_bus)
        
        # Update time to next blow
        self.time_to_next_blow = max(0, self.time_to_next_blow - 1.0)  # Assume 1 min timestep
        
        return self.get_state()
        
    def _apply_safety_rules(self, P_bof_gas: float):
        """Level 1: Safety rules"""
        
        # O2 hard limit
        self.state["oxygen"] = self.controller.clamp(
            self.state["oxygen"],
            0.0,
            SafetyLimits.BOF_O2_MAX
        )
        
        # Pressure protection
        if P_bof_gas > SafetyLimits.BOF_P_MAX:
            self.state["oxygen"] = self.controller.incremental_adjust(
                self.state["oxygen"], "decrease", step_size=0.10
            )
    
    def _apply_process_rules(self, T_steel: float):
        """Level 2: Process stability"""
        
        T_target = self.state["T_target"]
        
        # Temperature too high
        if T_steel > T_target + 20:
            # Reduce oxygen or increase scrap
            self.state["oxygen"] = self.controller.incremental_adjust(
                self.state["oxygen"], "decrease", step_size=0.03
            )
            self.state["scrap_steel"] = self.controller.incremental_adjust(
                self.state["scrap_steel"], "increase", step_size=0.02,
                max_val=30  # Maximum scrap ratio
            )
        
        # Temperature too low
        elif T_steel < T_target - 20:
            self.state["oxygen"] = self.controller.incremental_adjust(
                self.state["oxygen"], "increase", step_size=0.03,
                max_val=SafetyLimits.BOF_O2_MAX
            )
    
    def _apply_energy_rules(
        self,
        bof_gas_current: float,
        SOC_bofg: float,
        P_bofg: float,
        message_bus: Optional[MessageBus]
    ):
        """Level 3: Energy coordination"""
        
        # Send surge warning if approaching blow time
        if self.time_to_next_blow <= 2.0 and message_bus is not None:
            warning = BOFGSurgeWarning(
                time_to_blow=self.time_to_next_blow,
                expected_peak=60000,  # Typical BOFG peak
                duration=self.state["blow_duration"],
                current_gh_soc=SOC_bofg
            )
            message_bus.send(warning.to_message(message_bus.time))
        
        # If already producing high BOFG and GH is pressurized
        bof_gas_design = 50000  # Design BOFG rate
        if bof_gas_current > bof_gas_design * 1.3 and P_bofg > 14:
            self.state["oxygen"] = self.controller.incremental_adjust(
                self.state["oxygen"], "decrease", step_size=0.10
            )


if __name__ == "__main__":
    # Simple test
    agent = BOF_Agent("BOF1")
    
    obs = {
        "T_steel": 1680,  # Too hot
        "P_bof_gas": 12.0,
        "bof_gas_current": 40000,
        "SOC_bofg": 0.5,
        "P_bofg": 12.0
    }
    
    print("Initial state:", agent.get_state())
    action = agent.step(obs)
    print("After step (high T):", action)
