# -*- coding: utf-8 -*-
"""
Created on Wed May  9 19:14:49 2018
"""


def calc_granger_causality(x, diff_x, granger_list, group_var, groups, maxlag,
                           both_sides = False, only_min_crit = False,
                           filter_p_value = None):
    
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
    from useful import repeated
    from grangercausalitytests_mod import grangercausalitytests_mod
    from statsmodels.regression.linear_model import OLSResults
    
    if both_sides == True:
        granger_list_reversed = [x[::-1] for x in granger_list]
        granger_list = granger_list.copy()
        granger_list.extend(granger_list_reversed)
        len_granger_list = len(granger_list)
    
    if only_min_crit:
        results = pd.DataFrame(columns=['ID', 'group', 'y', 'y_diff', 'x',
                                     'x_diff', 'lag', 'p_value', 'AIC', 'BIC',
                                    'min_AIC', 'min_BIC'])
    else:
        results = pd.DataFrame(columns=['ID', 'group', 'y', 'y_diff', 'x',
                                         'x_diff','lag', 'p_value', 'AIC',
                                          'BIC'])
    
    for g in groups:
        for i, gl in enumerate(granger_list):
            
            if both_sides: # reversed pairs
                if i>=len_granger_list/2:
                    i = i - len_granger_list/2 # ID of reversed pair equals
                    # to the ID of the original pair:
                    # ID(Y~X) = ID(X~Y)
                    
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
                    {'ID': np.repeat(i, maxlag),
                     'group': np.repeat(g, maxlag),
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
            if only_min_crit:
                min_AIC = df.loc[df.AIC == min(df.AIC)]
                min_BIC = df.loc[df.BIC == min(df.BIC)]
                if min_AIC.equals(min_BIC):
                    min_AIC = min_AIC.assign(min_AIC = True)
                    min_AIC = min_AIC.assign(min_BIC = True)
                    df = min_AIC
                else: 
                    min_AIC = min_AIC.assign(min_AIC = True)
                    min_AIC = min_AIC.assign(min_BIC = False)
                    min_BIC = min_BIC.assign(min_AIC = False)
                    min_BIC = min_BIC.assign(min_BIC = True)
                    df = pd.concat([min_AIC, min_BIC], axis = 0)
            results = (pd.concat([results, df], axis = 0)
            .sort_values(by = ['group', 'ID'])
            .reset_index(drop=True))
    if filter_p_value is not None:
        return(results[results.p_value<filter_p_value])
    else:
        return(results)
    
### End of code