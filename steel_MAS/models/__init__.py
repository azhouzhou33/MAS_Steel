"""
Data models for Multi-Agent System
"""

from .twin_data import (
    BFInput, BFOutput,
    BOFInput, BOFOutput,
    CokeOvenInput, CokeOvenOutput,
    GasHolderInput, GasHolderOutput
)
from .gas_network import GasNetwork, GasNetworkState

__all__ = [
    'BFInput', 'BFOutput',
    'BOFInput', 'BOFOutput',
    'CokeOvenInput', 'CokeOvenOutput',
    'GasHolderInput', 'GasHolderOutput',
    'GasNetwork', 'GasNetworkState'
]
