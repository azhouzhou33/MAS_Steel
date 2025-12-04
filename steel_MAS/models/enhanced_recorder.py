"""
Enhanced DataRecorder Extension

Extends the base DataRecorder class to support:
1. Transition recording (state, action, next_state, reward)
2. Standard interface integration
3. RL-ready data storage
"""

from typing import List, Optional
from models.standard_interfaces import (
    StandardState, StandardAction, Reward, Transition
)
from models.reward_calculation import calculate_reward, calculate_episode_metrics


class EnhancedDataRecorder:
    """
    Enhanced data recorder with full transition support.
    
    Records:
    - Complete (s, a, s', r) transitions for RL training
    - Backward compatible with legacy dict-based recording
    - Episode-level metrics
    """
    
    def __init__(self):
        # Standard interface data
        self.transitions: List[Transition] = []
        self.rewards: List[Reward] = []
        self.states: List[StandardState] = []
        self.actions: List[StandardAction] = []
        
        # Episode tracking
        self.episode_count: int = 0
        self.current_episode_steps: int = 0
    
    def record_transition(
        self,
        state: StandardState,
        action: StandardAction,
        next_state: StandardState,
        reward: Optional[Reward] = None,
        done: bool = False
    ):
        """
        Record a complete (s, a, s', r) transition.
        
        Args:
            state: Current StandardState
            action: StandardAction taken
            next_state: Resulting StandardState
            reward: Reward object (calculated if not provided)
            done: Whether episode is done
        """
        # Calculate reward if not provided
        if reward is None:
            reward = calculate_reward(state, action, next_state)
        
        # Create transition
        transition = Transition(
            state=state,
            action=action,
            next_state=next_state,
            reward=reward,
            step=len(self.transitions),
            done=done
        )
        
        # Store
        self.transitions.append(transition)
        self.rewards.append(reward)
        self.states.append(state)
        self.actions.append(action)
        
        self.current_episode_steps += 1
        
        if done:
            self.episode_count += 1
            self.current_episode_steps = 0
    
    def get_episode_metrics(self) -> dict:
        """Calculate metrics for current episode"""
        if not self.rewards:
            return {}
        
        return calculate_episode_metrics(self.rewards)
    
    def get_summary(self) -> str:
        """Return detailed summary of recorded data"""
        if not self.transitions:
            return "No transitions recorded yet."
        
        metrics = self.get_episode_metrics()
        
        summary = f"Enhanced DataRecorder Summary:\n"
        summary += f"  Total transitions: {len(self.transitions)}\n"
        summary += f"  Episodes completed: {self.episode_count}\n"
        summary += f"  Current episode steps: {self.current_episode_steps}\n"
        summary += f"\nReward Metrics:\n"
        summary += f"  Mean total reward: {metrics.get('mean_total', 0):.3f}\n"
        summary += f"  Cumulative reward: {metrics.get('cumulative_reward', 0):.2f}\n"
        summary += f"  Mean production: {metrics.get('mean_production', 0):.3f}\n"
        summary += f"  Mean stability: {metrics.get('mean_stability', 0):.3f}\n"
        summary += f"  Mean efficiency: {metrics.get('mean_efficiency', 0):.3f}\n"
        
        return summary
    
    def export_transitions(self, filepath: str):
        """
        Export transitions to JSON for offline analysis/training.
        
        Args:
            filepath: Output JSON file path
        """
        import json
        
        data = {
            "transitions": [t.to_dict() for t in self.transitions],
            "metrics": self.get_episode_metrics(),
            "metadata": {
                "total_transitions": len(self.transitions),
                "episodes": self.episode_count
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[OK] Exported {len(self.transitions)} transitions to {filepath}")
    
    def get_last_n_transitions(self, n: int = 10) -> List[Transition]:
        """Get last n transitions"""
        return self.transitions[-n:]
    
    def get_state_history(self) -> List[StandardState]:
        """Get all recorded states"""
        return self.states
    
    def get_action_history(self) -> List[StandardAction]:
        """Get all recorded actions"""
        return self.actions
    
    def get_reward_history(self) -> List[Reward]:
        """Get all recorded rewards"""
        return self.rewards
