"""
Twin Model Wrappers for MAS
Create symbolic links or wrappers to existing twin models
"""

import sys
import os

# Add parent directories to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import existing twins
from Digital_Twin.Blast_Furnace.Blast_Furnace_Twin_to_share import BlastFurnaceTwin
from Digital_Twin.BOF.BOF_Twin import BOFTwin
from Digital_Twin.Coke_Oven.Coke_Oven_Twin import CokeOvenTwin
from Digital_Twin.Gasholders.Gasholders import BFGH, BOFGH, COGH

# Re-export for easy import
__all__ = [
    'BlastFurnaceTwin',
    'BOFTwin', 
    'CokeOvenTwin',
    'BFGH',
    'BOFGH',
    'COGH'
]
