# Import useful libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy as sp
import statsmodels.api as sm
import sklearn
import datetime
import yfinance as yf
import seaborn as sns
import random
import math
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal
from scipy.signal import StateSpace
from typing import Optional, List
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sys
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

import pandas as pd
import numpy as np
import xgboost as xgb
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt


# Useful functions
def information(input):
    print("The array is : \n", input)
    print(" ")
    print("type:", type(input))
    print("sys.getsizeof (Python object size) KB:", sys.getsizeof(input) / (1024))
    print("dtype:", input.dtype)
    print("shape:", input.shape)
    print(" ")
    
################################################################################################################################# 

# Define PP state space
# Define A,B,C,D

A_PP = np.array([
    [0.9275, -0.3135],
    [-0.0856, 0.2482]
])

B_PP = 1.0e-03 * np.array([
    [0.0374, 0.0544, 0.3203, 0.1426, -0.0568, 0.1194],
    [0.0730, 0.0962, 0.7956, 0.2623, -0.1350, 0.2562]
])

C_PP = 1.0e-03 * np.array([
    [1.2313, -0.0577]
])

D_PP = np.zeros((1, 6))

# Initial state
x_PP = np.array([
    0.2180,
    0.1180  
])

print("A is :")
information(A_PP)
print("\n")

print("B is :")
information(B_PP)
print("\n")

print("C is :")
information(C_PP)
print("\n")

#############################################################



class PowerPlant :
    """
    Class describing State space Power plant ouput power
    
    Parameters :
    
    State dimension : n = 2, 
    Input dimension : m = 6, 
    Output dimensions : p = 1
    
    A : n x n (ndarray, dtype = float)
    B : n x m (ndarray, dtype = float)
    C : p x n (ndarray, dtype = float)
    D : p x m (ndarray, dtype = float)
    x0: n x 1 (ndarray, dtype = float)
    
    Input : 
    u : m dimensional vector containing input power [MW]
    
    Output :
    y : p dimensional vector containing output Powerplant power [MW]

    """
    
    def __init__(self, A : np.ndarray = A_PP  , B : np.ndarray = B_PP, C : np.ndarray = C_PP, D : np.ndarray = D_PP, x0 : np.ndarray = x_PP, input_names : Optional[List[str]] = None, output_names : Optional[List[str]] = None) :
        """
        
        Parameters : 
        
        A : n x n (ndarray, dtype = float)
        B : n x m (ndarray, dtype = float)
        C : p x n (ndarray, dtype = float)
        D : p x m (ndarray, dtype = float)
        x0: n x 1 (ndarray, dtype = float)
        input_names : List of strings ( m dimensional ) ; type([List[str]])
        output_names : List of strings ( p dimensional ) ; type([List[str]])
        
        """
        
        # Declare state space
        self.A = np.array(A, dtype = float)
        self.B = np.array(B, dtype = float)
        self.C = np.array(C, dtype = float)
        self.D = np.array(D, dtype = float)
        self.x = np.array(x0, dtype = float)
        
        # declare dimensions
        n, m = self.B.shape
        p, _ = self.C.shape
        
        # Check
        assert self.A.shape == (n,n), f" A must be a square matrix {n} x {n}"
        assert self.B.shape == (n,m), f" B must be a matrix {n} x {m}"
        assert self.C.shape == (p,n), f" C must be a matrix {p} x {n}"
        assert self.D.shape == (p,m), f" D must be a matrix {p} x {m}"
        
        self.input_names = input_names if input_names else [f"u{i}" for i in range(m)]
        self.output_names = output_names if output_names else [f"y{i}" for i in range(p)]
        
    
    def __call__(self, input_dict : dict) -> dict:
        """
        
        Compute output y_{k} = C * x_{k} + D * u_{k} given current state and input.
        Compute  x_{k+1} = A * x_{k} + B * u_{k} given current state and input.
        
        input_dict: {input_name: value} --> {input_name_1 : value_1, input_name_2 : value_2, ..., }
        return: {output_name: value} --> {output_name_1 : value_1, output_name_2 : value_2, ...., }
        
        """
        
        # declare dimensions
        n, m = self.B.shape
        p, _ = self.C.shape
        
        # create u vector of m dimension with values in input names
        u = np.array ( [input_dict[name] for name in self.input_names ], dtype = float )
        
        assert u.shape == (m,), f"u must be {m} dimensional"
        
        # update x_{k+1} = A * x_{k} + B * u_{k}
        self.x = self.A @ self.x + self.B @ u
        
        assert self.x.shape == (n,), f"x must be {n} dimensional"
        
        y = self.C @ self.x + self.D @ u
        
        assert self.y.shape == (p,), f"y must be {p} dimensional"
        
        return {name: y[i] for i, name in enumerate(self.output_names) }