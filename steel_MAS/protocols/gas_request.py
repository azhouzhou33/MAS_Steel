"""
Communication Protocols for Multi-Agent System
Defines message types for inter-agent communication
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """Types of messages agents can send"""
    GAS_REQUEST = "gas_request"
    GAS_RESPONSE = "gas_response"
    BOFG_SURGE_WARNING = "bofg_surge_warning"
    STATE_BROADCAST = "state_broadcast"
    EMERGENCY_ALERT = "emergency_alert"


@dataclass
class Message:
    """Base message class"""
    msg_type: MessageType
    sender: str
    receiver: str
    timestamp: float
    data: Dict[str, Any]


@dataclass
class GasRequest:
    """Request for gas allocation"""
    requester: str
    gas_type: str  # 'BFG', 'BOFG', 'COG'
    amount_requested: float  # Nm³/h
    priority: int  # Higher = more important
    purpose: str  # 'heating', 'power_plant', etc.
    
    def to_message(self, timestamp: float) -> Message:
        return Message(
            msg_type=MessageType.GAS_REQUEST,
            sender=self.requester,
            receiver="GasHolderAgent",
            timestamp=timestamp,
            data={
                "gas_type": self.gas_type,
                "amount": self.amount_requested,
                "priority": self.priority,
                "purpose": self.purpose
            }
        )


@dataclass
class GasResponse:
    """Response to gas request"""
    allocated_amount: float
    available_amount: float
    allocation_ratio: float  # allocated / requested
    
    def to_message(self, sender: str, receiver: str, timestamp: float) -> Message:
        return Message(
            msg_type=MessageType.GAS_RESPONSE,
            sender=sender,
            receiver=receiver,
            timestamp=timestamp,
            data={
                "allocated": self.allocated_amount,
                "available": self.available_amount,
                "ratio": self.allocation_ratio
            }
        )


@dataclass
class BOFGSurgeWarning:
    """Warning about upcoming BOFG surge"""
    time_to_blow: float  # minutes
    expected_peak: float  # Nm³/h
    duration: float  # minutes
    current_gh_soc: float  # Current gas holder SOC
    
    def to_message(self, timestamp: float) -> Message:
        return Message(
            msg_type=MessageType.BOFG_SURGE_WARNING,
            sender="BOFAgent",
            receiver="GasHolderAgent",
            timestamp=timestamp,
            data={
                "time_to_blow": self.time_to_blow,
                "expected_peak": self.expected_peak,
                "duration": self.duration,
                "gh_soc": self.current_gh_soc
            }
        )


@dataclass
class StateBroadcast:
    """Broadcast current state to all agents"""
    agent_name: str
    state: Dict[str, Any]
    
    def to_message(self, timestamp: float) -> Message:
        return Message(
            msg_type=MessageType.STATE_BROADCAST,
            sender=self.agent_name,
            receiver="all",
            timestamp=timestamp,
            data=self.state
        )


class MessageBus:
    """
    Simple message bus for agent communication
    """
    
    def __init__(self):
        self.messages = []
        self.time = 0.0
    
    def send(self, message: Message):
        """Send a message"""
        self.messages.append(message)
    
    def get_messages(self, receiver: str, msg_type: Optional[MessageType] = None):
        """Get messages for a specific receiver"""
        filtered = [
            msg for msg in self.messages
            if (msg.receiver == receiver or msg.receiver == "all")
        ]
        
        if msg_type:
            filtered = [msg for msg in filtered if msg.msg_type == msg_type]
        
        return filtered
    
    def clear(self):
        """Clear all messages"""
        self.messages = []
    
    def update_time(self, time: float):
        """Update simulation time"""
        self.time = time
