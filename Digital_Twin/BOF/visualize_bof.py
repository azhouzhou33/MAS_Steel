import matplotlib.pyplot as plt
import numpy as np
from BOF_Twin import BOFTwin
import os

def visualize():
    # Initialize model
    model = BOFTwin()
    default_inputs = model.default_inputs()

    # --- 1. Sensitivity Analysis: Pig Iron vs Steel Output & CO2 ---
    print("Running Sensitivity Analysis...")
    pig_iron_values = np.arange(40, 125, 5)
    steel_output_values = []
    co2_values = []

    for pig_iron in pig_iron_values:
        inputs = default_inputs.copy()
        inputs["pig_iron [t/h]"] = pig_iron
        
        # Run simulation
        results = model(inputs)
        
        steel_output_values.append(results["liquid_steel [t/h]"])
        co2_values.append(results["co2_emissions [t/h]"])

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Pig Iron Input [t/h]', fontsize=12)
    ax1.set_ylabel('Steel Output [t/h]', color=color, fontsize=12)
    ax1.plot(pig_iron_values, steel_output_values, color=color, marker='o', label='Steel')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('CO2 Emissions [t/h]', color=color, fontsize=12)
    ax2.plot(pig_iron_values, co2_values, color=color, marker='x', linestyle='--', label='CO2')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('BOF Sensitivity Analysis: Pig Iron vs Steel & CO2', fontsize=14)
    fig.tight_layout()
    
    output_path_sensitivity = 'bof_sensitivity_analysis.png'
    plt.savefig(output_path_sensitivity)
    print(f"Saved {output_path_sensitivity}")
    plt.close()

    # --- 2. Material Balance (Pie Chart) ---
    print("Generating Material Balance Chart...")
    res = model(default_inputs)
    
    # Material balance
    labels = ['Liquid Steel', 'Slag', 'Losses']
    total_input = default_inputs["pig_iron [t/h]"] + default_inputs["scrap_steel [t/h]"]
    losses = total_input - res["liquid_steel [t/h]"] - res["bof_slag [t/h]"]
    # Ensure losses is non-negative (account for rounding or model variations)
    losses = max(0, losses)
    sizes = [
        res["liquid_steel [t/h]"],
        res["bof_slag [t/h]"],
        losses
    ]
    
    fig2, ax3 = plt.subplots(figsize=(8, 8))
    colors = ['#66b3ff', '#ff9999', '#ffcc99']
    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, shadow=True)
    ax3.axis('equal')
    plt.title('BOF Material Balance (Default Inputs)', fontsize=14)
    
    output_path_balance = 'bof_material_balance.png'
    plt.savefig(output_path_balance)
    print(f"Saved {output_path_balance}")
    plt.close()

    # --- 3. Comprehensive Dashboard with Linked Fluctuations ---
    print("Running Comprehensive Dashboard Simulation...")
    np.random.seed(42)
    time_steps = 100
    time = np.arange(time_steps)

    # Production target curve
    target_curve = 1.0 + 0.15 * np.sin(time / 10) + np.random.normal(0, 0.02, time_steps)
    
    # Linked Inputs
    pig_iron_linked = 80 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    scrap_linked = 20 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    oxygen_linked = 5000 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    lime_linked = 5 * target_curve * np.random.normal(1.0, 0.01, time_steps)

    # Storage for results
    results_history = {
        "steel": [],
        "slag": [],
        "gas": [],
        "co2": [],
        "oxygen_req": [],
        "power_req": [],
        "calorific_val": []
    }

    for t in range(time_steps):
        inputs = default_inputs.copy()
        inputs["pig_iron [t/h]"] = pig_iron_linked[t]
        inputs["scrap_steel [t/h]"] = scrap_linked[t]
        inputs["oxygen [Nm³/h]"] = oxygen_linked[t]
        inputs["lime [t/h]"] = lime_linked[t]
        
        res = model(inputs)
        
        results_history["steel"].append(res["liquid_steel [t/h]"])
        results_history["slag"].append(res["bof_slag [t/h]"])
        results_history["gas"].append(res["bof_gas [Nm³/h]"])
        results_history["co2"].append(res["co2_emissions [t/h]"])
        results_history["oxygen_req"].append(res["oxygen_required [Nm³/h]"])
        results_history["power_req"].append(res["power_required [kWh/h]"])
        results_history["calorific_val"].append(res["bof_gas_calorific_value [MJ/Nm³]"])

    # --- Visualization ---
    fig_dash, axes = plt.subplots(3, 2, figsize=(16, 14), sharex=True)
    fig_dash.suptitle('BOF Digital Twin - Comprehensive Dashboard', fontsize=20)

    # 1. Inputs
    ax_in = axes[0, 0]
    ax_in.plot(time, pig_iron_linked, label='Pig Iron [t/h]', color='tab:red')
    ax_in.plot(time, scrap_linked, label='Scrap [t/h]', color='tab:grey')
    ax_in.set_title('Linked Input Fluctuations', fontsize=14)
    ax_in.set_ylabel('Mass Flow [t/h]')
    ax_in.legend(loc='upper right')
    ax_in.grid(True, alpha=0.3)

    # 2. Steel Output
    ax_steel = axes[0, 1]
    ax_steel.plot(time, results_history["steel"], color='tab:blue', linewidth=2)
    ax_steel.set_title('Liquid Steel Production', fontsize=14)
    ax_steel.set_ylabel('[t/h]')
    ax_steel.grid(True, alpha=0.3)

    # 3. Slag & Gas
    ax_sg = axes[1, 0]
    ax_sg.plot(time, results_history["slag"], label='Slag', color='tab:brown')
    ax_sg_twin = ax_sg.twinx()
    ax_sg_twin.plot(time, results_history["gas"], label='BOF Gas', color='tab:green', linestyle='--')
    ax_sg.set_ylabel('Slag [t/h]', color='tab:brown')
    ax_sg_twin.set_ylabel('BOF Gas [Nm³/h]', color='tab:green')
    ax_sg.set_title('Slag & BOF Gas Production', fontsize=14)
    ax_sg.grid(True, alpha=0.3)

    # 4. CO2 Emissions
    ax_co2 = axes[1, 1]
    ax_co2.plot(time, results_history["co2"], color='tab:orange', linestyle='--')
    ax_co2.set_title('CO2 Emissions', fontsize=14)
    ax_co2.set_ylabel('[t/h]')
    ax_co2.grid(True, alpha=0.3)

    # 5. Oxygen Requirement
    ax_o2 = axes[2, 0]
    ax_o2.plot(time, results_history["oxygen_req"], color='tab:cyan')
    ax_o2.set_title('Oxygen Requirement', fontsize=14)
    ax_o2.set_ylabel('[Nm³/h]')
    ax_o2.set_xlabel('Time Steps')
    ax_o2.grid(True, alpha=0.3)

    # 6. Calorific Value
    ax_cal = axes[2, 1]
    ax_cal.plot(time, results_history["calorific_val"], color='tab:purple')
    ax_cal.set_title('BOF Gas Calorific Value', fontsize=14)
    ax_cal.set_ylabel('[MJ/Nm³]')
    ax_cal.set_xlabel('Time Steps')
    ax_cal.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    output_path_dash = 'bof_comprehensive_dashboard.png'
    plt.savefig(output_path_dash)
    print(f"Saved {output_path_dash}")
    plt.close()

if __name__ == "__main__":
    visualize()
