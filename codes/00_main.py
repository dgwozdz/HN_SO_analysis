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

# Loading custom functioons functions 

os.chdir('F:\Damian\github\HN_SO_analysis\HN_SO_analysis\codes')
from hn_plots import hn_plots, todays_date
from diff_nonstationary import diff_nonstationary
from useful import repeated # Useful function from the Web
from grangercausalitytests_mod import grangercausalitytests_mod
from calc_granger_causality import calc_granger_causality
from sel_data_min_date import sel_data_min_date

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
cutoffs = [None]


from sklearn.preprocessing import MultiLabelBinarizer
for cutoff in cutoffs:
    if cutoff == None:
        kaggle_data_loop = kaggle_data_raw.copy()
        cutoff_lbl = ''
    else:
        kaggle_data_loop = kaggle_data_raw.loc[kaggle_data_raw['score']>=cutoff]
        cutoff_lbl = '_'+str(cutoff)
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
        data[data['date'] < '2008-09-13'].index| # two days for differences of differences
        # 2007-02-19 - launch of StackOverflow
        data[(data['tech'] == 'd3js') & (data['date'] < '2011-06-01')].index,
        # Exclusion of d3js for which there were no obsrvations
                inplace = True)

### 5. Data aggregations

data_w = (data.groupby(['tech',
                       pd.Grouper(key = 'date', freq = 'W')])
                .sum()
                .reset_index())
data_m = (data.groupby(['tech',
                       pd.Grouper(key = 'date', freq = 'M')])
                .sum()
                .reset_index())

### 6 Granger causality
    
# 6.1 Data differntiation

PVALUE = .05 # significance level on the basis of which nonstationarity
# is determined
VARS = ['so_usage_cnt', 'so_score_sum',
        'hn_all_match_cnt', 'hn_all_match_score'] # variables for which
# nonstationarity is checked

# daily data

diff_req = (data.groupby(['tech'])[VARS]
    .agg([lambda x: diff_nonstationary(x, PVALUE)]))
diff_req.columns = diff_req.columns.droplevel(1)

# weekly data

diff_req_w = (data_w.groupby(['tech'])[VARS]
    .agg([lambda x: diff_nonstationary(x, PVALUE)]))
diff_req_w.columns = diff_req_w.columns.droplevel(1)

# monthly data

diff_req_m = (data_m.groupby(['tech'])[VARS]
    .agg([lambda x: diff_nonstationary(x, PVALUE)]))
diff_req_m.columns = diff_req_m.columns.droplevel(1)

# 6.2 Selection of observation starting from the first date for which at least
#  one of two variables: hn_all_match_score, so_views was greater than 0 (zero)

# daily data

data_min_date = sel_data_min_date(data,
                                      'tech',
                                      'date',
                                      'hn_all_match_score',
                                      'so_views')
data_min_date[list(data_min_date.columns.values[2:])] = (
        data_min_date[list(data_min_date.columns.values[2:])]
        .apply(pd.to_numeric))
# weekly data

data_w_min_date = sel_data_min_date(data_w,
                                      'tech',
                                      'date',
                                      'hn_all_match_score',
                                      'so_views')
data_w_min_date[list(data_w_min_date.columns.values[2:])] = (
        data_w_min_date[list(data_w_min_date.columns.values[2:])]
        .apply(pd.to_numeric))
 
data_w_min_date.groupby(['tech'])['hn_all_match_score',
                                      'so_views'].diff().diff().reset_index()

# monthly data

data_m_min_date = sel_data_min_date(data_m,
                                      'tech',
                                      'date',
                                      'hn_all_match_score',
                                      'so_views')
data_m_min_date[list(data_m_min_date.columns.values[2:])] = (
        data_m_min_date[list(data_m_min_date.columns.values[2:])]
        .apply(pd.to_numeric))

# differencing once and two times for visualization purposes

cols = data_m_min_date.columns.difference(['tech', 'date']).tolist()
data_m_min_date_diff = (data_m_min_date.groupby(['tech'])[cols]
    .diff().add_prefix('diff_').add_suffix('_1'))
data_m_min_date_diff2 = (data_m_min_date.groupby(['tech'])[cols]
    .diff().diff().add_prefix('diff_').add_suffix('_2'))
data_m_min_date = pd.concat([data_m_min_date,
                             data_m_min_date_diff,
                             data_m_min_date_diff2],
    axis = 1, copy = False)


# 6.3 Tests of Granger causality for each variable

GRANGER_LIST = [('hn_all_match_score', 'so_usage_cnt'), 
                 ('hn_all_match_cnt', 'so_usage_cnt'),
                 ('hn_all_match_score', 'so_score_sum'),
                 ('hn_all_match_cnt', 'so_score_sum')]
P_VALUE = .05

# tests for data with daily frequency

granger_results_d = calc_granger_causality(x = data_min_date,
                                            diff_x = diff_req_w,
                      granger_list = GRANGER_LIST,
                      group_var = 'tech',
                      groups = set(data_min_date.tech),
                      maxlag = 100,
                      both_sides = True,
                      only_min_crit = True,
                      filter_p_value = P_VALUE)

# tests for data with weekly frequency

granger_results_w = calc_granger_causality(x = data_w_min_date,
                      diff_x = diff_req,
                      granger_list = GRANGER_LIST,
                      group_var = 'tech',
                      groups = set(data_w_min_date.tech),
                      maxlag = 52,
                      both_sides = True,
                      only_min_crit = True,
                      filter_p_value = P_VALUE)

# tests for data with monthly frequency

granger_results_m = calc_granger_causality(x = data_m_min_date,
                      diff_x = diff_req_m,
                      granger_list = GRANGER_LIST,
                      group_var = 'tech',
                      groups = set(data_m_min_date.tech),
                      maxlag = 36,
                      both_sides = True,
                      only_min_crit = True,
                      filter_p_value = P_VALUE)


#granger_results_d.to_pickle('.\\saved_objects\\granger_results_d_20180514_2055')
#granger_results_w.to_pickle('.\\saved_objects\\granger_results_w_20180514_2055')
#granger_results_m.to_pickle('.\\saved_objects\\granger_results_m_20180514_2314')

#granger_results_d = pd.read_pickle('.\\saved_objects\\granger_results_d_20180514_20')
#granger_results_w = pd.read_pickle('.\\saved_objects\\granger_results_w_20180514_20')
#granger_results_m = pd.read_pickle('.\\saved_objects\\granger_results_m_20180514_2314')

# Plots for the needs of statistically significant mothly aggregated data

#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['css'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'hn_all_match_score',
#             common_var4 = 'hn_all_match_score',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_usage_cnt',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)
#
#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['html'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'diff_hn_all_match_score_1',
#             common_var4 = 'hn_all_match_score',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'diff_so_usage_cnt_1',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)
#
#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['java'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'diff_hn_all_match_score_1',
#             common_var4 = 'hn_all_match_score',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'diff_so_score_sum_2',
#             var3 = 'diff_so_usage_cnt_1',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)
#
#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['jquery'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'diff_hn_all_match_score_1',
#             common_var4 = 'hn_all_match_score',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'diff_so_score_sum_1',
#             var3 = 'diff_so_score_sum_1',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)
#
#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['swift'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'diff_hn_all_match_score_1',
#             common_var4 = 'hn_all_match_cnt',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'diff_so_score_sum_1',
#             var3 = 'diff_so_score_sum_1',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)
#
#hn_plots(data = data_m_min_date,
#         output_date = todays_date(),
#             select_tech = ['tensorflow'],
#             common_var = 'diff_hn_all_match_score_1',
#             common_var2 = 'diff_hn_all_match_cnt_1',
#             common_var3 = 'diff_hn_all_match_score_1',
#             common_var4 = 'hn_all_match_cnt',
#             after_date = '2006-01-01',
#             var1 = 'diff_so_usage_cnt_2',
#             var2 = 'diff_so_score_sum_1',
#             var3 = 'diff_so_score_sum_1',
#             var4 = 'so_score_sum',
#             subfolder = 'plots',
#             add_freq_label = False)

# 6.4 Plots for standardized data

data_min_date[['hn_all_match_score_cum',
             'hn_all_match_cnt_cum',
              'so_usage_cnt_cum',
              'so_score_sum_cum']] = (data_min_date.
              groupby('tech')['hn_all_match_score',
             'hn_all_match_cnt',
              'so_usage_cnt', 'so_score_sum'].cumsum())


hn_plots(data = data_min_date,
         output_date = todays_date(),
             select_tech =  set(data_min_date.tech),
             common_var = 'hn_all_match_score_cum',
             common_var2 = 'hn_all_match_score_cum',
             common_var3 = 'hn_all_match_cnt_cum',
             common_var4 = 'hn_all_match_cnt_cum',
             after_date = '2006-01-01',
             var1 = 'so_usage_cnt_cum',
             var2 = 'so_score_sum_cum',
             var3 = 'so_usage_cnt_cum',
             var4 = 'so_score_sum_cum',
             subfolder = 'plots',
             add_freq_label = False,
             same_oy = True)

# suffix '_s' from '_standardised'
data_min_date[['hn_all_match_score_cum_s',
                'hn_all_match_cnt_cum_s',
                'so_usage_cnt_cum_s',
                'so_score_sum_cum_s']] = (data_min_date.groupby('tech')[
                        'hn_all_match_score_cum',
                        'hn_all_match_cnt_cum',
                        'so_usage_cnt_cum',
                        'so_score_sum_cum'].apply(
                lambda x: (x - x.min())/(x.max() - x.min())))

hn_plots(data = data_min_date,
         output_date = todays_date(),
             select_tech =  set(data_min_date.tech),
             common_var = 'hn_all_match_score_cum_s',
             common_var2 = 'hn_all_match_score_cum_s',
             common_var3 = 'hn_all_match_cnt_cum_s',
             common_var4 = 'hn_all_match_cnt_cum_s',
             after_date = '2006-01-01',
             var1 = 'so_usage_cnt_cum_s',
             var2 = 'so_score_sum_cum_s',
             var3 = 'so_usage_cnt_cum_s',
             var4 = 'so_score_sum_cum_s',
             subfolder = 'plots',
             add_freq_label = False,
             same_oy = True)

#######################################################################
# 7 Plots for the needs of Markdown for Github


#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['c#'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for C#',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for C#',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for C#',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for C#',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['c'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for C',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for C',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for C',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for C',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['c++'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for C++',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for C++',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for C++',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for C++',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['cobol'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Cobol',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Cobol',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['css'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for CSS',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for CSS',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for CSS',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for CSS',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['d3js'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_score_sum_cum_s',
#             var2 = 'so_score_sum_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for D3.js',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for D3.js',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['delphi'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Delphi',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Delphi',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['fortran'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Fortran',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Fortran',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['hadoop'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_score_sum_cum_s',
#             var2 = 'so_score_sum_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for Hadoop',
#             label2 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for Hadoop',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['html'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_score_sum_cum_s',
#             var2 = 'so_score_sum_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for HTML',
#             label2 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for HTML',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['java'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_score_cum_s',
#             common_var4 = 'hn_all_match_score_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_score_sum_cum_s',
#             var4 = 'so_score_sum_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Java',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Java',
#             label3 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for Java',
#             label4 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for Java',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['javascript'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Javascript',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Javascript',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Java',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Java',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['pascal'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_score_cum_s',
#             common_var4 = 'hn_all_match_score_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_score_sum_cum_s',
#             var4 = 'so_score_sum_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Pascal',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Pascal',
#             label3 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for Pascal',
#             label4 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for Pascal',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['perl'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Perl',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Perl',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Perl',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Perl',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['php'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_score_sum_cum_s',
#             var2 = 'so_score_sum_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for PHP',
#             label2 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for PHP',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['python'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Python',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Python',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Python',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Python',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['shell'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Shell',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Shell',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Shell',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Shell',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['spark'],
#             common_var = 'hn_all_match_score_cum_s',
#             common_var2 = 'hn_all_match_score_cum',
#             common_var3 = 'hn_all_match_cnt_cum_s',
#             common_var4 = 'hn_all_match_cnt_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for Spark',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for Spark',
#             label3 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Spark',
#             label4 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Spark',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['sql'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_score_cum_s',
#             common_var4 = 'hn_all_match_score_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_score_sum_cum_s',
#             var4 = 'so_score_sum_cum_s',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of points on HN for SQL',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of points on HN for SQL',
#             label3 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for SQL',
#             label4 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for SQL',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['swift'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_score_cum_s',
#             common_var4 = 'hn_all_match_score_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Swift',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Swift',
#             label3 = 'Standardized cumulative number of points on SO vs.\n'
#             'standardized cumulative number of points on HN for Swift',
#             label4 = 'Cumulative number of points on SO vs.\n'
#             'cumulative number of points on HN for Swift',
#             show_y_lab = False)
#
#hn_plots(data = data_min_date,
#         output_date = todays_date(),
#             select_tech =  ['tensorflow'],
#             common_var = 'hn_all_match_cnt_cum_s',
#             common_var2 = 'hn_all_match_cnt_cum',
#             common_var3 = 'hn_all_match_score_cum_s',
#             common_var4 = 'hn_all_match_score_cum',
#             after_date = '2006-01-01',
#             var1 = 'so_usage_cnt_cum_s',
#             var2 = 'so_usage_cnt_cum',
#             var3 = 'so_usage_cnt_cum_s',
#             var4 = 'so_usage_cnt_cum',
#             subfolder = 'plots',
#             add_freq_label = False,
#             same_oy = True,
#             label1 = 'Standardized cumulative number of questions on SO vs.\n'
#             'standardized cumulative number of topics on HN for Tensorflow',
#             label2 = 'Cumulative number of questions on SO vs.\n'
#             'cumulative number of topics on HN for Tensorflow',
#             show_y_lab = False)