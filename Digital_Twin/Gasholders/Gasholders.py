"""
GasHolders Digital Twin Models
State-space models for BFG, BOFG, and COG gasholders
"""

import numpy as np
from typing import Optional, List


# ==============================================================================
# BFGH (Blast Furnace Gas Holder) Parameters
# ==============================================================================
# Define A, B, C, D matrices for BFGH
A_BFGH = np.array([0.994])
B_BFGH = np.array([3.135 * 1e-6])
C_BFGH = np.array([3.49416 * 1e6])

# Initial state
x_BFGH = np.array([0.004])


# ==============================================================================
# BOFGH (BOF Gas Holder) Parameters
# ==============================================================================
# Define A, B, C, D matrices for BOFGH
A_BOFGH = np.array([0.999])
B_BOFGH = np.array([7.2884 * 1e-6])
C_BOFGH = np.array([3.2121 * 1e6])

# Initial state
x_BOFGH = np.array([0.0049])


# ==============================================================================
# COGH (Coke Oven Gas Holder) Parameters
# ==============================================================================
# Define A, B, C, D matrices for COGH
A_COGH = np.array([1])
B_COGH = np.array([1.7187 * 1e-6])
C_COGH = np.array([1.0066 * 1e6])

# Initial state
x_COGH = np.array([0.0045])


# ==============================================================================
# Base State Space Class
# ==============================================================================
class StateSpaceGasHolder:
    """
    Base class for Gas Holder state-space models
    
    State-space representation:
        x_{k+1} = A * x_k + B * u_k
        y_k = C * x_k + D * u_k
    
    Parameters:
        State dimension: n = 1
        Input dimension: m = 1
        Output dimension: p = 1
    
    Where:
        - x ∈ R^n is the state vector
        - u ∈ R^m is the input vector (output gas [kNm³/h])
        - y ∈ R^p is the output vector (Gasholder level percentage [])
        - A ∈ R^{n×n} is the system matrix
        - B ∈ R^{n×m} is the input matrix
        - C ∈ R^{p×n} is the output matrix
        - D ∈ R^{p×m} is the feedthrough matrix
    """
    
    def __init__(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray = 0,
        x0: np.ndarray = None,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None
    ):
        """
        Initialize the state-space gas holder model
        
        Parameters:
            A: n x n system matrix (ndarray, dtype=float)
            B: n x m input matrix (ndarray, dtype=float)
            C: p x n output matrix (ndarray, dtype=float)
            D: p x m feedthrough matrix (ndarray, dtype=float)
            x0: n x 1 initial state (ndarray, dtype=float)
            input_names: List of input variable names (m dimensional)
            output_names: List of output variable names (p dimensional)
        """
        # Declare state space matrices
        self.A = np.atleast_2d(np.array(A, dtype=float))
        self.B = np.atleast_2d(np.array(B, dtype=float))
        self.C = np.atleast_2d(np.array(C, dtype=float))
        self.D = np.atleast_2d(np.array(D, dtype=float))
        self.x = np.array(x0, dtype=float).flatten() if x0 is not None else np.zeros(1)
        
        # Get dimensions
        n, m = self.B.shape
        p, _ = self.C.shape
        
        # Dimension checks
        assert self.A.shape == (n, n), f"A must be a square matrix {n} x {n}"
        assert self.B.shape == (n, m), f"B must be a matrix {n} x {m}"
        assert self.C.shape == (p, n), f"C must be a matrix {p} x {n}"
        assert self.D.shape == (p, m), f"D must be a matrix {p} x {m}"
        
        # Set input/output names
        self.input_names = input_names if input_names else [f"u{i}" for i in range(m)]
        self.output_names = output_names if output_names else [f"y{i}" for i in range(p)]
    
    def __call__(self, input_dict: dict) -> dict:
        """
        Execute one time step of the state-space model
        
        Computes:
            y_k = C * x_k + D * u_k (output at current step)
            x_{k+1} = A * x_k + B * u_k (state update)
        
        Args:
            input_dict: Dictionary mapping input names to values
                       {input_name_1: value_1, input_name_2: value_2, ...}
        
        Returns:
            Dictionary mapping output names to values
            {output_name_1: value_1, output_name_2: value_2, ...}
        """
        # Get dimensions
        n, m = self.B.shape
        p, _ = self.C.shape
        
        # Extract input vector from dictionary
        u = np.array([input_dict[name] for name in self.input_names], dtype=float)
        assert u.shape == (m,), f"u must be {m} dimensional"
        
        # Compute output: y_k = C * x_k + D * u_k
        y = self.C @ self.x + self.D @ u
        assert y.shape == (p,), f"y must be {p} dimensional"
        
        # Update state: x_{k+1} = A * x_k + B * u_k
        self.x = self.A @ self.x + self.B @ u
        assert self.x.shape == (n,), f"x must be {n} dimensional"
        
        # Return output dictionary
        return {name: y[i] for i, name in enumerate(self.output_names)}
    
    def reset(self, x0: Optional[np.ndarray] = None):
        """Reset the state to initial or specified value"""
        if x0 is not None:
            self.x = np.array(x0, dtype=float)
        else:
            self.x = np.zeros_like(self.x)


# ==============================================================================
# Specific Gas Holder Classes
# ==============================================================================

class BFGH(StateSpaceGasHolder):
    """
    Blast Furnace Gas Holder (BFGH)
    
    Input:
        u: Gas output [kNm³/h]
    
    Output:
        y: Gasholder level percentage []
    """
    
    def __init__(
        self,
        A: np.ndarray = A_BFGH,
        B: np.ndarray = B_BFGH,
        C: np.ndarray = C_BFGH,
        D: np.ndarray = 0,
        x0: np.ndarray = x_BFGH,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None
    ):
        super().__init__(A, B, C, D, x0, input_names, output_names)


class BOFGH(StateSpaceGasHolder):
    """
    BOF Gas Holder (BOFGH)
    
    Input:
        u: Gas output [kNm³/h]
    
    Output:
        y: Gasholder level percentage []
    """
    
    def __init__(
        self,
        A: np.ndarray = A_BOFGH,
        B: np.ndarray = B_BOFGH,
        C: np.ndarray = C_BOFGH,
        D: np.ndarray = 0,
        x0: np.ndarray = x_BOFGH,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None
    ):
        super().__init__(A, B, C, D, x0, input_names, output_names)


class COGH(StateSpaceGasHolder):
    """
    Coke Oven Gas Holder (COGH)
    
    Input:
        u: Gas output [kNm³/h]
    
    Output:
        y: Gasholder level percentage []
    """
    
    def __init__(
        self,
        A: np.ndarray = A_COGH,
        B: np.ndarray = B_COGH,
        C: np.ndarray = C_COGH,
        D: np.ndarray = 0,
        x0: np.ndarray = x_COGH,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None
    ):
        super().__init__(A, B, C, D, x0, input_names, output_names)


# ==============================================================================
# Test/Demo Code
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Gas Holders State-Space Models - Demo")
    print("=" * 60)
    
    # Test BFGH
    print("\n1. BFGH (Blast Furnace Gas Holder)")
    print("-" * 60)
    bfgh = BFGH(input_names=["gas_output_BFG"], output_names=["level_BFGH"])
    
    # Simulate a few time steps
    gas_flows = [100, 120, 110, 105, 115]  # kNm³/h
    
    for i, gas in enumerate(gas_flows):
        result = bfgh({"gas_output_BFG": gas})
        print(f"Step {i+1}: Gas Output = {gas} kNm³/h → Level = {result['level_BFGH']:.4f}")
    
    # Test BOFGH
    print("\n2. BOFGH (BOF Gas Holder)")
    print("-" * 60)
    bofgh = BOFGH(input_names=["gas_output_BOFG"], output_names=["level_BOFGH"])
    
    for i, gas in enumerate(gas_flows):
        result = bofgh({"gas_output_BOFG": gas})
        print(f"Step {i+1}: Gas Output = {gas} kNm³/h → Level = {result['level_BOFGH']:.4f}")
    
    # Test COGH
    print("\n3. COGH (Coke Oven Gas Holder)")
    print("-" * 60)
    cogh = COGH(input_names=["gas_output_COG"], output_names=["level_COGH"])
    
    for i, gas in enumerate(gas_flows):
        result = cogh({"gas_output_COG": gas})
        print(f"Step {i+1}: Gas Output = {gas} kNm³/h → Level = {result['level_COGH']:.4f}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
