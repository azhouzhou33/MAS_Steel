#Author: Jonas van Bracht @BFI - jonas.van-bracht@bfi.de
#Please contact me directly if you have any questions.

#Upfront: This script already includes safeguards to ensure that implausible values (too high) do not influence the calculation. The lower limit is 0.

class BlastFurnaceTwin: #Name of the twin to be called up in the multi-agent system
    def __init__(self, **params): #Initialises the class with user-defined parameters.
        self.params = params #All arguments are stored in the 'params' dictionary.
        

    def default_inputs(self): #Returns a dictionary containing the default input values, used if no specific inputs are provided by the user in the multi-agent system.
        return {
            #These are the default values for each parameter that can be entered.
            "ore [t/h]":50,
            "pellets [t/h]":100,
            "sinter [t/h]":100,
            "coke_mass_flow_bf4 [t/h]":100,
            "coke_gas_coke_plant_bf4 [m³/h]":20000,
            "calorific_value_coke_gas_bf4 [MJ/m³]":20,
            "power [kWh/h]":50000,
            "oxygen [m³/h]":50000,
            "wind_volume [Nm³/min]":4000,  # Blast air volume
            #In the first step, we defined the distribution of blast furnace gas (output) as an input parameter.
            #Further down in the code, there is a check function that sets all output parameters to zero if the percentage distribution deviates from 100%.
            "intern BF_GAS_PERCENTAGE [%]":50,
            "power plant BF_GAS_PERCENTAGE [%]":20,
            "slab heat furnace BF_GAS_PERCENTAGE [%]":20,
            "coke plant BF_GAS_PERCENTAGE [%]": 10
        }

    def __call__(self, inputs):
        return self.simulate(inputs)  #Makes the class instance callable like a function. When called with an input dictionary, it executes the 'simulate' method in the multi-agent system.

    def __call__(self, inputs: dict) -> dict: #Callable version with type hints. Expects a dictionary as input and returns a dictionary as output.

        #Here, the values entered, e.g. 'ore [t/h]', are defined as variables, e.g. ore.
        #The variable is used for calculations in the rest of the code.
        #The label with the unit is displayed in the current multi-agent system so that the user knows which parameter to specify in which unit.
        ore = inputs.get("ore [t/h]", 50) #Here, additional default values are specified, only this time for the variables in the code.
        pellets = inputs.get("pellets [t/h]", 100)
        sinter = inputs.get("sinter [t/h]", 100)
        coke_coke_plant_bf4 = inputs.get("coke_mass_flow_bf4 [t/h]", 100)
        coke_gas_coke_plant_bf4 = inputs.get("coke_gas_coke_plant_bf4 [m³/h]", 20000)
        calorific_value_coke_gas = inputs.get("calorific_value_coke_gas_bf4 [MJ/m³]", 20)
        power = inputs.get("power [kWh/h]", 50000)
        bf_gas_bf4_percentage_intern = inputs.get("intern BF_GAS_PERCENTAGE [%]", 50)
        bf_gas_bf4_percentage_power_plant = inputs.get("power plant BF_GAS_PERCENTAGE [%]", 20)
        bf_gas_bf4_percentage_slab_heat_furnace = inputs.get("slab heat furnace BF_GAS_PERCENTAGE [%]", 20)
        bf_gas_bf4_percentage_coke_plant = inputs.get("coke plant BF_GAS_PERCENTAGE [%]", 10)
        
        # NEW: Wind-based oxygen calculation
        wind_volume = inputs.get("wind_volume [Nm³/min]", 4000)  # Blast air volume
        # Air contains 21% O2 by volume
        O2_from_wind = 0.21 * wind_volume * 60  # Convert Nm³/min to Nm³/h
        # Oxygen enrichment (if provided separately, otherwise use wind-based O2)
        oxygen_enrichment = inputs.get("oxygen_enrichment [Nm³/h]", 0)
        # Total oxygen = base O2 from air + enrichment
        oxygen = O2_from_wind + oxygen_enrichment

        #The fixed calculation parameters are specified here. These have the unit resource per tonne of pig iron.
        ore_tPI = 1000  #[kg/t_pig_iron]
        pellets_tPI = 1000  #[kg/t_pig_iron]
        sinter_tPI = 1000  #[kg/t_pig_iron]
        coke_tPI = 500  #[kg/t_pig_iron]
        coke_gas_tPI = 1000  #[MJ/t_pig_iron]
        power_tPI = 100  #[kWh/t_pig_iron]
        oxygen_tPI = 100  #[Nm³/t_pig_iron]
        #With one small exception here, to get to the masses of CO2.
        co2_cog = 1 #[kgCO2/m^3 COG]

        #The first step here is to calculate how much pig iron can be produced based on the quantity of ore, pellets and sinter supplied.
        pig_iron_bf4_subtotal = round(((ore * 1000) / ore_tPI + (pellets * 1000) / pellets_tPI + (sinter * 1000) / sinter_tPI), 2)

        #Checking how much coke is needed to produce the calculated amount of pig iron.
        coke_required = round((coke_tPI * pig_iron_bf4_subtotal) / 1000,2)

        #Check whether the actual amount of coke transferred is sufficient to cover the required coke.
        #If a higher amount than the required amount is fed into the blast furnace twin, only the required amount is used.
        #If less coke is fed into the blast furnace, this value is used for further calculation.
        coke_used = coke_coke_plant_bf4 if coke_coke_plant_bf4 <= coke_required else coke_required


        #The quantity of pig iron produced is calculated based on the coke used.
        #Here, the quantity of coke used has a direct influence on the pig iron output parameter.
        pig_iron_bf4_steelworks_coke = round(((ore * 1000) / ore_tPI + (pellets * 1000) / pellets_tPI + (sinter * 1000) / sinter_tPI) * (coke_used / coke_required), 2)

        #Calculation of self-generated electricity based on a calculation formula, which was generated from process data.
        #The amount of self-generated electricity depends on the amount of pig iron produced.
        bf4_electricity_own = round(10 * pig_iron_bf4_steelworks_coke+5000, 2)

        #Calculation of the additional amount of electricity required to operate the blast furnace.
        power_required = round(power_tPI * pig_iron_bf4_steelworks_coke - bf4_electricity_own,2)

        #Check whether the quantity supplied is sufficient for pig iron production, otherwise lower value and reduction in production.
        power_used = power if power <= power_required else power_required

        #The amount of pig iron produced is calculated again based on the amount of electricity supplied.
        pig_iron_bf4_steelworks_coke_power = round(((ore * 1000) / ore_tPI + (pellets * 1000) / pellets_tPI + (sinter * 1000) / sinter_tPI) * (coke_used / coke_required) * (power_used / power_required), 2)

        #Calculation of the required amount of oxygen (O2)
        oxygen_required = round(oxygen_tPI * pig_iron_bf4_steelworks_coke_power, 2)

        #Check whether the quantity supplied is sufficient for pig iron production, otherwise lower value and reduction in production.
        oxygen_used = oxygen if oxygen <= oxygen_required else oxygen_required

        #Calculation of the energy flow from coke gas
        energy_flow_coke_gas_in = coke_gas_coke_plant_bf4 * calorific_value_coke_gas

        #Calculation of how much coke gas is needed for pig iron production
        energy_flow_coke_gas_required = round(pig_iron_bf4_steelworks_coke_power * coke_gas_tPI, 2)

        # NEW: COG combustion limited by available air (wind)
        # COG needs air for combustion - stoichiometric constraint
        wind_volume_hourly = wind_volume * 60  # Convert to Nm³/h
        max_cog_by_wind = wind_volume_hourly * 5.0  # Empirical factor: max COG per unit wind
        
        #Check whether the amount of coke gas introduced is sufficient and within wind constraints
        coke_gas_used = min(energy_flow_coke_gas_in, energy_flow_coke_gas_required, max_cog_by_wind)

        #Recalculation of how much pig iron can be produced based on the parameters coke, power, oxygen and coke gas.
        # FIXED: Safety check to avoid division by zero
        if energy_flow_coke_gas_required > 0:
            cog_factor = coke_gas_used / energy_flow_coke_gas_required
        else:
            cog_factor = 1.0  # If no COG required, assume full production capability
        
        pig_iron_bf4_steelworks = round(((ore * 1000) / ore_tPI + (pellets * 1000) / pellets_tPI + (sinter * 1000) / sinter_tPI) * (coke_used / coke_required) * (power_used / power_required) * (oxygen_used / oxygen_required) * cog_factor, 2)

        # NEW: Thermal balance calculation
        # Heat inputs: wind + COG + coke
        # Higher heat → higher T_hot_metal → lower Si
        heat_from_wind = wind_volume * 0.3  # Relative heat contribution from blast air
        heat_from_cog = coke_gas_used * 0.001  # Heat from COG combustion
        heat_from_coke = coke_used * 15  # High calorific value from coke
        
        total_heat_index = heat_from_wind + heat_from_cog + heat_from_coke
        baseline_heat = 5000  # Nominal operating point
        
        # Temperature: increases with heat input
        T_hot_metal = round(1450 + (total_heat_index - baseline_heat) * 0.05, 1)
        T_hot_metal = max(1400, min(1550, T_hot_metal))  # Clamp to realistic range
        
        # Si content: decreases as temperature increases (inverse relationship)
        si_baseline = 0.5  # % at nominal conditions
        si_content = round(si_baseline - (T_hot_metal - 1500) * 0.002, 3)
        si_content = max(0.2, min(0.8, si_content))  # Clamp to realistic range

        # FIXED: Wind-based BFG production with realistic coefficients
        # BFG is primarily produced from air blown through the furnace
        # Empirical formula: BFG ∝ wind_volume (not pig_iron)
        # Realistic coefficients for steel plant scale:
        #   - Wind = 4000 Nm³/min = 240,000 Nm³/h
        #   - BFG should be 100,000-200,000 Nm³/h (1:2-1:1 ratio to wind)
        #   - α=0.4, β=20000 gives ~116,000 Nm³/h at nominal wind
        total_bf_gas_volume_flow_bf4 = round(0.4 * wind_volume_hourly + 20000, 2)

        #Calculation of the absolute values of blast furnace gas for internal use, power plant, slab heat and coke plant.
        #In this version of the twin, the percentage distribution is entered manually (input).
        bf_gas_bf4_intern = round(bf_gas_bf4_percentage_intern / 100 * total_bf_gas_volume_flow_bf4, 2)
        bf_gas_bf4_power_plant = round(bf_gas_bf4_percentage_power_plant / 100 * total_bf_gas_volume_flow_bf4, 2)
        bf_gas_bf4_slab_heat = round(bf_gas_bf4_percentage_slab_heat_furnace / 100 * total_bf_gas_volume_flow_bf4, 2)
        bf_gas_bf4_coke_plant = round(bf_gas_bf4_percentage_coke_plant / 100 * total_bf_gas_volume_flow_bf4, 2)

        #Calculation of the CO2 mass flow as a function of the quantity of pig iron produced.
        bf4_total_co2_mass_flow = round((total_bf_gas_volume_flow_bf4 / 1000 + coke_gas_coke_plant_bf4 * co2_cog),2)

        #Calculation of the amount of slag depending on the amount of pig iron produced.
        bf4_slag_mass_flow = round(pig_iron_bf4_steelworks, 2)

        #Calculation of the calorific value depending on the quantity of pig iron produced or the quantity of blast furnace gas produced.
        bf_gas_bf4_calorific_value = round(0.01 * pig_iron_bf4_steelworks, 2)

        #Since blast furnace gas is transferred to three twins, the calorific value must also be transferred in addition to the volume flows.
        #Therefore, three variables with the same value are defined here.
        bf_gas_bf4_calorific_value_CP = bf_gas_bf4_calorific_value

        bf_gas_bf4_calorific_value_PP = bf_gas_bf4_calorific_value

        bf_gas_bf4_calorific_value_SRF = bf_gas_bf4_calorific_value

        #Here, a check is performed to see whether the percentage distribution of the blast furnace gas corresponds to 100%.
        #If the distribution is not equal to 100%, all output parameters are set to 0.
        total_percentage = (bf_gas_bf4_percentage_intern + bf_gas_bf4_percentage_power_plant + bf_gas_bf4_percentage_slab_heat_furnace + bf_gas_bf4_percentage_coke_plant)

        if total_percentage != 100:
            pig_iron_bf4_steelworks = 0
            bf_gas_bf4_power_plant = 0
            bf_gas_bf4_intern = 0
            bf_gas_bf4_slab_heat = 0
            bf_gas_bf4_coke_plant = 0
            bf4_total_co2_mass_flow = 0
            bf4_slag_mass_flow = 0
            bf4_electricity_own = 0
            power_required = 0
            oxygen_required = 0
            bf_gas_bf4_calorific_value = 0
            bf_gas_bf4_calorific_value_CP = 0
            bf_gas_bf4_calorific_value_PP = 0
            bf_gas_bf4_calorific_value_SRF = 0
            total_bf_gas_volume_flow_bf4 = 0
            T_hot_metal = 0
            si_content = 0

        #The output parameters in the multi-agent system are output using 'return'.
        #The calculated variables are passed on to the respective twin. The user is shown the respective text 'pig_iron_bf4_steelworks [t/h]' with the corresponding variable (pig_iron_bf4_steelworks).
        return {
            "pig_iron_bf4_steelworks [t/h]": round(pig_iron_bf4_steelworks,2),
            "bf_gas_bf4_power_plant [m³/h]": bf_gas_bf4_power_plant,
            "bf_gas_bf4_intern [m³/h]": bf_gas_bf4_intern,
            "bf_gas_bf4_slab_heat [m³/h]": bf_gas_bf4_slab_heat,
            "bf_gas_bf4_coke_plant [m³/h]": bf_gas_bf4_coke_plant,
            "bf4_total_co2_mass_flow [t/h]": round(bf4_total_co2_mass_flow,2),
            "bf4_slag_mass_flow [t/h]": bf4_slag_mass_flow,
            "bf4_electricity_own [kW]": bf4_electricity_own,
            "power_required [kWh/h]": power_required,
            "oxygen_required [Nm³/h]": oxygen_required,
            "bf_gas_bf4_calorific_value [MJ/m³]": bf_gas_bf4_calorific_value,
            "bf_gas_bf4_calorific_value_CP [MJ/m³]": bf_gas_bf4_calorific_value_CP,
            "bf_gas_bf4_calorific_value_PP [MJ/m³]": bf_gas_bf4_calorific_value_PP,
            "bf_gas_bf4_calorific_value_SRF [MJ/m³]": bf_gas_bf4_calorific_value_SRF,
            "bf_gas_total_flow [m³/h]": round(total_bf_gas_volume_flow_bf4,2),
            "T_hot_metal [°C]": T_hot_metal,  # NEW: Thermal output
            "Si [%]": si_content,  # NEW: Silicon content
        }


#This function allows the script to be executed directly in the python/editor environment. Corresponding input variables are defined.
model = BlastFurnaceTwin()
result = model({"ore [t/h]": 50, "pellets [t/h]": 100, "sinter [t/h]": 100,
                "coke_mass_flow_bf4 [t/h]": 100, "coke_gas_coke_plant_bf4 [m³/h]": 20000,"calorific_value_coke_gas_bf4 [MJ/m³]":20, "power [kWh/h]": 50000, "oxygen [m³/h]": 50000, "wind_volume [Nm³/min]": 4000, "intern BF_GAS_PERCENTAGE [%]":50,"power plant BF_GAS_PERCENTAGE [%]":20, "slab heat furnace BF_GAS_PERCENTAGE [%]":20, "coke plant BF_GAS_PERCENTAGE [%]":10})
for x, value in result.items():
    print(f"{x}: {value}")