"""
Rule-Based Control Utilities
Provides base classes and utilities for rule-based agent control
"""

import numpy as np
from typing import Dict, Any, Tuple


class RuleBasedController:
    """
    Base class for rule-based control with hysteresis and incremental adjustment
    """
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))
    
    @staticmethod
    def hysteresis_check(
        current_value: float,
        target: float,
        upper_band: float,
        lower_band: float,
        current_state: bool
    ) -> Tuple[bool, str]:
        """
        Hysteresis logic to avoid oscillation
        
        Args:
            current_value: Current measured value
            target: Target setpoint
            upper_band: Upper threshold above target
            lower_band: Lower threshold below target
            current_state: Current activation state (True = action active)
        
        Returns:
            (should_activate, reason)
        """
        if current_value > target + upper_band:
            return True, "above_upper_band"
        elif current_value < target - lower_band:
            return True, "below_lower_band"
        elif current_state:
            # Stay in current state if within hysteresis band
            if target - lower_band/2 <= current_value <= target + upper_band/2:
                return True, "within_hysteresis"
        return False, "normal"
    
    @staticmethod
    def incremental_adjust(
        current_value: float,
        direction: str,
        step_size: float = 0.05,
        min_val: float = 0.0,
        max_val: float = float('inf')
    ) -> float:
        """
        Incrementally adjust value (avoid large jumps)
        
        Args:
            current_value: Current value
            direction: 'increase' or 'decrease'
            step_size: Adjustment factor (e.g., 0.05 = 5%)
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        
        Returns:
            Adjusted value
        """
        if direction == 'increase':
            new_value = current_value * (1 + step_size)
        elif direction == 'decrease':
            new_value = current_value * (1 - step_size)
        else:
            new_value = current_value
        
        return RuleBasedController.clamp(new_value, min_val, max_val)
    
    @staticmethod
    def priority_allocate(
        available: float,
        demands: Dict[str, float],
        priorities: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Allocate limited resource based on priority
        
        Args:
            available: Total available resource
            demands: Dict of {consumer: demand_amount}
            priorities: Dict of {consumer: priority_level} (higher = more important)
        
        Returns:
            Dict of {consumer: allocated_amount}
        """
        allocation = {}
        remaining = available
        
        # Sort consumers by priority (descending)
        sorted_consumers = sorted(
            demands.keys(),
            key=lambda x: priorities.get(x, 0),
            reverse=True
        )
        
        for consumer in sorted_consumers:
            demand = demands[consumer]
            allocated = min(demand, remaining)
            allocation[consumer] = allocated
            remaining -= allocated
            
            if remaining <= 0:
                break
        
        # Fill in zeros for consumers that didn't get allocation
        for consumer in demands:
            if consumer not in allocation:
                allocation[consumer] = 0.0
        
        return allocation


class SafetyLimits:
    """Hard safety limits for different units"""
    
    # Blast Furnace
    BF_WIND_MIN = 1000  # Nm³/min
    BF_WIND_MAX = 8000  # Nm³/min
    BF_O2_MAX = 6.0     # %
    BF_PCI_MAX = 200    # kg/t HM
    BF_TEMP_MAX = 1600  # °C
    BF_SI_MAX = 0.8     # %
    
    # BOF
    BOF_O2_MAX = 60000  # Nm³/h
    BOF_TEMP_MAX = 1750 # °C
    BOF_P_MAX = 15.0    # kPa
    
    # Coke Oven
    CO_TEMP_MAX = 1400  # °C
    CO_TEMP_MIN = 1000  # °C
    
    # Gas Holders
    GH_P_EMERGENCY = 16.0  # kPa
    GH_P_MIN = 8.0         # kPa
    GH_SOC_MIN = 0.05      # 5%
    GH_SOC_MAX = 0.95      # 95%
