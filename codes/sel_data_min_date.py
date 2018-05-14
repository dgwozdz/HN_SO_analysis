# -*- coding: utf-8 -*-
"""
Created on Sat May 12 14:44:39 2018
"""

def sel_data_min_date(data, group_var, date_var, var1, var2): # sel = select
    
    """Returns a data set with excluded lacks of data. Observations
    with zeroes as values before the first observation with nonzero values
    are considered lacks of data"""
    """
    PARAMETERS:
    1) data - input data frame
    2) group_var - grouping variable on the basis of which the data
        set is divided into groups
    3) date_var - variable with time index
    4) var1 - first variable for which all observations should be greater
        than zero
    4) var2 - first variable for which all observations should be greater
    than zero
    """
    
    import pandas as pd
    
    new_data = pd.DataFrame(columns = data.columns.values)
    
    for i in set(data[group_var]):
        min_date = (data.loc[(data[group_var] == i) &
                           ((data[var1] > 0) |
                                   (data[var2]>0))].date.min()
                           .strftime('%Y-%m-%d'))
        tech_data = data[(data[group_var] == i) & (data[date_var] >= min_date)]
        new_data = pd.concat([new_data, tech_data], axis = 0)
    return(new_data)

### End of code