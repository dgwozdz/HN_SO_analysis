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

os.chdir('F:\Damian\github\HN_SO_analysis\HN_SO_analysis\codes')
from hn_plots import hn_plots, todays_date

os.chdir('F:\Damian\github\HN_SO_analysis\HN_SO_analysis')

### 1. Stack Overflow data
 
stack_data1 = pd.read_csv('.\\stack_data\\tags_per_day_1_20180325.csv')
stack_data2 = pd.read_csv('.\\stack_data\\tags_per_day_2_20180306.csv')
stack_data3 = pd.read_csv('.\\stack_data\\tags_per_day_3_20180306.csv')
stack_data4 = pd.read_csv('.\\stack_data\\tags_per_day_4_d3js_tensorflow_20180403.csv')

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
#%matplotlib inline      
#          
#for i in stack_data['tags'].unique():
#    plt.plot()
#    stack_plot = stack_data.loc[stack_data['tags'] == i]
#    plt.plot(stack_plot['post_date'], stack_plot['usage_cnt'])
#    plt.title(i)
#    plt.show()
    
### 2. Kaggle data

kaggle_data_raw = pd.read_csv('.\\kaggle_data\\kaggle_data_20180414_1358.csv')
kaggle_data_raw = kaggle_data_raw[
        (kaggle_data_raw.title_match.isnull() == False) |
        (kaggle_data_raw.text_match.isnull() == False)]

# combine ttle and text

#kaggle_data_raw
#kaggle_data_raw.columns
#kaggle_data_raw.loc[:, i] = [list(set(x))
#                                for x in kaggle_data_raw[i].str.split(',')]

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
    

kaggle_data_raw['all_match'] = (kaggle_data_raw['text_match']
    +','+ kaggle_data_raw['title_match'])
kaggle_list = []

cutoffs = [None, 10, 25]
#kaggle_data_raw.columns
#type(kaggle_data_raw)
#kaggle_data_loop = kaggle_data_raw.loc[kaggle_data_raw['score']>=10]
#type(kaggle_data_loop)
#kaggle_data_raw.info()
#kaggle_data_loop.info()
from sklearn.preprocessing import MultiLabelBinarizer
#for i in ['text_match', 'title_match', 'all_match']:
#    print(i)

#kaggle_data_raw = kaggle_data_raw.iloc[169460:169479]

#kaggle_data_loop['text_match'].str.split(',')
#kaggle_data_loop.loc[:, i] = [list(set(x))
#cutoff = None
for cutoff in cutoffs:
    if cutoff == None:
        kaggle_data_loop = kaggle_data_raw.copy()
        cutoff_lbl = ''
    else:
        kaggle_data_loop = kaggle_data_raw.loc[kaggle_data_raw['score']>=cutoff]
        cutoff_lbl = '_' + str(cutoff)
#    print(cutoff)
#    print(cutoff == None)
#    print(kaggle_data_loop.describe())
    for i in ['text_match', 'title_match', 'all_match']:
        
    #kaggle_data_raw['text_match'].str.split(',')    
    #    i  = 'text_match'
        # Removal of duplicates
        before = kaggle_data_loop[i]
        kaggle_data_loop.loc[:, i] = [list(set(x))
                                    for x in kaggle_data_loop[i].str.split(',')]
    #    kaggle_data_raw[i].str.split(',')
    #    [list(set(x)) for x in kaggle_data_raw['title_match'].str.split(',')]
    #    [list(set(x)) for x in kaggle_data_loop['title_match'].str.split(',')]
        
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

## Weekly freqency

#hn_plots(data = data, freq = 'w',
#         output_date = TODAY,
#             select_tech = ['d3js', 'javascript', 'tensorflow'],
#             common_var = 'hn_all_match_score',
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_answers',
#             var4 = 'so_views')
#
#hn_plots(data = data, freq = 'w',
#         output_date = TODAY,
#             select_tech = ['d3js', 'javascript', 'tensorflow'],
#             common_var = 'hn_all_match_score',
#             common_var3 = 'hn_all_match_cnt',
#             common_var4 = 'hn_all_match_cnt',
#             after_date = '2010-01-01',
#             var1 = 'so_favorites',
#             var2 = 'so_comments',
#             var3 = 'so_favorites',
#             var4 = 'so_comments')
#
#hn_plots(data = data, freq = 'w',
#         output_date = TODAY,
#             select_tech = ['d3js', 'javascript', 'tensorflow'],
#             common_var = 'hn_all_match_cnt',
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_score_sum',
#             var3 = 'so_answers',
#             var4 = 'so_views')



## Monthly frequency


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

hn_plots(data = data, freq = 'M',
         output_date = todays_date(),
             select_tech = ['d3js', 'tensorflow', 'javascript'],
             common_var = 'hn_all_match_cnt_10',
             common_var3 = 'hn_all_match_score_10',
             common_var4 = 'hn_all_match_score_10',
             after_date = '2010-01-01',
             var1 = 'so_usage_cnt',
             var2 = 'so_score_sum',
             var3 = 'so_usage_cnt',
             var4 = 'so_score_sum',
             subfolder = 'plots')

hn_plots(data = data, freq = 'M',
         output_date = todays_date(),
             select_tech = ['d3js', 'tensorflow', 'javascript'],
             common_var = 'hn_all_match_cnt_25',
             common_var3 = 'hn_all_match_score_25',
             common_var4 = 'hn_all_match_score_25',
             after_date = '2010-01-01',
             var1 = 'so_usage_cnt',
             var2 = 'so_score_sum',
             var3 = 'so_usage_cnt',
             var4 = 'so_score_sum',
             subfolder = 'plots')

data.tech.unique()

#hn_plots(data = data, freq = 'M',
#         output_date = todays_date(),
#             select_tech = ['d3js', 'javascript', 'tensorflow'],
#             common_var = 'hn_all_match_score',
#             common_var2 = 'hn_all_match_score' + cutoff_str,
#             common_var3 = 'hn_all_match_score',
#             common_var4 = 'hn_all_match_score' + cutoff_str,
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_usage_cnt',
#             var3 = 'so_score_sum',
#             var4 = 'so_score_sum',
#             subfolder = 'plots')
#
#hn_plots(data = data, freq = 'M',
#         output_date = todays_date(),
#             select_tech = ['d3js', 'javascript', 'tensorflow'],
#             common_var = 'hn_all_match_cnt',
#             common_var2 = 'hn_all_match_cnt' + cutoff_str,
#             common_var3 = 'hn_all_match_cnt',
#             common_var4 = 'hn_all_match_cnt' + cutoff_str,
#             after_date = '2010-01-01',
#             var1 = 'so_usage_cnt',
#             var2 = 'so_usage_cnt',
#             var3 = 'so_score_sum',
#             var4 = 'so_score_sum',
#             subfolder = 'plots')

### End of code----

#data.columns
#data.loc[(data['tech'] == 'tensorflow') &
#         ((data['hn_text_match_score'] > 0) | (data['so_views']>0))].date.min()
#
#after_date = '2010-01-01'
#max(pd.to_datetime(after_date),
#                        data.loc[(data['tech'] == 'tensorflow') &
#         ((data['hn_text_match_score'] > 0) |
#                 (data['so_views']>0))].date.min()).date().strftime('%Y-%m-%d')

# Correlations
#corr_day = data.groupby('tech').corr().reset_index()
#corr_week = data_week.groupby('tech').corr().reset_index()
#data.columns
#data.sort_values(by = ['tech', 'date'], inplace = True)
#for i in (<columns>)
#data['diff_' + i] = data.groupby(['tech'])[i].transform(lambda x: x.diff())

#'hn_all_match_cnt' == None
#
#max(pd.to_datetime('2010-01-01'),
#                        data.loc[(data['tech'] == 'd3js') &
#         ((data['hn_all_match_score'] > 0) | (data['so_views']>0))].date.min()).strftime('%Y-%m-%d')