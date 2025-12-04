import matplotlib.pyplot as plt
import numpy as np
from Blast_Furnace_Twin_to_share import BlastFurnaceTwin
import os

def visualize():
    # Initialize model
    model = BlastFurnaceTwin()
    default_inputs = model.default_inputs()

    # --- 1. Sensitivity Analysis: Ore vs Pig Iron & CO2 ---
    print("Running Sensitivity Analysis...")
    ore_values = np.arange(0, 105, 5)
    pig_iron_values = []
    co2_values = []

    for ore in ore_values:
        inputs = default_inputs.copy()
        inputs["ore [t/h]"] = ore
        
        # Run simulation
        results = model(inputs)
        
        pig_iron_values.append(results["pig_iron_bf4_steelworks [t/h]"])
        co2_values.append(results["bf4_total_co2_mass_flow [t/h]"])

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:red'
    ax1.set_xlabel('Ore Input [t/h]', fontsize=12)
    ax1.set_ylabel('Pig Iron Production [t/h]', color=color, fontsize=12)
    ax1.plot(ore_values, pig_iron_values, color=color, marker='o', label='Pig Iron')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'tab:blue'
    ax2.set_ylabel('Total CO2 Mass Flow [t/h]', color=color, fontsize=12)
    ax2.plot(ore_values, co2_values, color=color, marker='x', linestyle='--', label='CO2')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Sensitivity Analysis: Ore Input vs Pig Iron & CO2', fontsize=14)
    fig.tight_layout()
    
    output_path_sensitivity = 'sensitivity_analysis.png'
    plt.savefig(output_path_sensitivity)
    print(f"Saved {output_path_sensitivity}")
    plt.close()

    # --- 2. Gas Distribution (Pie Chart) ---
    print("Generating Gas Distribution Chart...")
    # Run with default values
    res = model(default_inputs)
    
    # Extract gas values
    labels = ['Intern', 'Power Plant', 'Slab Heat', 'Coke Plant']
    sizes = [
        res["bf_gas_bf4_intern [m³/h]"],
        res["bf_gas_bf4_power_plant [m³/h]"],
        res["bf_gas_bf4_slab_heat [m³/h]"],
        res["bf_gas_bf4_coke_plant [m³/h]"]
    ]
    
    # Pie Chart
    fig2, ax3 = plt.subplots(figsize=(8, 8))
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, shadow=True)
    ax3.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Blast Furnace Gas Distribution (Default Inputs)', fontsize=14)
    
    output_path_gas = 'gas_distribution.png'
    plt.savefig(output_path_gas)
    print(f"Saved {output_path_gas}")
    plt.close()

    output_path_gas = 'gas_distribution.png'
    plt.savefig(output_path_gas)
    print(f"Saved {output_path_gas}")
    plt.close()

    # --- 3. Comprehensive Dashboard with Linked Fluctuations ---
    print("Running Comprehensive Dashboard Simulation...")
    np.random.seed(42)
    time_steps = 100
    time = np.arange(time_steps)

    # Define a "Production Target" curve (e.g., sine wave + trend)
    # This represents the planned production level (0.8 to 1.2 of default)
    target_curve = 1.0 + 0.15 * np.sin(time / 10) + np.random.normal(0, 0.02, time_steps)
    
    # Linked Inputs: Inputs vary based on the target curve + small random noise
    # This ensures they are sufficient to meet the target (avoiding constant bottlenecks)
    ore_linked = 50 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    coke_linked = 100 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    power_linked = 50000 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    oxygen_linked = 50000 * target_curve * np.random.normal(1.0, 0.01, time_steps)

    # Storage for results
    results_history = {
        "pig_iron": [],
        "bf_gas_total": [],
        "bf_gas_intern": [],
        "bf_gas_power": [],
        "bf_gas_slab": [],
        "bf_gas_coke": [],
        "co2": [],
        "power_req": [],
        "power_own": [],
        "oxygen_req": [],
        "calorific_val": []
    }

    for t in range(time_steps):
        inputs = default_inputs.copy()
        inputs["ore [t/h]"] = ore_linked[t]
        inputs["coke_mass_flow_bf4 [t/h]"] = coke_linked[t]
        inputs["power [kWh/h]"] = power_linked[t]
        inputs["oxygen [m³/h]"] = oxygen_linked[t]
        
        res = model(inputs)
        
        results_history["pig_iron"].append(res["pig_iron_bf4_steelworks [t/h]"])
        results_history["bf_gas_total"].append(res["bf_gas_total_flow [m³/h]"])
        results_history["bf_gas_intern"].append(res["bf_gas_bf4_intern [m³/h]"])
        results_history["bf_gas_power"].append(res["bf_gas_bf4_power_plant [m³/h]"])
        results_history["bf_gas_slab"].append(res["bf_gas_bf4_slab_heat [m³/h]"])
        results_history["bf_gas_coke"].append(res["bf_gas_bf4_coke_plant [m³/h]"])
        results_history["co2"].append(res["bf4_total_co2_mass_flow [t/h]"])
        results_history["power_req"].append(res["power_required [kWh/h]"])
        results_history["power_own"].append(res["bf4_electricity_own [kW]"])
        results_history["oxygen_req"].append(res["oxygen_required [Nm³/h]"])
        results_history["calorific_val"].append(res["bf_gas_bf4_calorific_value [MJ/m³]"])

    # --- Visualization ---
    fig_dash, axes = plt.subplots(4, 2, figsize=(16, 20), sharex=True)
    fig_dash.suptitle('Blast Furnace Digital Twin - Comprehensive Dashboard', fontsize=20)

    # 1. Inputs
    ax_in = axes[0, 0]
    ax_in.plot(time, ore_linked, label='Ore [t/h]')
    ax_in.plot(time, coke_linked, label='Coke [t/h]')
    ax_in.set_title('Linked Input Fluctuations', fontsize=14)
    ax_in.set_ylabel('Mass Flow [t/h]')
    ax_in.legend(loc='upper right')
    ax_in.grid(True, alpha=0.3)

    # 2. Pig Iron Output
    ax_pi = axes[0, 1]
    ax_pi.plot(time, results_history["pig_iron"], color='tab:red', linewidth=2)
    ax_pi.set_title('Pig Iron Production', fontsize=14)
    ax_pi.set_ylabel('[t/h]')
    ax_pi.grid(True, alpha=0.3)

    # 3. BF Gas Total
    ax_gas = axes[1, 0]
    ax_gas.plot(time, results_history["bf_gas_total"], color='tab:green', label='Total Gas')
    ax_gas.set_title('Total BF Gas Production', fontsize=14)
    ax_gas.set_ylabel('[m³/h]')
    ax_gas.grid(True, alpha=0.3)

    # 4. BF Gas Distribution (Stacked)
    ax_dist = axes[1, 1]
    ax_dist.stackplot(time, 
                      results_history["bf_gas_intern"], 
                      results_history["bf_gas_power"], 
                      results_history["bf_gas_slab"], 
                      results_history["bf_gas_coke"],
                      labels=['Intern', 'Power Plant', 'Slab Heat', 'Coke Plant'],
                      alpha=0.7)
    ax_dist.set_title('BF Gas Distribution', fontsize=14)
    ax_dist.set_ylabel('[m³/h]')
    ax_dist.legend(loc='upper left', fontsize='small')
    ax_dist.grid(True, alpha=0.3)

    # 5. CO2 Emissions
    ax_co2 = axes[2, 0]
    ax_co2.plot(time, results_history["co2"], color='tab:grey', linestyle='--')
    ax_co2.set_title('CO2 Emissions', fontsize=14)
    ax_co2.set_ylabel('[t/h]')
    ax_co2.grid(True, alpha=0.3)

    # 6. Power (Required vs Own)
    ax_pwr = axes[2, 1]
    ax_pwr.plot(time, results_history["power_req"], label='Required', color='tab:orange')
    ax_pwr.plot(time, results_history["power_own"], label='Own Gen', color='tab:purple')
    ax_pwr.set_title('Power Balance', fontsize=14)
    ax_pwr.set_ylabel('[kWh/h] / [kW]')
    ax_pwr.legend()
    ax_pwr.grid(True, alpha=0.3)

    # 7. Oxygen Demand
    ax_o2 = axes[3, 0]
    ax_o2.plot(time, results_history["oxygen_req"], color='tab:cyan')
    ax_o2.set_title('Oxygen Requirement', fontsize=14)
    ax_o2.set_ylabel('[Nm³/h]')
    ax_o2.set_xlabel('Time Steps')
    ax_o2.grid(True, alpha=0.3)

    # 8. Calorific Value
    ax_cal = axes[3, 1]
    ax_cal.plot(time, results_history["calorific_val"], color='tab:brown')
    ax_cal.set_title('BF Gas Calorific Value', fontsize=14)
    ax_cal.set_ylabel('[MJ/m³]')
    ax_cal.set_xlabel('Time Steps')
    ax_cal.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97]) # Adjust for suptitle
    
    output_path_dash = 'comprehensive_dashboard.png'
    plt.savefig(output_path_dash)
    print(f"Saved {output_path_dash}")
    plt.close()

if __name__ == "__main__":
    visualize()
