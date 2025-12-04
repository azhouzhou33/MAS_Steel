# Author: Digital Twin Implementation
# Coke Oven Digital Twin Model

class CokeOvenTwin:
    def __init__(self, **params):
        """Initialize the Coke Oven twin with user-defined parameters."""
        self.params = params
    
    def default_inputs(self):
        """Returns default input values for Coke Oven operation."""
        return {
            # Input materials
            "coal_input [t/h]": 100,                    # Coal feed rate
            "heating_gas [Nm³/h]": 15000,               # Heating gas (BFG/COG mix)
            "heating_gas_calorific_value [MJ/Nm³]": 4.5,  # Heating gas energy content
            "steam [t/h]": 2,                           # Steam for process
            "power [kWh/h]": 3000,                      # Electrical power
        }
    
    def __call__(self, inputs):
        return self.simulate(inputs)
    
    def __call__(self, inputs: dict) -> dict:
        """Callable version with type hints."""
        
        # Extract input parameters with defaults
        coal_input = inputs.get("coal_input [t/h]", 100)
        heating_gas = inputs.get("heating_gas [Nm³/h]", 15000)
        heating_gas_cv = inputs.get("heating_gas_calorific_value [MJ/Nm³]", 4.5)
        steam = inputs.get("steam [t/h]", 2)
        power = inputs.get("power [kWh/h]", 3000)
        
        # Fixed calculation parameters (per ton of coal)
        coke_yield = 0.72               # 72% coke yield from coal (typical)
        cog_per_coal = 330              # [Nm³/t_coal] - COG generation
        tar_per_coal = 0.03             # [t_tar/t_coal] - tar yield
        ammonia_per_coal = 0.003        # [t_ammonia/t_coal] - ammonia yield
        co2_factor = 0.08               # [t_CO2/t_coal] - CO2 emissions
        
        heating_requirement = 1.5e3     # [MJ/t_coal] - heating energy needed
        power_per_coal = 30             # [kWh/t_coal] - power requirement
        steam_per_coal = 0.02           # [t_steam/t_coal] - steam requirement
        
        # Calculate theoretical coke production
        coke_theoretical = round(coal_input * coke_yield, 2)
        
        # Check heating gas requirement
        heating_energy_available = heating_gas * heating_gas_cv
        heating_energy_required = round(heating_requirement * coal_input, 2)
        heating_ratio = min(1.0, heating_energy_available / heating_energy_required) if heating_energy_required > 0 else 0
        
        # Adjust production based on heating availability
        coal_processed_heating = round(coal_input * heating_ratio, 2)
        
        # Check steam requirement
        steam_required = round(steam_per_coal * coal_processed_heating, 2)
        steam_used = steam if steam <= steam_required else steam_required
        steam_ratio = steam_used / steam_required if steam_required > 0 else 0
        
        # Adjust production based on steam availability
        coal_processed_steam = round(coal_processed_heating * steam_ratio, 2)
        
        # Check power requirement
        power_required = round(power_per_coal * coal_processed_steam, 2)
        power_used = power if power <= power_required else power_required
        power_ratio = power_used / power_required if power_required > 0 else 0
        
        # Final coal processed and outputs
        coal_processed = round(coal_processed_steam * power_ratio, 2)
        
        # Calculate final outputs
        coke_production = round(coal_processed * coke_yield, 2)
        cog_production = round(coal_processed * cog_per_coal, 2)
        tar_production = round(coal_processed * tar_per_coal, 2)
        ammonia_production = round(coal_processed * ammonia_per_coal, 2)
        co2_emissions = round(coal_processed * co2_factor, 2)
        
        # COG calorific value (typically 17-19 MJ/Nm³)
        cog_calorific_value = round(17.5 + 0.005 * coal_processed, 2)
        
        # Recalculate actual requirements for output
        heating_gas_actual = round(heating_requirement * coal_processed / heating_gas_cv, 2) if heating_gas_cv > 0 else 0
        steam_actual = round(steam_per_coal * coal_processed, 2)
        power_actual = round(power_per_coal * coal_processed, 2)
        
        # Return output parameters
        return {
            "coke_production [t/h]": coke_production,
            "cog_production [Nm³/h]": cog_production,
            "cog_calorific_value [MJ/Nm³]": cog_calorific_value,
            "tar [t/h]": tar_production,
            "ammonia_liquor [t/h]": ammonia_production,
            "co2_emissions [t/h]": co2_emissions,
            "heating_gas_required [Nm³/h]": heating_gas_actual,
            "steam_required [t/h]": steam_actual,
            "power_required [kWh/h]": power_actual,
            "coal_processed [t/h]": coal_processed
        }


# Test execution
if __name__ == "__main__":
    model = CokeOvenTwin()
    result = model({
        "coal_input [t/h]": 100,
        "heating_gas [Nm³/h]": 15000,
        "heating_gas_calorific_value [MJ/Nm³]": 4.5,
        "steam [t/h]": 2,
        "power [kWh/h]": 3000
    })
    
    print("Coke Oven Digital Twin - Test Results:")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key}: {value}")
