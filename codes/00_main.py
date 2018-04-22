# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 22:03:26 2018
"""

#### 0. Loading libraries, setting working directory

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import gc
import timeit
from functools import reduce
from itertools import chain
from datetime import datetime

from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from sklearn import linear_model
from scipy import stats


os.chdir('F:\Damian\github\HN_SO_analysis\HN_SO_analysis\codes')
from hn_plots import hn_plots, todays_date
from diff_nonstationary import diff_nonstationary
from useful import repeated # Useful function from the Web

os.chdir('F:\Damian\github\HN_SO_analysis\HN_SO_analysis')

### 1. Stack Overflow data
 
stack_data1 = pd.read_csv('.\\stack_data\\tags_per_day_1_20180325.csv')
stack_data2 = pd.read_csv('.\\stack_data\\tags_per_day_2_20180306.csv')
stack_data3 = pd.read_csv('.\\stack_data\\tags_per_day_3_20180306.csv')
stack_data4 = pd.read_csv(
        '.\\stack_data\\tags_per_day_4_d3js_tensorflow_20180403.csv')

stack_data = pd.concat([stack_data1, stack_data2, stack_data3, stack_data4])

stack_data['tags'] = stack_data['tags'].str.replace('<', '').str.replace('>', '')
stack_data['post_date'] = pd.to_datetime(stack_data['post_date'])
stack_data.loc[stack_data['tags'] == 'd3js'].describe()


del stack_data1, stack_data2, stack_data3, stack_data4

stack_data.tags.replace('apache-spark', 'spark', inplace = True)
stack_data.tags.replace('d3.js', 'd3js', inplace = True)
stack_data = stack_data.rename(columns = {'score_sum': 'so_score_sum',
                                          'views': 'so_views',
                                          'answers': 'so_answers',
                                          'favorites': 'so_favorites',
                                          'comments': 'so_comments',
                                          'usage_cnt': 'so_usage_cnt'})
    
### 2. Kaggle data

kaggle_data_raw = pd.read_csv('.\\kaggle_data\\kaggle_data_20180414_1358.csv')
kaggle_data_raw = kaggle_data_raw[
        (kaggle_data_raw.title_match.isnull() == False) |
        (kaggle_data_raw.text_match.isnull() == False)]

idx = pd.date_range('01-01-2006', '31-12-2017')

for i in ['text_match', 'title_match']:
    kaggle_data_raw.loc[:, i] = (kaggle_data_raw[i].str.replace('[', '')
    .str.replace(']', '')
    .str.replace("'", '')
    .str.replace(" ", "")
    .str.replace("\\\\n", "")
    .str.replace("\\\\t", "")
    .str.replace(".", "")
    .str.replace("?", "")
    .str.replace("!", "")
    .str.replace("d3js", "d3") # Simplification: d3 and d3js to d3js
    .str.replace("d3", "d3js"))
    
check = list(kaggle_data_raw.loc[:, 'text_match'].unique())

# Combining title and text matches

kaggle_data_raw['all_match'] = (kaggle_data_raw['text_match']
    +','+ kaggle_data_raw['title_match'])
kaggle_list = []

## Cutoffs for scores of topics on HN:
# if the score of a given topic
# was smaller than the declared number, it won't be taken into calculation;
# `None` means lack of such restriction
cutoffs = [None, 10, 25]


from sklearn.preprocessing import MultiLabelBinarizer
for cutoff in cutoffs:
    if cutoff == None:
        kaggle_data_loop = kaggle_data_raw.copy()
        cutoff_lbl = ''
    else:
        kaggle_data_loop = kaggle_data_raw.loc[kaggle_data_raw['score']>=cutoff]
    for i in ['text_match', 'title_match', 'all_match']:
        
        # Removal of duplicates
        before = kaggle_data_loop[i]
        kaggle_data_loop.loc[:, i] = [list(set(x))
                                    for x in kaggle_data_loop[i].str.split(',')]
        
        # Summing the scores per date and text/title match
        s = kaggle_data_loop[i].str.len()
        df = pd.DataFrame({'date': kaggle_data_loop.date.repeat(s),
                           'score': kaggle_data_loop.score.repeat(s),
                           i: np.concatenate(kaggle_data_loop[i].values) })
        df = df.loc[df[i] != '']
        kaggle_data_score = pd.pivot_table(df,
                    index = 'date', columns = i, values = 'score',
                   aggfunc = 'sum', fill_value = 0)
        kaggle_data_score.index = pd.DatetimeIndex(
        kaggle_data_score.index)
        
        kaggle_data_score = kaggle_data_score.reindex(
                idx, fill_value = 0).stack().reset_index()
        colnames = ['date', 'tech', 'hn_' + i] # hn = Hacker News
        kaggle_data_score.columns = list(chain.from_iterable([colnames[0:2], [colnames[2] + '_score' + cutoff_lbl]]))
        kaggle_list.append(kaggle_data_score)
    
    # Filling the lacking dates with zeroes for counts

    mlb = MultiLabelBinarizer()
    kaggle_data_cnt = pd.DataFrame(
            mlb.fit_transform(kaggle_data_loop[i]),
            kaggle_data_loop.date, mlb.classes_).sum(level = 0)
    kaggle_data_cnt.index = pd.DatetimeIndex(kaggle_data_cnt.index)
    kaggle_data_cnt = kaggle_data_cnt.reindex(idx, fill_value = 0).stack().reset_index()
    kaggle_data_cnt.columns = list(chain.from_iterable([colnames[0:2], [colnames[2] + '_cnt' + cutoff_lbl]]))
    kaggle_data_cnt = kaggle_data_cnt.groupby(['date', 'tech']).sum().reset_index()
    kaggle_data_cnt = kaggle_data_cnt[kaggle_data_cnt.tech != '']
    kaggle_list.append(kaggle_data_cnt)

### 3. Merging data from stack overflow and kaggle into one data frame
    
kaggle_data = reduce(lambda df1, df2:
    df1.merge(df2, how = 'outer', on = ['date', 'tech']), kaggle_list)
kaggle_data.date = pd.to_datetime(kaggle_data.date)
data = (pd.merge(kaggle_data, stack_data, how = 'left',
                left_on = ['date', 'tech'], right_on = ['post_date', 'tags'])
        .drop(['post_date', 'tags'], axis = 1)
        .fillna(0))

del kaggle_list, kaggle_data_raw, kaggle_data

### 4. Data exclusions

# Swift appeared 2nd June 2014: all the data befor this date from Hacker News
# should be dropped

data.drop(data[(data['tech'] == 'swift') & (data['date'] < '2014-06-02')].index |
        data[(data['tech'] == 'spark') & (data['date'] < '2014-05-30')].index |
        data[data['date'] < '2008-09-13'].index, # two days for differences of differences
        # 2007-02-19 - launch of StackOverflow
                inplace = True)

### 5. Plotting time series
## Monthly frequency

#hn_plots(data = data, freq = 'M',
#         output_date = todays_date(),
#             select_tech = ['d3js', 'tensorflow', 'javascript'],
#             common_var = 'hn_all_match_cnt',
#             common_var3 = 'hn_all_match_score',
#             common_var4 = 'hn_all_match_score',
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_usage_cnt',
#             var4 = 'so_score_sum',
#             subfolder = 'plots')
#
#hn_plots(data = data, freq = 'M',
#         output_date = todays_date(),
#             select_tech = ['d3js', 'tensorflow', 'javascript'],
#             common_var = 'hn_all_match_cnt_10',
#             common_var3 = 'hn_all_match_score_10',
#             common_var4 = 'hn_all_match_score_10',
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_usage_cnt',
#             var4 = 'so_score_sum',
#             subfolder = 'plots')
#
#hn_plots(data = data, freq = 'M',
#         output_date = todays_date(),
#             select_tech = ['d3js', 'tensorflow', 'javascript'],
#             common_var = 'hn_all_match_cnt_25',
#             common_var3 = 'hn_all_match_score_25',
#             common_var4 = 'hn_all_match_score_25',
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_usage_cnt',
#             var4 = 'so_score_sum',
#             subfolder = 'plots')

### 6. Testing for nonstationarity

# 6.1 Plotting data to visually identify a trend
hn_plots(data = data, freq = 'M',
         output_date = todays_date(),
             select_tech = ['d3js', 'tensorflow', 'javascript'],
             common_var = 'hn_all_match_cnt',
             common_var3 = 'hn_all_match_score',
             common_var4 = 'hn_all_match_score',
             after_date = '2010-01-01',
             var1 = 'so_usage_cnt',
             var2 = 'so_score_sum',
             var3 = 'so_usage_cnt',
             var4 = 'so_score_sum',
             subfolder = 'plots')

# Manually limiting the analysis for d3js since the number of observations
# for analyzed variables is too small
hn_plots(data = data, freq = 'M',
         output_date = todays_date(),
             select_tech = ['d3js'],
             common_var = 'hn_all_match_cnt',
             common_var3 = 'hn_all_match_score',
             common_var4 = 'hn_all_match_score',
             after_date = '2011-06-01',
             var1 = 'so_usage_cnt',
             var2 = 'so_score_sum',
             var3 = 'so_usage_cnt',
             var4 = 'so_score_sum',
             subfolder = 'plots')

data_3tech = data.loc[data['tech'].isin(['javascript', 'd3js', 'tensorflow'])]
data_3tech.drop(data_3tech[(data_3tech['tech'] == 'd3js') &
                           (data_3tech['date'] <  '2011-06-01')].index, 
    inplace = True)
data_3tech = (data_3tech.groupby(['tech',
                       pd.Grouper(key = 'date', freq = 'M')])
                .sum()
                .reset_index())

# Idea - doing linear regression and checking whether the time coefficient
# is statistically significant

# 6.2 Differentiate time series

#data_3tech['diff_so_usage_cnt_1'] = (data_3tech.groupby(['tech']).
#          so_usage_cnt.diff())
#data_3tech['diff_so_score_sum_1'] = (data_3tech.groupby(['tech']).
#          so_score_sum.diff())
#data_3tech['diff_hn_all_match_score_1'] = (data_3tech.groupby(['tech']).
#          hn_all_match_score.diff())
#data_3tech['diff_hn_all_match_cnt_1'] = (data_3tech.groupby(['tech']).
#          hn_all_match_cnt.diff())

adf_tests = (data_3tech.groupby(['tech'])['so_usage_cnt', 'so_score_sum',
             'hn_all_match_cnt', 'hn_all_match_score']
            .agg([lambda x: adfuller(x, regression = 'ct')[1]]).reset_index())
adf_tests.loc[adf_tests['tech'] == 'd3js']['so_score_sum'] = adfuller(
        data_3tech[data_3tech['tech'] == 'd3js']['so_score_sum'],
        regression = 'c')[1] # for d3js and so_score_sum linear trend
# seems to be not suitable

# Conclusion: no need to diffentiate d3js for HN and javascript in 
# case of ; the rest of the variable
# have to be differentiated

# Linear models for each variable
PVALUE = .05
VARS = ['so_usage_cnt', 'so_score_sum',
        'hn_all_match_cnt', 'hn_all_match_score']

diff_req = (data_3tech.groupby(['tech'])[VARS]
    .agg([lambda x: diff_nonstationary(x, PVALUE)]))
diff_req.columns = diff_req.columns.droplevel(1)

# parameters: granger_list, tech, maxlag
GRANGER_LIST = [('hn_all_match_score', 'so_usage_cnt'), 
 ('hn_all_match_cnt', 'so_usage_cnt'),
 ('hn_all_match_score', 'so_score_sum'),
 ('hn_all_match_score', 'so_usage_cnt')]

GRANGER_LIST[0][1]
def calc_granger_causality(x, diff_x, granger_list, group_var, groups, maxlag):
    for g in groups:
        for gl in granger_list:
            print(gl)
#            print(diff_x.at[g, gl[0]])
            yvar = repeated(pd.DataFrame.diff,
                            int(diff_x.at[g, gl[0]]))(x[x[group_var] == g][gl[0]])
#            print(diff_x.at[g, gl[1]])
            xvar = repeated(pd.DataFrame.diff,
                            int(diff_x.at[g, gl[1]]))(x[x[group_var] == g][gl[1]])
            results = grangercausalitytests((pd.concat([yvar, xvar], axis=1)
                                            .dropna()),
                                            maxlag = maxlag)
            print(results)
            return(results)

a = calc_granger_causality(x = data_3tech,
                      diff_x = diff_req,
                      granger_list = GRANGER_LIST,
                      group_var = 'tech',
                      groups = ['tensorflow'],
                      maxlag = 1)
