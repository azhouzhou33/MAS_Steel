"""
Standard Interface Adapters - Extension to twin_translator.py

These functions convert between StandardState/Action and Twin formats.
This file should be appended to the existing twin_translator.py
"""

# ===== STANDARD INTERFACE ADAPTERS (NEW) =====

def twin_outputs_to_standard_state(
    twin_outputs: Dict[str, Dict[str, Any]],
    gas_network_state: Dict[str, float],
    time: int
) -> StandardState:
    """
    Convert raw Twin outputs + gas network state → StandardState
    
    Args:
        twin_outputs: Dict with keys "BF", "BOF", "Coke" containing Twin outputs
        gas_network_state: Current gas holder states (SOC, pressure)
        time: Current simulation step
    
    Returns:
        StandardState object with unified representation
    """
    from models.standard_interfaces import (
        StandardState, GasHolderState, ProductionState, DemandState
    )
    
    # Extract gas holder state
    gas_holder = GasHolderState(
        soc_bfg=gas_network_state.get("soc_bfg", 0.5),
        soc_bofg=gas_network_state.get("soc_bofg", 0.5),
        soc_cog=gas_network_state.get("soc_cog", 0.5),
        p_bfg=gas_network_state.get("p_bfg", 12.0),
        p_bofg=gas_network_state.get("p_bofg", 12.0),
        p_cog=gas_network_state.get("p_cog", 12.0),
    )
    
    # Extract production state from Twin outputs
    bf_out = twin_outputs.get("BF", {})
    bof_out = twin_outputs.get("BOF", {})
    coke_out = twin_outputs.get("Coke", {})
    
    production = ProductionState(
        bf_bfg_supply=bf_out.get("bf_gas_total_flow [m³/h]", 0.0),
        bf_t_hot_metal=bf_out.get("T_hot_metal [°C]", 1500.0),
        bf_si_content=bf_out.get("Si [%]", 0.45),
        bof_bofg_supply=bof_out.get("bof_gas [Nm³/h]", 0.0),
        coke_cog_supply=coke_out.get("cog_production [Nm³/h]", 0.0),
    )
    
    # Extract demand state (simplified - currently from gas network state)
    demand = DemandState(
        power_plant_demand=gas_network_state.get("power_plant_demand", 50000.0),
        heating_demand=gas_network_state.get("heating_demand", 20000.0),
        priority_level=gas_network_state.get("priority_level", 0.5),
    )
    
    return StandardState(
        time=time,
        gas_holder=gas_holder,
        production=production,
        demand=demand
    )


def standard_action_to_twin_inputs(
    action: StandardAction,
    current_state: StandardState
) -> Dict[str, Dict[str, Any]]:
    """
    Convert StandardAction → Twin input dictionaries
    
    Args:
        action: StandardAction with gas_allocation and production_control
        current_state: Current StandardState (for context)
    
    Returns:
        Dict with keys "BF", "BOF", "Coke" containing Twin input dicts
    """
    prod_ctrl = action.production_control
    gas_alloc = action.gas_allocation
    
    # Prepare BF Twin inputs
    bf_inputs = {
        "ore [t/h]": 50,
        "pellets [t/h]": 100,
        "sinter [t/h]": 100,
        "coke_mass_flow_bf4 [t/h]": prod_ctrl.bf_pci / 1.5,
        "coke_gas_coke_plant_bf4 [m³/h]": max(min(gas_alloc.cog_to_bf, 8000), 1000),
        "calorific_value_coke_gas_bf4 [MJ/m³]": 18.0,
        "power [kWh/h]": 50000,
        "wind_volume [Nm³/min]": prod_ctrl.bf_wind_volume,
        "oxygen_enrichment [Nm³/h]": 0,  # Calculated from O2 enrichment %
        "intern BF_GAS_PERCENTAGE [%]": 50,
        "power plant BF_GAS_PERCENTAGE [%]": 20,
        "slab heat furnace BF_GAS_PERCENTAGE [%]": 20,
        "coke plant BF_GAS_PERCENTAGE [%]": 10
    }
    
    # Prepare BOF Twin inputs
    bof_inputs = {
        "pig_iron [t/h]": 80,
        "scrap_steel [t/h]": prod_ctrl.bof_scrap_steel,
        "oxygen [Nm³/h]": prod_ctrl.bof_oxygen,
        "lime [t/h]": 5,
        "power [kWh/h]": 5000
    }
    
    # Prepare Coke Oven Twin inputs
    coke_inputs = {
        "coal_input [t/h]": 100,
        "heating_gas [Nm³/h]": prod_ctrl.coke_heating_gas,
        "heating_gas_calorific_value [MJ/Nm³]": 4.5,
        "steam [t/h]": 2,
        "power [kWh/h]": 3000
    }
    
    return {
        "BF": bf_inputs,
        "BOF": bof_inputs,
        "Coke": coke_inputs
    }


def legacy_state_to_standard_state(
    legacy_state: Dict[str, Any],
    time: int
) -> StandardState:
    """
    Convert legacy dict-based state → StandardState (for backward compatibility)
    
    Args:
        legacy_state: Old-style state dictionary
        time: Current step
    
    Returns:
        StandardState object
    """
    from models.standard_interfaces import (
        StandardState, GasHolderState, ProductionState, DemandState
    )
    
    gas_holder = GasHolderState(
        soc_bfg=legacy_state.get("soc_bfg", 0.5),
        soc_bofg=legacy_state.get("soc_bofg", 0.5),
        soc_cog=legacy_state.get("soc_cog", 0.5),
        p_bfg=legacy_state.get("p_bfg", 12.0),
        p_bofg=legacy_state.get("p_bofg", 12.0),
        p_cog=legacy_state.get("p_cog", 12.0),
    )
    
    production = ProductionState(
        bf_bfg_supply=legacy_state.get("bfg_supply", 0.0),
        bf_t_hot_metal=legacy_state.get("T_hot_metal", 1500.0),
        bf_si_content=legacy_state.get("Si", 0.45),
        bof_bofg_supply=legacy_state.get("bofg_supply", 0.0),
        coke_cog_supply=legacy_state.get("cog_supply", 0.0),
    )
    
    demand = DemandState(
        power_plant_demand=50000.0,  # Default values
        heating_demand=20000.0,
        priority_level=0.5,
    )
    
    return StandardState(
        time=time,
        gas_holder=gas_holder,
        production=production,
        demand=demand
    )


def standard_state_to_legacy_state(state: StandardState) -> Dict[str, Any]:
    """
    Convert StandardState → legacy dict format (for backward compatibility)
    
    Args:
        state: StandardState object
    
    Returns:
        Legacy-style state dictionary
    """
    return {
        "soc_bfg": state.gas_holder.soc_bfg,
        "soc_bofg": state.gas_holder.soc_bofg,
        "soc_cog": state.gas_holder.soc_cog,
        "p_bfg": state.gas_holder.p_bfg,
        "p_bofg": state.gas_holder.p_bofg,
        "p_cog": state.gas_holder.p_cog,
        "bfg_supply": state.production.bf_bfg_supply,
        "T_hot_metal": state.production.bf_t_hot_metal,
        "Si": state.production.bf_si_content,
        "bofg_supply": state.production.bof_bofg_supply,
        "cog_supply": state.production.coke_cog_supply,
        "COG_available": state.production.coke_cog_supply,
        "O2_available": 50000,  # Default
        "peak_electricity": False,
    }
