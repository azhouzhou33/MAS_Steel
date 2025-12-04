import matplotlib.pyplot as plt
import numpy as np
from Coke_Oven_Twin import CokeOvenTwin
import os

def visualize():
    # Initialize model
    model = CokeOvenTwin()
    default_inputs = model.default_inputs()

    # --- 1. Sensitivity Analysis: Coal vs Coke & COG ---
    print("Running Sensitivity Analysis...")
    coal_values = np.arange(50, 155, 5)
    coke_output_values = []
    cog_output_values = []

    for coal in coal_values:
        inputs = default_inputs.copy()
        inputs["coal_input [t/h]"] = coal
        # Scale heating gas proportionally
        inputs["heating_gas [Nm³/h]"] = 15000 * (coal / 100)
        
        # Run simulation
        results = model(inputs)
        
        coke_output_values.append(results["coke_production [t/h]"])
        cog_output_values.append(results["cog_production [Nm³/h]"])

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:green'
    ax1.set_xlabel('Coal Input [t/h]', fontsize=12)
    ax1.set_ylabel('Coke Production [t/h]', color=color, fontsize=12)
    ax1.plot(coal_values, coke_output_values, color=color, marker='o', label='Coke')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color = 'tab:purple'
    ax2.set_ylabel('COG Production [Nm³/h]', color=color, fontsize=12)
    ax2.plot(coal_values, cog_output_values, color=color, marker='x', linestyle='--', label='COG')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Coke Oven Sensitivity Analysis: Coal vs Coke & COG', fontsize=14)
    fig.tight_layout()
    
    output_path_sensitivity = 'coke_oven_sensitivity_analysis.png'
    plt.savefig(output_path_sensitivity)
    print(f"Saved {output_path_sensitivity}")
    plt.close()

    # --- 2. Product Distribution (Pie Chart) ---
    print("Generating Product Distribution Chart...")
    res = model(default_inputs)
    
    # Product distribution (as % of coal processed)
    coal_processed = res["coal_processed [t/h]"]
    labels = ['Coke', 'COG (mass equiv)', 'Tar', 'Ammonia', 'Other losses']
    
    # Convert COG to mass equivalent (approx 0.5 kg/Nm³)
    cog_mass_equiv = res["cog_production [Nm³/h]"] * 0.0005  # t/h
    
    total_products = res["coke_production [t/h]"] + cog_mass_equiv + res["tar [t/h]"] + res["ammonia_liquor [t/h]"]
    other_losses = max(0, coal_processed - total_products)
    
    sizes = [
        res["coke_production [t/h]"],
        cog_mass_equiv,
        res["tar [t/h]"],
        res["ammonia_liquor [t/h]"],
        other_losses
    ]
    
    fig2, ax3 = plt.subplots(figsize=(8, 8))
    colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999', '#cccccc']
    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, shadow=True)
    ax3.axis('equal')
    plt.title('Coke Oven Product Distribution (Default Inputs)', fontsize=14)
    
    output_path_balance = 'coke_oven_product_distribution.png'
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
    coal_linked = 100 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    heating_gas_linked = 15000 * target_curve * np.random.normal(1.0, 0.01, time_steps)
    steam_linked = 2 * target_curve * np.random.normal(1.0, 0.01, time_steps)

    # Storage for results
    results_history = {
        "coke": [],
        "cog": [],
        "tar": [],
        "ammonia": [],
        "co2": [],
        "cog_cv": [],
        "heating_gas_req": []
    }

    for t in range(time_steps):
        inputs = default_inputs.copy()
        inputs["coal_input [t/h]"] = coal_linked[t]
        inputs["heating_gas [Nm³/h]"] = heating_gas_linked[t]
        inputs["steam [t/h]"] = steam_linked[t]
        
        res = model(inputs)
        
        results_history["coke"].append(res["coke_production [t/h]"])
        results_history["cog"].append(res["cog_production [Nm³/h]"])
        results_history["tar"].append(res["tar [t/h]"])
        results_history["ammonia"].append(res["ammonia_liquor [t/h]"])
        results_history["co2"].append(res["co2_emissions [t/h]"])
        results_history["cog_cv"].append(res["cog_calorific_value [MJ/Nm³]"])
        results_history["heating_gas_req"].append(res["heating_gas_required [Nm³/h]"])

    # --- Visualization ---
    fig_dash, axes = plt.subplots(3, 2, figsize=(16, 14), sharex=True)
    fig_dash.suptitle('Coke Oven Digital Twin - Comprehensive Dashboard', fontsize=20)

    # 1. Inputs
    ax_in = axes[0, 0]
    ax_in.plot(time, coal_linked, label='Coal [t/h]', color='black')
    ax_in_twin = ax_in.twinx()
    ax_in_twin.plot(time, heating_gas_linked, label='Heating Gas [Nm³/h]', color='tab:orange', linestyle='--')
    ax_in.set_ylabel('Coal [t/h]', color='black')
    ax_in_twin.set_ylabel('Heating Gas [Nm³/h]', color='tab:orange')
    ax_in.set_title('Linked Input Fluctuations', fontsize=14)
    ax_in.grid(True, alpha=0.3)

    # 2. Coke Output
    ax_coke = axes[0, 1]
    ax_coke.plot(time, results_history["coke"], color='tab:green', linewidth=2)
    ax_coke.set_title('Coke Production', fontsize=14)
    ax_coke.set_ylabel('[t/h]')
    ax_coke.grid(True, alpha=0.3)

    # 3. COG Production
    ax_cog = axes[1, 0]
    ax_cog.plot(time, results_history["cog"], color='tab:purple', linewidth=2)
    ax_cog.set_title('COG Production', fontsize=14)
    ax_cog.set_ylabel('[Nm³/h]')
    ax_cog.grid(True, alpha=0.3)

    # 4. By-products
    ax_byprod = axes[1, 1]
    ax_byprod.plot(time, results_history["tar"], label='Tar', color='tab:brown')
    ax_byprod.plot(time, results_history["ammonia"], label='Ammonia', color='tab:cyan', linestyle='--')
    ax_byprod.set_title('By-products (Tar & Ammonia)', fontsize=14)
    ax_byprod.set_ylabel('[t/h]')
    ax_byprod.legend()
    ax_byprod.grid(True, alpha=0.3)

    # 5. CO2 Emissions
    ax_co2 = axes[2, 0]
    ax_co2.plot(time, results_history["co2"], color='tab:grey', linestyle='--')
    ax_co2.set_title('CO2 Emissions', fontsize=14)
    ax_co2.set_ylabel('[t/h]')
    ax_co2.set_xlabel('Time Steps')
    ax_co2.grid(True, alpha=0.3)

    # 6. COG Calorific Value
    ax_cv = axes[2, 1]
    ax_cv.plot(time, results_history["cog_cv"], color='tab:red')
    ax_cv.set_title('COG Calorific Value', fontsize=14)
    ax_cv.set_ylabel('[MJ/Nm³]')
    ax_cv.set_xlabel('Time Steps')
    ax_cv.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    output_path_dash = 'coke_oven_comprehensive_dashboard.png'
    plt.savefig(output_path_dash)
    print(f"Saved {output_path_dash}")
    plt.close()

if __name__ == "__main__":
    visualize()
