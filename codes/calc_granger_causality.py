# -*- coding: utf-8 -*-
"""
Created on Wed May  9 19:14:49 2018
"""


def calc_granger_causality(x, diff_x, granger_list, group_var, groups, maxlag):
    
    """Computes Granger Cauusality test for two given time series.
    Takes into consideration time series differencing on the basis of
    results produced by """
    """
    PARAMETERS:
    1) x - input time series
    2) alpha - significance level
    """
    
    import pandas as pd
    import numpy as np
    from warnings import warn
    from useful import repeated
    from grangercausalitytests_mod import grangercausalitytests_mod
    from statsmodels.regression.linear_model import OLSResults
    
    results = pd.DataFrame(columns=['group', 'y', 'y_diff', 'x', 'x_diff',
                                    'lag', 'p_value', 'AIC', 'BIC'])
    
    for g in groups:
        for gl in granger_list:
            yvar_diffs = int(diff_x.at[g, gl[0]])
            yvar = repeated(pd.DataFrame.diff,
                            yvar_diffs)(x[x[group_var] == g][gl[0]])
#            if len(yvar) <= 3 * maxlag + 1: # +1 = constant
#                warn("The maximum lag was too large")
#            else:
            xvar_diffs = int(diff_x.at[g, gl[1]])
            xvar = repeated(pd.DataFrame.diff,
                            xvar_diffs)(x[x[group_var] == g][gl[1]])
            gstats = grangercausalitytests_mod(
                    (pd.concat([yvar, xvar], axis=1).dropna()),
                    maxlag = maxlag, verbose = False
                    )

            df = pd.DataFrame(
                    {'group': np.repeat(g, maxlag),
                     'y': np.repeat(gl[0], maxlag),
                     'y_diff': np.repeat(yvar_diffs, maxlag),
                     'x': np.repeat(gl[1], maxlag),
                     'x_diff': np.repeat(xvar_diffs, maxlag),
                     'lag': range(1, maxlag+1),
                     'p_value': [gstats[x][0]['ssr_ftest'][1]
                                     for x in range(1, maxlag+1)],
                     'AIC': [OLSResults.aic(gstats[x][1][1])
                                     for x in range(1, maxlag+1)],
                     'BIC': [OLSResults.bic(gstats[x][1][1])
                                     for x in range(1, maxlag+1)],
                     }
                 )
            results = pd.concat([results, df], axis = 0)
    return(results.reset_index(drop=True))
    
### End of code