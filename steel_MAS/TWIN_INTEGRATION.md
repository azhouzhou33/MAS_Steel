"""
Digital Twin Integration Guide for MAS
Shows how agent actions map to twin inputs and outputs
"""

# =============================================================================
# INTEGRATION ARCHITECTURE
# =============================================================================

"""
Agent Actions → Twin Inputs → Twin Calculation → Twin Outputs → Environment State

Flow:
1. Agents decide actions based on observations
2. Environment maps actions to twin-specific inputs
3. Twins compute outputs using their internal models
4. Environment updates state from twin outputs
5. Updated state becomes new observations for agents
"""

# =============================================================================
# 1. BLAST FURNACE TWIN INTEGRATION
# =============================================================================

"""
Agent Actions (from BF_Agent):
- wind_volume [Nm³/min]
- O2_enrichment [%]
- PCI [kg/t HM]
- COG_ratio [fraction]

Mapped to BF Twin Inputs:
{
    "ore [t/h]": 50,
    "pellets [t/h]": 100,
    "sinter [t/h]": 100,
    "coke_mass_flow_bf4 [t/h]": PCI / 1.5,  # Mapping
    "coke_gas_coke_plant_bf4 [m³/h]": COG_available,
    "oxygen [m³/h]": O2_enrichment * wind_volume * 10,
    ...
}

BF Twin Outputs → Environment State:
- pig_iron_bf4_steelworks [t/h] → state["pig_iron_production"]
- bf_gas_total_flow [m³/h] → state["bfg_supply"]
- bf4_total_co2_mass_flow [t/h] → state["co2_emissions"]
"""

# =============================================================================
# 2. BOF TWIN INTEGRATION
# =============================================================================

"""
Agent Actions (from BOF_Agent):
- oxygen [Nm³/h]
- scrap_steel [t/batch]

Mapped to BOF Twin Inputs:
{
    "pig_iron [t/h]": min(state["pig_iron_production"], 80),
    "scrap_steel [t/h]": scrap_steel,
    "oxygen [Nm³/h]": oxygen,
    "lime [t/h]": 5,
    "power [kWh/h]": 5000
}

BOF Twin Outputs → Environment State:
- liquid_steel [t/h] → state["liquid_steel"]
- bof_gas [Nm³/h] → state["bofg_supply"]
- co2_emissions [t/h] → state["co2_bof"]
"""

# =============================================================================
# 3. COKE OVEN TWIN INTEGRATION
# =============================================================================

"""
Agent Actions (from CokeOven_Agent):
- heating_gas_input [Nm³/h]
- pushing_rate [relative]

Mapped to Coke Oven Twin Inputs:
{
    "coal_input [t/h]": 100,
    "heating_gas [Nm³/h]": heating_gas_input,
    "heating_gas_calorific_value [MJ/Nm³]": 4.5,
    "steam [t/h]": 2,
    "power [kWh/h]": 3000
}

Coke Oven Twin Outputs → Environment State:
- coke_production [t/h] → state["coke_production"]
- cog_production [Nm³/h] → state["cog_supply"]
- tar [t/h], ammonia_liquor [t/h] → state["byproducts"]
"""

# =============================================================================
# 4. GAS HOLDER TWIN INTEGRATION (State-Space Models)
# =============================================================================

"""
Agent Actions (from GasHolder_Agent):
- bfg_to_pp [Nm³/h]
- bfg_to_heating [Nm³/h]
- bofg_to_pp, bofg_to_heating, cog_to_heating, cog_to_bf

Calculation:
net_flow = production - consumption

Mapped to Gas Holder Twin Inputs (BFGH, BOFGH, COGH):
{
    "gas_net_flow": bfg_production - (bfg_to_pp + bfg_to_heating)
}

Gas Holder Twins use State-Space Models:
x_{k+1} = A * x_k + B * u_k
y_k = C * x_k

Outputs update:
- SOC (State of Charge) [0-1]
- Pressure [kPa]
"""

# =============================================================================
# KEY INTEGRATION POINTS IN CODE
# =============================================================================

"""
File: steel_MAS/env/mas_sim_env.py

Method: _step_with_twins()
Lines: ~126-235

This method:
1. Takes agent actions as input
2. Maps to twin-specific input formats
3. Calls twin models: bf_twin(), bof_twin(), co_twin(), bfgh(), etc.
4. Extracts outputs and updates self.state{}
5. Returns state as observations for next agent step

Run with twins enabled:
env = MAS_SimEnv(use_twins=True)  # in main.py
"""

# =============================================================================
# EXAMPLE: One Simulation Step
# =============================================================================

"""
Step 1: BF Agent observes SOC_BFG = 0.90 (too full)
        → Reduces wind_volume to 3800 Nm³/min

Step 2: Environment maps to BF twin:
        → oxygen [m³/h] = 3.5 * 3800 * 10 = 133000

Step 3: BF Twin calculates:
        → pig_iron_production = 190 t/h
        → bfg_supply = 95000 Nm³/h (less gas!)

Step 4: GasHolder Agent increases consumption:
        → bfg_to_pp = 55000 Nm³/h

Step 5: Gas Holder Twin calculates:
        → net_flow = 95000 - 55000 - 30000 = 10000 Nm³/h (positive but smaller)
        → SOC trends down toward normal range
"""
