# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 17:13:28 2018
"""

from statsmodels.tsa.stattools import adfuller
import pandas as pd
from scipy import stats

def diff_nonstationary(x, alpha):
    
    """Returns number of differentiations required to transform
    a non-stationary time series into a stationary one. If 0 (zero) is
    returned, there's no need to differentiate."""
    """
    PARAMETERS:
    1) x - input time series
    2) alpha - significance level
    """
    
    i = 0 # no need to differentiate
    pvalue = adfuller(x, regression =
            ('ct' if
            stats.linregress( pd.Series(range(1, len(x)+1)), x ).pvalue<alpha
            else 'c')
            )[1]
    while pvalue>alpha:
        x = x.diff()
        pvalue = adfuller(x.dropna(),
            regression = 'c')[1]
        i += 1
        if pvalue<=alpha:
            break
    return(int(i))
    
### End of code