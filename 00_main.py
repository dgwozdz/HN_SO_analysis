# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 22:03:26 2018

@author: kaksat
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import gc
import timeit

os.chdir('F:\Damian\github\kaggle_hacker_news')

### Stack data

stack_data1 = pd.read_csv('.\\stack_data\\tags_per_day_1_20180325.csv')
stack_data2 = pd.read_csv('.\\stack_data\\tags_per_day_2_20180306.csv')
stack_data3 = pd.read_csv('.\\stack_data\\tags_per_day_3_20180306.csv')

stack_data = pd.concat([stack_data1, stack_data2, stack_data3])

stack_data['tags'] = stack_data['tags'].str.replace('<', '').str.replace('>', '')
stack_data['post_date'] = pd.to_datetime(stack_data['post_date'])
del stack_data1, stack_data2, stack_data3

stack_data.tags.replace('apache-spark', 'spark', inplace = True)

stack_data.head(10)                         
                             
#%matplotlib inline      
#          
#for i in stack_data['tags'].unique():
#    plt.plot()
#    stack_plot = stack_data.loc[stack_data['tags'] == i]
#    plt.plot(stack_plot['post_date'], stack_plot['usage_cnt'])
#    plt.title(i)
#    plt.show()
    
### Kaggle data

kaggle_data_raw = pd.read_csv('.\\kaggle_data\\kaggle_data_20180319.csv')
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
    .str.replace("!", ""))
    # Removal of duplicates
    kaggle_data_raw.loc[:, i] = [list(set(x))
                                for x in kaggle_data_raw[i].str.split(',')]
    # Summing the scores per date and text/title match
    s = kaggle_data_raw[i].str.len()
    df = pd.DataFrame({'date': kaggle_data_raw.date.repeat(s),
                          'score': kaggle_data_raw.score.repeat(s),
            i: np.concatenate(kaggle_data_raw[i].values)})
    df = df.loc[df[i] != '']
    if i == 'text_match':
        kaggle_data_txt_score = pd.pivot_table(df,
                    index = 'date', columns = i, values = 'score',
                   aggfunc = 'sum', fill_value = 0)
        kaggle_data_txt_score.index = pd.DatetimeIndex(
        kaggle_data_txt_score.index)
        
        kaggle_data_txt_score = kaggle_data_txt_score.reindex(
                idx, fill_value = 0).stack().reset_index()
        kaggle_data_txt_score.columns = ['date', 'tech', 'txt_score_sum']
        
    else:
        kaggle_data_title_score = pd.pivot_table(df,
                    index = 'date', columns = i, values = 'score',
                   aggfunc = 'sum', fill_value = 0)
        kaggle_data_title_score.index = pd.DatetimeIndex(
        kaggle_data_title_score.index)
        
        kaggle_data_title_score = kaggle_data_title_score.reindex(
                idx, fill_value = 0).stack().reset_index()
        kaggle_data_title_score.columns = ['date', 'tech', 'title_score_sum']

# Filling the lacking dates with zeroes

from sklearn.preprocessing import MultiLabelBinarizer

mlb = MultiLabelBinarizer()
kaggle_data_txt = pd.DataFrame(
        mlb.fit_transform(kaggle_data_raw.text_match),
        kaggle_data_raw.date, mlb.classes_).sum(level = 0)
kaggle_data_txt.index = pd.DatetimeIndex(kaggle_data_txt.index)
kaggle_data_txt = kaggle_data_txt.reindex(idx, fill_value = 0).stack().reset_index()
kaggle_data_txt.columns = ['date', 'tech', 'txt_cnt']
kaggle_data_txt = kaggle_data_txt.groupby(['date', 'tech']).sum().reset_index()
kaggle_data_txt = kaggle_data_txt[kaggle_data_txt.tech != '']

mlb = MultiLabelBinarizer()
kaggle_data_title = pd.DataFrame(
        mlb.fit_transform(kaggle_data_raw.title_match),
        kaggle_data_raw.date, mlb.classes_).sum(level = 0)
kaggle_data_title.index = pd.DatetimeIndex(kaggle_data_title.index)
kaggle_data_title = kaggle_data_title.reindex(idx, fill_value = 0).stack().reset_index()
kaggle_data_title.columns = ['date', 'tech', 'title_cnt']
kaggle_data_title = kaggle_data_title.groupby(['date', 'tech']).sum().reset_index()
kaggle_data_title = kaggle_data_title[kaggle_data_title.tech != '']

# Merging data into one kaggle data frame

kaggle_data = (pd.merge(kaggle_data_txt, kaggle_data_title, how = 'outer',
                                on = ['date', 'tech'])
                .merge(kaggle_data_txt_score, how = 'outer',
                       on = ['date', 'tech'])
                .merge(kaggle_data_title_score, how = 'outer',
                       on = ['date', 'tech']))
kaggle_data.date = pd.to_datetime(kaggle_data.date)
data = (pd.merge(kaggle_data, stack_data, how = 'left',
                left_on = ['date', 'tech'], right_on = ['post_date', 'tags'])
        .drop(['post_date', 'tags'], axis = 1)
        .fillna(0))

del kaggle_data_txt, kaggle_data_title, kaggle_data_txt_score, kaggle_data_title_score, kaggle_data_raw

# Swift appeared 2nd June 2014: all the data befor this date from Hacker News
# should be dropped

data.drop(data[(data['tech'] == 'swift') & (data['date'] < '2014-06-02')].index |
        data[(data['tech'] == 'spark') & (data['date'] < '2014-05-30')].index,
                inplace = True)

# Group by weekly frequency
#kaggle_data.date = pd.to_datetime(kaggle_data.date)
#kaggle_weekly = (kaggle_data.groupby(['tech',
#                                    pd.Grouper(key = 'date', freq = 'W-MON')])
#                .sum()
#                .reset_index())
    
alpha = 0.7
%matplotlib inline
for i in data.tech.unique():
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    data_plot = data.loc[data['tech'] == i]
    ax1.plot(data_plot['date'], data_plot['txt_cnt'], 'g-', alpha = alpha)
    ax2.plot(data_plot['date'], np.log(data_plot['views']), 'b-', alpha = alpha)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Text counts', color = 'g')
    ax2.set_ylabel('Score text sum', color = 'b')
    plt.title(i)
    plt.show()









gc.collect()