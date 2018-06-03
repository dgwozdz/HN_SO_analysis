List of used codes

1) kaggle_data.py - code for obtaining data from Kaggle
2) stack_queries.sql - queries to obtain data from StackOverflow; since Data Explorer allows to return only 50 thousand rows at once, queries had to be divided
3) 00_main.py - main code in Python wrangling data and producing plots
4) hn_plots.py - function to plot time series
5) sel_data_min_date - returns a data set with excluded lacks of data. Observations with zeroes as values before the first observation with nonzero values are considered lacks of data
6) grangercausalitytests_mod - modified Granger causality test; does not take into consideration observations for the potential cause from period "t" (period which is forecasted OLS model)
7) diff_nonstationary - function to differentiate nonstationary time series
8) calc_granger_causality - conducts Granger causality test for two variables in groups
9) useful - useful functions from the web