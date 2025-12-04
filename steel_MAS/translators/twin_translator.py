    """
    Translates between Agent actions, Twin inputs/outputs, and Environment state.
    All physical mapping coefficients and conversions are centralized here.
    
    This separation:
    - Makes it easy to update Twin models without changing Agent or Env code
    - Documents all physical assumptions in one place
    - Enables easy testing of mapping logic
    """
    
    # =========================================================================
    # PHYSICAL CONSTANTS & MAPPING FACTORS
    # =========================================================================
    
    # Blast Furnace
    PCI_TO_COKE_FACTOR = 1.5  # PCI (kg/t HM) to coke mass flow conversion
    # NOTE: Oxygen is now calculated from wind (21% O2 in air) in the Twin itself
    
    # Gas distribution defaults (when not specified by actions)
    DEFAULT_BF_GAS_DISTRIBUTION = {
        "intern": 50.0,  # %
        "power_plant": 20.0,
        "slab_heat_furnace": 20.0,
        "coke_plant": 10.0
    }
    
    # =========================================================================
    # BLAST FURNACE TWIN TRANSLATION
    # =========================================================================
    
    @staticmethod
    def bf_action_to_twin_input(
        agent_action: Dict[str, Any],
        env_state: Dict[str, Any]
    ) -> BFInput:
        """
        Map BF agent action to BF Twin input format.
        
        Args:
            agent_action: Agent's control decision
                - wind_volume: Nm³/min
                - O2_enrichment: %
                - PCI: kg/t HM
                - COG_ratio: fraction
            env_state: Current environment state
                - COG_available: Nm³/h
        
        Returns:
            Typed BFInput object
        """
        # Extract agent actions with defaults
        wind_volume = agent_action.get("wind_volume", 4000)  # Nm³/min
        o2_enrichment_pct = agent_action.get("O2_enrichment", 3.5)  # %
        pci = agent_action.get("PCI", 150)  # kg/t HM
        
        # Physical mappings
        coke_mass_flow = pci / TwinTranslator.PCI_TO_COKE_FACTOR
        
        # NOTE: Oxygen is now calculated in the Twin from wind (21% O2 in air)
        # The o2_enrichment_pct can be passed as oxygen_enrichment if needed
        # For backward compatibility, we still pass a nominal oxygen value
        base_o2_from_wind = 0.21 * wind_volume * 60  # Nm³/h
        oxygen_enrichment_flow = base_o2_from_wind * (o2_enrichment_pct / 100)
        
        # Get resources from environment state
        cog_available = env_state.get("COG_available", 20000)
        
        # Create typed input
        return BFInput(
            ore=50.0,  # Could be made dynamic based on production plan
            pellets=100.0,
            sinter=100.0,
            coke_mass_flow=coke_mass_flow,
            coke_gas_flow=cog_available,
            calorific_value_coke_gas=20.0,  # MJ/m³
            power=50000.0,  # kWh/h
            oxygen=base_o2_from_wind,  # Base O2 from wind
            wind_volume=wind_volume,  # NEW: Wind volume for physics
            intern_bf_gas_percentage=TwinTranslator.DEFAULT_BF_GAS_DISTRIBUTION["intern"],
            power_plant_bf_gas_percentage=TwinTranslator.DEFAULT_BF_GAS_DISTRIBUTION["power_plant"],
            slab_heat_furnace_bf_gas_percentage=TwinTranslator.DEFAULT_BF_GAS_DISTRIBUTION["slab_heat_furnace"],
            coke_plant_bf_gas_percentage=TwinTranslator.DEFAULT_BF_GAS_DISTRIBUTION["coke_plant"]
        )
    
    @staticmethod
    def bf_output_to_env_state(bf_output: BFOutput) -> Dict[str, Any]:
        """
        Extract relevant state updates from BF Twin output.
        
        Args:
            bf_output: Typed BFOutput from Twin
        
        Returns:
            Dictionary of state updates for environment
        """
        return {
            "pig_iron_production": bf_output.pig_iron_steelworks,
            "bfg_supply": bf_output.bf_gas_total_flow,
            "co2_emissions_bf": bf_output.total_co2_mass_flow,
            "slag_bf": bf_output.slag_mass_flow,
            "electricity_own_bf": bf_output.electricity_own,
            "T_hot_metal": bf_output.t_hot_metal,  # NEW: Thermal outputs
            "Si": bf_output.si_content,  # NEW: Silicon content
        }
    
    # =========================================================================
    # BOF TWIN TRANSLATION
    # =========================================================================
    
    @staticmethod
    def bof_action_to_twin_input(
        agent_action: Dict[str, Any],
        env_state: Dict[str, Any]
    ) -> BOFInput:
        """
        Map BOF agent action to BOF Twin input format.
        
        Args:
            agent_action: Agent's control decision
                - oxygen: Nm³/h
                - scrap_steel: t/batch
            env_state: Current environment state
                - pig_iron_production: t/h
        
        Returns:
            Typed BOFInput object
        """
        # Extract agent actions
        oxygen = agent_action.get("oxygen", 45000)  # Nm³/h
        scrap_steel = agent_action.get("scrap_steel", 20)  # t/batch
        
        # Get pig iron availability from BF
        pig_iron_available = env_state.get("pig_iron_production", 200)
        pig_iron_to_bof = min(pig_iron_available, 80)  # BOF capacity limit
        
        return BOFInput(
            pig_iron=pig_iron_to_bof,
            scrap_steel=scrap_steel,
            oxygen=oxygen,
            lime=5.0,  # t/h - could be made dynamic
            power=5000.0  # kWh/h
        )
    
    @staticmethod
    def bof_output_to_env_state(bof_output: BOFOutput) -> Dict[str, Any]:
        """Extract relevant state updates from BOF Twin output"""
        return {
            "liquid_steel": bof_output.liquid_steel,
            "bofg_supply": bof_output.bof_gas,
            "co2_emissions_bof": bof_output.co2_emissions,
            "T_steel": 1650  # Simplified - in real Twin this would be output
        }
    
    # =========================================================================
    # COKE OVEN TWIN TRANSLATION
    # =========================================================================
    
    @staticmethod
    def coke_oven_action_to_twin_input(
        agent_action: Dict[str, Any],
        env_state: Dict[str, Any]
    ) -> CokeOvenInput:
        """
        Map Coke Oven agent action to Coke Oven Twin input format.
        
        Args:
            agent_action: Agent's control decision
                - heating_gas_input: Nm³/h
                - pushing_rate: relative adjustment factor
            env_state: Current environment state
        
        Returns:
            Typed CokeOvenInput object
        """
        heating_gas = agent_action.get("heating_gas_input", 15000)  # Nm³/h
        
        return CokeOvenInput(
            coal_input=100.0,  # t/h - base production rate
            heating_gas=heating_gas,
            heating_gas_calorific_value=4.5,  # MJ/Nm³
            steam=2.0,  # t/h
            power=3000.0  # kWh/h
        )
    
    @staticmethod
    def coke_oven_output_to_env_state(co_output: CokeOvenOutput) -> Dict[str, Any]:
        """Extract relevant state updates from Coke Oven Twin output"""
        return {
            "coke_production": co_output.coke_production,
            "cog_supply": co_output.cog_production,
            "COG_available": co_output.cog_production,  # Make available to other units
            "tar_production": co_output.tar,
            "co2_emissions_co": co_output.co2_emissions
        }
    
    # =========================================================================
    # GAS HOLDER TRANSLATION
    # =========================================================================
    
    @staticmethod
    def calculate_gas_net_flow(
        gas_production: float,
        gas_consumption_dict: Dict[str, float],
        gas_type: str
    ) -> float:
        """
        Calculate net flow for a gas holder.
        
        Args:
            gas_production: Production rate (Nm³/h)
            gas_consumption_dict: All consumption demands
            gas_type: 'bfg', 'bofg', or 'cog'
        
        Returns:
            Net flow (Nm³/h)
        """
        # Sum all consumption for this gas type
        consumption = 0.0
        for key, value in gas_consumption_dict.items():
            if gas_type in key.lower():
                consumption += value
        
        return gas_production - consumption
