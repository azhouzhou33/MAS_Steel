# Author: Digital Twin Implementation
# BOF (Basic Oxygen Furnace) Digital Twin Model

class BOFTwin:
    def __init__(self, **params):
        """Initialize the BOF twin with user-defined parameters."""
        self.params = params
    
    def default_inputs(self):
        """Returns default input values for BOF operation."""
        return {
            # Input materials
            "pig_iron [t/h]": 80,           # Molten pig iron from blast furnace
            "scrap_steel [t/h]": 20,        # Scrap steel for cooling/dilution
            "oxygen [Nm³/h]": 5000,         # Oxygen for decarburization
            "lime [t/h]": 5,                # Lime flux for slag formation
            "power [kWh/h]": 5000,          # Electrical power consumption
        }
    
    def __call__(self, inputs):
        return self.simulate(inputs)
    
    def __call__(self, inputs: dict) -> dict:
        """Callable version with type hints."""
        
        # Extract input parameters with defaults
        pig_iron = inputs.get("pig_iron [t/h]", 80)
        scrap_steel = inputs.get("scrap_steel [t/h]", 20)
        oxygen = inputs.get("oxygen [Nm³/h]", 5000)
        lime = inputs.get("lime [t/h]", 5)
        power = inputs.get("power [kWh/h]", 5000)
        
        # Fixed calculation parameters (per ton of steel)
        oxygen_tSteel = 50          # [Nm³/t_steel] - oxygen requirement
        lime_tSteel = 50            # [kg/t_steel] - lime requirement
        power_tSteel = 50           # [kWh/t_steel] - power requirement
        slag_ratio = 0.15           # [t_slag/t_steel] - slag generation ratio
        bof_gas_tSteel = 60         # [Nm³/t_steel] - BOF gas generation
        co2_factor = 0.15           # [t_CO2/t_steel] - CO2 emissions factor
        
        # Calculate theoretical steel production from iron sources
        # Assume ~95% yield from pig iron and scrap
        steel_from_iron = round((pig_iron + scrap_steel) * 0.95, 2)
        
        # Check oxygen requirement
        oxygen_required = round(oxygen_tSteel * steel_from_iron, 2)
        oxygen_used = oxygen if oxygen <= oxygen_required else oxygen_required
        
        # Adjust steel production based on oxygen availability
        steel_after_oxygen = round(steel_from_iron * (oxygen_used / oxygen_required), 2)
        
        # Check lime requirement
        lime_required = round((lime_tSteel * steel_after_oxygen) / 1000, 2)
        lime_used = lime if lime <= lime_required else lime_required
        
        # Adjust steel production based on lime availability
        steel_after_lime = round(steel_after_oxygen * (lime_used / lime_required), 2)
        
        # Check power requirement
        power_required = round(power_tSteel * steel_after_lime, 2)
        power_used = power if power <= power_required else power_required
        
        # Final steel production based on all constraints
        liquid_steel = round(steel_after_lime * (power_used / power_required), 2)
        
        # Calculate outputs based on final steel production
        bof_slag = round(slag_ratio * liquid_steel, 2)
        bof_gas_volume = round(bof_gas_tSteel * liquid_steel, 2)
        co2_emissions = round(co2_factor * liquid_steel, 2)
        
        # BOF gas calorific value (CO-rich gas, ~8-10 MJ/Nm³)
        # Varies slightly with production rate
        bof_gas_calorific_value = round(8.0 + 0.01 * liquid_steel, 2)
        
        # Recalculate actual requirements for output
        oxygen_actual = round(oxygen_tSteel * liquid_steel, 2)
        power_actual = round(power_tSteel * liquid_steel, 2)
        lime_actual = round((lime_tSteel * liquid_steel) / 1000, 2)
        
        # Return output parameters
        return {
            "liquid_steel [t/h]": round(liquid_steel, 2),
            "bof_slag [t/h]": bof_slag,
            "bof_gas [Nm³/h]": bof_gas_volume,
            "bof_gas_calorific_value [MJ/Nm³]": bof_gas_calorific_value,
            "co2_emissions [t/h]": co2_emissions,
            "oxygen_required [Nm³/h]": oxygen_actual,
            "power_required [kWh/h]": power_actual,
            "lime_required [t/h]": lime_actual
        }


# Test execution
if __name__ == "__main__":
    model = BOFTwin()
    result = model({
        "pig_iron [t/h]": 80,
        "scrap_steel [t/h]": 20,
        "oxygen [Nm³/h]": 5000,
        "lime [t/h]": 5,
        "power [kWh/h]": 5000
    })
    
    print("BOF Digital Twin - Test Results:")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}: {value}")
