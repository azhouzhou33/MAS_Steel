"""
Typed data models for Digital Twin inputs and outputs.
Replaces bare dictionaries with validated dataclasses.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


# =============================================================================
# BLAST FURNACE TWIN DATA MODELS
# =============================================================================

@dataclass
class BFInput:
    """Blast Furnace Twin input parameters"""
    ore: float  # t/h
    pellets: float  # t/h
    sinter: float  # t/h
    coke_mass_flow: float  # t/h
    coke_gas_flow: float  # m³/h
    calorific_value_coke_gas: float  # MJ/m³
    power: float  # kWh/h
    oxygen: float  # m³/h
    wind_volume: float  # Nm³/min - blast air volume
    intern_bf_gas_percentage: float  # %
    power_plant_bf_gas_percentage: float  # %
    slab_heat_furnace_bf_gas_percentage: float  # %
    coke_plant_bf_gas_percentage: float  # %
    
    def validate(self) -> bool:
        """Validate input ranges and constraints"""
        # Check percentage distribution sums to 100%
        percentages = (
            self.intern_bf_gas_percentage +
            self.power_plant_bf_gas_percentage +
            self.slab_heat_furnace_bf_gas_percentage +
            self.coke_plant_bf_gas_percentage
        )
        
        if abs(percentages - 100.0) > 0.01:
            return False
        
        # Check non-negative values
        if any(val < 0 for val in [
            self.ore, self.pellets, self.sinter, self.coke_mass_flow,
            self.coke_gas_flow, self.power, self.oxygen
        ]):
            return False
        
        return True
    
    def to_twin_dict(self) -> Dict[str, Any]:
        """Convert to format expected by legacy BF Twin"""
        return {
            "ore [t/h]": self.ore,
            "pellets [t/h]": self.pellets,
            "sinter [t/h]": self.sinter,
            "coke_mass_flow_bf4 [t/h]": self.coke_mass_flow,
            "coke_gas_coke_plant_bf4 [m³/h]": self.coke_gas_flow,
            "calorific_value_coke_gas_bf4 [MJ/m³]": self.calorific_value_coke_gas,
            "power [kWh/h]": self.power,
            "oxygen [m³/h]": self.oxygen,
            "wind_volume [Nm³/min]": self.wind_volume,
            "intern BF_GAS_PERCENTAGE [%]": self.intern_bf_gas_percentage,
            "power plant BF_GAS_PERCENTAGE [%]": self.power_plant_bf_gas_percentage,
            "slab heat furnace BF_GAS_PERCENTAGE [%]": self.slab_heat_furnace_bf_gas_percentage,
            "coke plant BF_GAS_PERCENTAGE [%]": self.coke_plant_bf_gas_percentage
        }


@dataclass
class BFOutput:
    """Blast Furnace Twin output results"""
    pig_iron_steelworks: float  # t/h
    bf_gas_power_plant: float  # m³/h
    bf_gas_intern: float  # m³/h
    bf_gas_slab_heat: float  # m³/h
    bf_gas_coke_plant: float  # m³/h
    total_co2_mass_flow: float  # t/h
    slag_mass_flow: float  # t/h
    electricity_own: float  # kW
    power_required: float  # kWh/h
    oxygen_required: float  # Nm³/h
    bf_gas_calorific_value: float  # MJ/m³
    bf_gas_total_flow: float  # m³/h
    t_hot_metal: float  # °C - hot metal temperature
    si_content: float  # % - silicon content
    
    @classmethod
    def from_twin_dict(cls, twin_output: Dict[str, Any]) -> 'BFOutput':
        """Create from legacy BF Twin output dictionary"""
        return cls(
            pig_iron_steelworks=twin_output.get("pig_iron_bf4_steelworks [t/h]", 0.0),
            bf_gas_power_plant=twin_output.get("bf_gas_bf4_power_plant [m³/h]", 0.0),
            bf_gas_intern=twin_output.get("bf_gas_bf4_intern [m³/h]", 0.0),
            bf_gas_slab_heat=twin_output.get("bf_gas_bf4_slab_heat [m³/h]", 0.0),
            bf_gas_coke_plant=twin_output.get("bf_gas_bf4_coke_plant [m³/h]", 0.0),
            total_co2_mass_flow=twin_output.get("bf4_total_co2_mass_flow [t/h]", 0.0),
            slag_mass_flow=twin_output.get("bf4_slag_mass_flow [t/h]", 0.0),
            electricity_own=twin_output.get("bf4_electricity_own [kW]", 0.0),
            power_required=twin_output.get("power_required [kWh/h]", 0.0),
            oxygen_required=twin_output.get("oxygen_required [Nm³/h]", 0.0),
            bf_gas_calorific_value=twin_output.get("bf_gas_bf4_calorific_value [MJ/m³]", 0.0),
            bf_gas_total_flow=twin_output.get("bf_gas_total_flow [m³/h]", 0.0),
            t_hot_metal=twin_output.get("T_hot_metal [°C]", 1500.0),
            si_content=twin_output.get("Si [%]", 0.5)
        )


# =============================================================================
# BOF TWIN DATA MODELS
# =============================================================================

@dataclass
class BOFInput:
    """BOF Twin input parameters"""
    pig_iron: float  # t/h
    scrap_steel: float  # t/h
    oxygen: float  # Nm³/h
    lime: float  # t/h
    power: float  # kWh/h
    
    def validate(self) -> bool:
        """Validate input ranges"""
        return all(val >= 0 for val in [
            self.pig_iron, self.scrap_steel, self.oxygen, self.lime, self.power
        ])
    
    def to_twin_dict(self) -> Dict[str, Any]:
        """Convert to format expected by legacy BOF Twin"""
        return {
            "pig_iron [t/h]": self.pig_iron,
            "scrap_steel [t/h]": self.scrap_steel,
            "oxygen [Nm³/h]": self.oxygen,
            "lime [t/h]": self.lime,
            "power [kWh/h]": self.power
        }


@dataclass
class BOFOutput:
    """BOF Twin output results"""
    liquid_steel: float  # t/h
    bof_gas: float  # Nm³/h
    co2_emissions: float  # t/h
    slag: float  # t/h
    
    @classmethod
    def from_twin_dict(cls, twin_output: Dict[str, Any]) -> 'BOFOutput':
        """Create from legacy BOF Twin output dictionary"""
        return cls(
            liquid_steel=twin_output.get("liquid_steel [t/h]", 0.0),
            bof_gas=twin_output.get("bof_gas [Nm³/h]", 0.0),
            co2_emissions=twin_output.get("co2_emissions [t/h]", 0.0),
            slag=twin_output.get("slag [t/h]", 0.0)
        )


# =============================================================================
# COKE OVEN TWIN DATA MODELS
# =============================================================================

@dataclass
class CokeOvenInput:
    """Coke Oven Twin input parameters"""
    coal_input: float  # t/h
    heating_gas: float  # Nm³/h
    heating_gas_calorific_value: float  # MJ/Nm³
    steam: float  # t/h
    power: float  # kWh/h
    
    def validate(self) -> bool:
        """Validate input ranges"""
        return all(val >= 0 for val in [
            self.coal_input, self.heating_gas, self.heating_gas_calorific_value,
            self.steam, self.power
        ])
    
    def to_twin_dict(self) -> Dict[str, Any]:
        """Convert to format expected by legacy Coke Oven Twin"""
        return {
            "coal_input [t/h]": self.coal_input,
            "heating_gas [Nm³/h]": self.heating_gas,
            "heating_gas_calorific_value [MJ/Nm³]": self.heating_gas_calorific_value,
            "steam [t/h]": self.steam,
            "power [kWh/h]": self.power
        }


@dataclass
class CokeOvenOutput:
    """Coke Oven Twin output results"""
    coke_production: float  # t/h
    cog_production: float  # Nm³/h
    tar: float  # t/h
    ammonia_liquor: float  # t/h
    co2_emissions: float  # t/h
    
    @classmethod
    def from_twin_dict(cls, twin_output: Dict[str, Any]) -> 'CokeOvenOutput':
        """Create from legacy Coke Oven Twin output dictionary"""
        return cls(
            coke_production=twin_output.get("coke_production [t/h]", 0.0),
            cog_production=twin_output.get("cog_production [Nm³/h]", 0.0),
            tar=twin_output.get("tar [t/h]", 0.0),
            ammonia_liquor=twin_output.get("ammonia_liquor [t/h]", 0.0),
            co2_emissions=twin_output.get("co2_emissions [t/h]", 0.0)
        )


# =============================================================================
# GAS HOLDER DATA MODELS
# =============================================================================

@dataclass
class GasHolderInput:
    """Gas Holder State-Space Model input"""
    gas_net_flow: float  # Nm³/h
    
    def to_twin_dict(self) -> Dict[str, Any]:
        """Convert to format expected by Gas Holder models"""
        return {
            "gas_net_flow": self.gas_net_flow
        }


@dataclass
class GasHolderOutput:
    """Gas Holder State-Space Model output"""
    level: float  # Normalized level [0-1]
    soc: float  # State of Charge [0-1]
    pressure: float  # kPa
    
    @classmethod
    def from_twin_dict(cls, twin_output: Dict[str, Any], soc: float, pressure: float) -> 'GasHolderOutput':
        """Create from Gas Holder model output"""
        return cls(
            level=twin_output.get("level", 0.5),
            soc=soc,
            pressure=pressure
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_all_inputs(*inputs) -> bool:
    """Validate multiple input objects at once"""
    return all(inp.validate() for inp in inputs if hasattr(inp, 'validate'))
