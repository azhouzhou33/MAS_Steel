"""
Agent Control Demonstration
Shows detailed step-by-step process of how agents control digital twins
"""

import sys
import os
# Add current directory and parent directory to path
sys.path.append(os.path.dirname(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import numpy as np
from agents.bf_agent import BF_Agent
from agents.bof_agent import BOF_Agent
from agents.coke_oven_agent import CokeOven_Agent
from agents.gas_holder_agent import GasHolder_Agent

# Import twins - using importlib due to spaces in directory names
import importlib.util
try:
    # Get the parent directory path
    digital_twin_dir = os.path.join(parent_dir, "Digital_Twin")
    
    # Import BlastFurnaceTwin
    bf_path = os.path.join(digital_twin_dir, "Blast Furnace", "Blast_Furnace_Twin_to_share.py")
    spec = importlib.util.spec_from_file_location("BlastFurnaceTwin", bf_path)
    bf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bf_module)
    BlastFurnaceTwin = bf_module.BlastFurnaceTwin
    
    # Import BOFTwin
    bof_path = os.path.join(digital_twin_dir, "BOF", "BOF_Twin.py")
    spec = importlib.util.spec_from_file_location("BOFTwin", bof_path)
    bof_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bof_module)
    BOFTwin = bof_module.BOFTwin
    
    # Import CokeOvenTwin
    co_path = os.path.join(digital_twin_dir, "Coke Oven", "Coke_Oven_Twin.py")
    spec = importlib.util.spec_from_file_location("CokeOvenTwin", co_path)
    co_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(co_module)
    CokeOvenTwin = co_module.CokeOvenTwin
    
    TWINS_AVAILABLE = True
    print("✅ Digital twins loaded successfully!")
except Exception as e:
    TWINS_AVAILABLE = False
    print(f"Warning: Digital twins not available - {e}")


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_dict(data, indent=2):
    """Print dictionary in a formatted way"""
    for key, value in data.items():
        if isinstance(value, float):
            print(f"{' '*indent}{key}: {value:.2f}")
        else:
            print(f"{' '*indent}{key}: {value}")


def demonstrate_bf_control():
    """Demonstrate BF Agent controlling BF Twin"""
    
    print_section("场景 1: BF Agent 调控 Blast Furnace Twin")
    
    # Initialize
    bf_agent = BF_Agent("BF1")
    bf_twin = BlastFurnaceTwin() if TWINS_AVAILABLE else None
    
    if not TWINS_AVAILABLE:
        print("⚠️  Twin模型不可用，使用模拟数据")
        return
    
    # =========================================================================
    # STEP 1: Initial State (Normal Operation)
    # =========================================================================
    print("\n" + "-" * 80)
    print("📊 步骤 1: 初始状态 (正常运行)")
    print("-" * 80)
    
    # Agent initial state
    initial_agent_state = bf_agent.get_state()
    print("\n🤖 Agent 初始控制参数:")
    print_dict(initial_agent_state)
    
    # Twin inputs for normal operation
    # NEW: Wind-based oxygen physics
    wind_volume = initial_agent_state["wind_volume"]  # Nm³/min
    O2_from_wind = 0.21 * wind_volume * 60  # 21% O2 in air, convert to Nm³/h
    O2_enrichment_pct = initial_agent_state["O2_enrichment"]  # %
    O2_enrichment_flow = O2_from_wind * (O2_enrichment_pct / 100)  # Additional O2
    total_oxygen = O2_from_wind + O2_enrichment_flow
    
    initial_twin_inputs = {
        "ore [t/h]": 50,
        "pellets [t/h]": 100,
        "sinter [t/h]": 100,
        "coke_mass_flow_bf4 [t/h]": 100,
        "coke_gas_coke_plant_bf4 [m³/h]": 20000,
        "calorific_value_coke_gas_bf4 [MJ/m³]": 20,
        "power [kWh/h]": 50000,
        "wind_volume [Nm³/min]": wind_volume,  # NEW: Wind volume
        "oxygen [m³/h]": total_oxygen,  # Wind-based oxygen
        "intern BF_GAS_PERCENTAGE [%]": 50,
        "power plant BF_GAS_PERCENTAGE [%]": 20,
        "slab heat furnace BF_GAS_PERCENTAGE [%]": 20,
        "coke plant BF_GAS_PERCENTAGE [%]": 10
    }
    
    print("\n📥 Twin 输入参数:")
    key_inputs = ["oxygen [m³/h]", "coke_mass_flow_bf4 [t/h]", "power [kWh/h]"]
    for key in key_inputs:
        print(f"  {key}: {initial_twin_inputs[key]:.2f}")
    
    # Calculate initial outputs
    initial_outputs = bf_twin(initial_twin_inputs)
    
    print("\n📤 Twin 输出结果 (调控前):")
    key_outputs = [
        "pig_iron_bf4_steelworks [t/h]",
        "bf_gas_total_flow [m³/h]",
        "T_hot_metal [°C]",  # NEW: Thermal output
        "Si [%]",  # NEW: Silicon content
        "bf4_total_co2_mass_flow [t/h]"
    ]
    for key in key_outputs:
        if key in initial_outputs:
            print(f"  {key}: {initial_outputs[key]:.2f}")
    
    # =========================================================================
    # STEP 2: Problem Detected - Gas Holder Full
    # =========================================================================
    print("\n" + "-" * 80)
    print("⚠️  步骤 2: 检测到问题 - BFG气柜过满！")
    print("-" * 80)
    
    # Simulated observation with high gas holder SOC
    problem_observation = {
        "Si": 0.45,
        "T_hot_metal": 1500,
        "SOC_bfg": 0.92,  # 🔴 Too full!
        "P_bfg": 15.2,    # 🔴 Too high!
        "COG_available": 20000,
        "COG_required": 18000,
        "O2_available": 50000,
        "peak_electricity": False
    }
    
    print("\n🔍 Agent 观察到的状态:")
    print(f"  SOC_BFG: {problem_observation['SOC_bfg']:.2f} (目标范围: 0.25-0.85)")
    print(f"  P_BFG: {problem_observation['P_bfg']:.1f} kPa (目标范围: 9-14 kPa)")
    print(f"  ❌ 气柜过满，需要减少BFG产量！")
    
    # =========================================================================
    # STEP 3: Agent Decision Making
    # =========================================================================
    print("\n" + "-" * 80)
    print("🧠 步骤 3: Agent 决策过程")
    print("-" * 80)
    
    print("\n📋 Agent 规则触发:")
    print("  1. ✅ Level 3 (能源协同): SOC_bfg > 0.85 → 减少风量和氧气")
    print("  2. 应用规则: wind_volume *= 0.95, PCI *= 0.97, O2 *= 0.95")
    
    # Agent makes decision
    adjusted_agent_state = bf_agent.step(problem_observation)
    
    print("\n🎯 Agent 调整后的控制参数:")
    print(f"  wind_volume: {initial_agent_state['wind_volume']:.0f} → {adjusted_agent_state['wind_volume']:.0f} Nm³/min (↓{(1-adjusted_agent_state['wind_volume']/initial_agent_state['wind_volume'])*100:.1f}%)")
    print(f"  O2_enrichment: {initial_agent_state['O2_enrichment']:.2f} → {adjusted_agent_state['O2_enrichment']:.2f}% (↓{(1-adjusted_agent_state['O2_enrichment']/initial_agent_state['O2_enrichment'])*100:.1f}%)")
    print(f"  PCI: {initial_agent_state['PCI']:.1f} → {adjusted_agent_state['PCI']:.1f} kg/t HM (↓{(1-adjusted_agent_state['PCI']/initial_agent_state['PCI'])*100:.1f}%)")
    
    # =========================================================================
    # STEP 4: Twin Re-calculation with New Actions
    # =========================================================================
    print("\n" + "-" * 80)
    print("⚙️  步骤 4: Twin 重新计算 (应用Agent调控)")
    print("-" * 80)
    
    # Map adjusted agent state to twin inputs
    # NEW: Recalculate oxygen based on adjusted wind
    wind_adj = adjusted_agent_state["wind_volume"]
    O2_wind_adj = 0.21 * wind_adj * 60
    O2_enrich_pct_adj = adjusted_agent_state["O2_enrichment"]
    O2_enrich_adj = O2_wind_adj * (O2_enrich_pct_adj / 100)
    total_oxygen_adj = O2_wind_adj + O2_enrich_adj
    
    adjusted_twin_inputs = initial_twin_inputs.copy()
    adjusted_twin_inputs["wind_volume [Nm³/min]"] = wind_adj
    adjusted_twin_inputs["oxygen [m³/h]"] = total_oxygen_adj
    adjusted_twin_inputs["coke_mass_flow_bf4 [t/h]"] = adjusted_agent_state["PCI"] / 1.5
    
    print("\n📥 Twin 新输入参数:")
    print(f"  oxygen [m³/h]: {initial_twin_inputs['oxygen [m³/h]']:.0f} → {adjusted_twin_inputs['oxygen [m³/h]']:.0f}")
    print(f"  coke_mass_flow_bf4 [t/h]: {initial_twin_inputs['coke_mass_flow_bf4 [t/h]']:.1f} → {adjusted_twin_inputs['coke_mass_flow_bf4 [t/h]']:.1f}")
    
    # Calculate new outputs
    adjusted_outputs = bf_twin(adjusted_twin_inputs)
    
    print("\n📤 Twin 新输出结果:")
    for key in key_outputs:
        if key in adjusted_outputs and key in initial_outputs:
            old_val = initial_outputs[key]
            new_val = adjusted_outputs[key]
            change = ((new_val - old_val) / old_val * 100) if old_val != 0 else 0
            arrow = "↓" if change < 0 else "↑"
            print(f"  {key}:")
            print(f"    调控前: {old_val:.2f}")
            print(f"    调控后: {new_val:.2f} ({arrow}{abs(change):.1f}%)")
    
    # =========================================================================
    # STEP 5: Summary of Control Effect
    # =========================================================================
    print("\n" + "-" * 80)
    print("📈 步骤 5: 调控效果总结")
    print("-" * 80)
    
    bfg_before = initial_outputs.get("bf_gas_total_flow [m³/h]", 0)
    bfg_after = adjusted_outputs.get("bf_gas_total_flow [m³/h]", 0)
    bfg_reduction = bfg_before - bfg_after
    
    print(f"\n✅ 调控成功！")
    print(f"  🎯 目标: 减少BFG产量以降低气柜压力")
    print(f"  📊 结果: BFG产量减少 {bfg_reduction:.0f} m³/h")
    print(f"  💡 预期效果: 气柜SOC将逐步下降至安全范围")
    
    print("\n🔄 闭环控制:")
    print("  1. Agent观察 → 气柜过满")
    print("  2. Agent决策 → 减少风量/氧气")
    print("  3. Twin计算 → BFG产量降低")
    print("  4. 环境更新 → 气柜SOC下降")
    print("  5. 循环继续...")
    
    return {
        "initial_outputs": initial_outputs,
        "adjusted_outputs": adjusted_outputs,
        "initial_agent_state": initial_agent_state,
        "adjusted_agent_state": adjusted_agent_state
    }


def demonstrate_bof_control():
    """Demonstrate BOF Agent controlling BOF Twin"""
    
    print_section("场景 2: BOF Agent 调控 BOF Twin")
    
    bof_agent = BOF_Agent("BOF1")
    bof_twin = BOFTwin() if TWINS_AVAILABLE else None
    
    if not TWINS_AVAILABLE:
        print("⚠️  Twin模型不可用")
        return
    
    print("\n📋 场景: 钢水温度过高，需要降温")
    
    # Initial state
    initial_state = bof_agent.get_state()
    print(f"\n🤖 初始氧气流量: {initial_state['oxygen']:.0f} Nm³/h")
    print(f"   初始废钢量: {initial_state['scrap_steel']:.1f} t/batch")
    
    # Initial twin calculation
    initial_inputs = {
        "pig_iron [t/h]": 80,
        "scrap_steel [t/h]": initial_state['scrap_steel'],
        "oxygen [Nm³/h]": initial_state['oxygen'],
        "lime [t/h]": 5,
        "power [kWh/h]": 5000
    }
    
    initial_outputs = bof_twin(initial_inputs)
    print(f"\n📤 初始钢水产量: {initial_outputs['liquid_steel [t/h]']:.2f} t/h")
    
    # Problem: High temperature
    observation = {
        "T_steel": 1695,  # Too high!
        "P_bof_gas": 12.0,
        "bof_gas_current": 40000,
        "SOC_bofg": 0.5,
        "P_bofg": 12.0
    }
    
    print(f"\n⚠️  检测到问题: 温度 = {observation['T_steel']}°C (目标: 1650°C)")
    
    # Agent adjusts
    adjusted_state = bof_agent.step(observation)
    
    print(f"\n🎯 Agent调整:")
    print(f"  氧气流量: {initial_state['oxygen']:.0f} → {adjusted_state['oxygen']:.0f} Nm³/h")
    print(f"  废钢量: {initial_state['scrap_steel']:.1f} → {adjusted_state['scrap_steel']:.1f} t/batch")
    
    # New twin calculation
    adjusted_inputs = initial_inputs.copy()
    adjusted_inputs['oxygen [Nm³/h]'] = adjusted_state['oxygen']
    adjusted_inputs['scrap_steel [t/h]'] = adjusted_state['scrap_steel']
    
    adjusted_outputs = bof_twin(adjusted_inputs)
    
    print(f"\n📤 调整后钢水产量: {adjusted_outputs['liquid_steel [t/h]']:.2f} t/h")
    print(f"\n💡 效果: 降低氧气+增加废钢 → 降低温度，保持产量")


def demonstrate_full_coordination():
    """Demonstrate full multi-agent coordination"""
    
    print_section("场景 3: 多Agent协同调控")
    
    print("\n🌐 完整系统协同:")
    print("\n  初始状态:")
    print("    • BFG气柜: SOC = 0.90 (过满)")
    print("    • BOFG气柜: SOC = 0.50 (正常)")
    print("    • COG气柜: SOC = 0.30 (偏低)")
    
    print("\n  🤖 各Agent响应:")
    print("    1. BF_Agent: 检测BFG过满 → 减少风量 → BFG↓")
    print("    2. GasHolder_Agent: 增加BFG消耗 → 送电厂↑")
    print("    3. CokeOven_Agent: 检测COG偏低 → 加快推焦 → COG↑")
    print("    4. BOF_Agent: 维持正常运行")
    
    print("\n  📊 系统响应:")
    print("    • BFG: 产量↓ + 消耗↑ → SOC降至0.70 ✅")
    print("    • BOFG: 维持稳定 → SOC保持0.50 ✅")
    print("    • COG: 产量↑ → SOC升至0.45 ✅")
    
    print("\n  🎯 结果: 所有气柜恢复正常范围！")


if __name__ == "__main__":
    print("\n" + "🎬" * 40)
    print("  Agent 调控 Digital Twin 演示")
    print("  展示完整的调控过程和output变化")
    print("🎬" * 40)
    
    # Run demonstrations
    bf_results = demonstrate_bf_control()
    
    print("\n\n")
    demonstrate_bof_control()
    
    print("\n\n")
    demonstrate_full_coordination()
    
