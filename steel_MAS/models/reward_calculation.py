"""
Reward Calculation Module

Calculates multi-objective rewards for MAS performance evaluation.
This module supports both Rule-based agent evaluation and future RL training.
"""

from typing import Dict
from models.standard_interfaces import StandardState, StandardAction, Reward


def calculate_reward(
    state: StandardState,
    action: StandardAction,
    next_state: StandardState
) -> Reward:
    """
    Calculate multi-objective reward for state transition
    
    Reward components:
    1. Production score: Favors higher BFG production (proxy for output)
    2. Stability score: Penalizes SOC out of safe bounds [0.25, 0.85]
    3. Efficiency score: Rewards good gas utilization
    
    Args:
        state: Current state
        action: Action taken
        next_state: Resulting state
    
    Returns:
        Reward object with detailed breakdown
    """
    
    # === 1. Production Score ===
    # Normalize BFG production to [0, 1]
    # Nominal: 116,000 Nm³/h, max: ~140,000
    bf_bfg = next_state.production.bf_bfg_supply
    production_score = min(bf_bfg / 140000.0, 1.0)
    
    # === 2. Stability Score ===
    # Penalize SOC out of bounds [0.25, 0.85]
    soc_bfg = next_state.gas_holder.soc_bfg
    soc_bofg = next_state.gas_holder.soc_bofg
    soc_cog = next_state.gas_holder.soc_cog
    
    soc_penalties = []
    for soc in [soc_bfg, soc_bofg, soc_cog]:
        if soc < 0.25:
            soc_penalties.append(0.25 - soc)  # Under-fill penalty
        elif soc > 0.85:
            soc_penalties.append(soc - 0.85)  # Over-fill penalty
    
    total_soc_penalty = sum(soc_penalties)
    stability_score = max(0.0, 1.0 - total_soc_penalty * 2.0)  # Scale penalty
    
    # === 3. Efficiency Score ===
    # Gas utilization = consumption / (supply + 1e-6)
    # Higher = better utilization
    
    total_supply = (
        next_state.production.bf_bfg_supply +
        next_state.production.bof_bofg_supply +
        next_state.production.coke_cog_supply
    )
    
    total_consumption = (
        action.gas_allocation.bfg_to_power_plant +
        action.gas_allocation.bfg_to_heating +
        action.gas_allocation.bofg_to_power_plant +
        action.gas_allocation.cog_to_bf +
        action.gas_allocation.cog_to_heating
    )
    
    # Target utilization ~0.8 (allow 20% reserve)
    utilization = total_consumption / (total_supply + 1e-6)
    if utilization >= 0.7 and utilization <= 0.9:
        efficiency_score = 1.0  # Optimal range
    elif utilization < 0.7:
        efficiency_score = utilization / 0.7  # Under-utilization penalty
    else:  # > 0.9
        efficiency_score = max(0.0, 1.0 - (utilization - 0.9) * 5.0)  # Over-utilization penalty
    
    # === Weighted Total ===
    weights = {
        "production": 0.4,
        "stability": 0.4,
        "efficiency": 0.2
    }
    
    total = (
        weights["production"] * production_score +
        weights["stability"] * stability_score +
        weights["efficiency"] * efficiency_score
    )
    
    # Detailed breakdown for debugging
    breakdown = {
        "bf_bfg_supply": bf_bfg,
        "soc_penalty_total": total_soc_penalty,
        "soc_bfg": soc_bfg,
        "soc_bofg": soc_bofg,
        "soc_cog": soc_cog,
        "utilization": utilization,
        "total_supply": total_supply,
        "total_consumption": total_consumption,
    }
    
    return Reward(
        production_score=production_score,
        stability_score=stability_score,
        efficiency_score=efficiency_score,
        total=total,
        breakdown=breakdown
    )


def calculate_episode_metrics(rewards: list) -> Dict[str, float]:
    """
    Calculate aggregate metrics over an episode
    
    Args:
        rewards: List of Reward objects from each step
    
    Returns:
        Dict with mean/std of reward components
    """
    import numpy as np
    
    production_scores = [r.production_score for r in rewards]
    stability_scores = [r.stability_score for r in rewards]
    efficiency_scores = [r.efficiency_score for r in rewards]
    total_rewards = [r.total for r in rewards]
    
    return {
        "mean_production": np.mean(production_scores),
        "mean_stability": np.mean(stability_scores),
        "mean_efficiency": np.mean(efficiency_scores),
        "mean_total": np.mean(total_rewards),
        "std_total": np.std(total_rewards),
        "cumulative_reward": np.sum(total_rewards),
        "min_total": np.min(total_rewards),
        "max_total": np.max(total_rewards),
    }
