# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in 

#import numpy as np # linear algebra
#import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from google.cloud import bigquery
import bq_helper
import sys
from datetime import datetime
import pandas as pd

# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list the files in the input directory

import os
print(os.listdir("../input"))

# create a helper object for our bigquery dataset
hacker_news = bq_helper.BigQueryHelper(active_project= "bigquery-public-data", 
                                       dataset_name = "hacker_news")
# hacker_news.list_tables()
client = bigquery.Client()

# Stories
tech_match = """
with a as
(
select cast(timestamp as date) date,
    regexp_extract_all(lower(title),
        r"([,\s]r[,.?!\s]|python|javascript|java|scala|ruby|[,\s]c[,?!\s]|c\+\+|c#|spark|hadoop|sql|css|html|php|jquery|swift|vba|shell|delphi|cobol|pascal|fortran|perl|rust|d3.js|d3[.\s]js| d3 |tensorflow)") title_match,
    regexp_extract_all(lower(text),
        r"([,\s]r[,.?!\s]|python|javascript|java|scala|ruby|[,\s]c[,?!\s]|c\+\+|c#|spark|hadoop|sql|css|html|php|jquery|swift|vba|shell|delphi|cobol|pascal|fortran|perl|rust|d3.js|d3[.\s]js| d3 |tensorflow)") text_match,
    score
    from `bigquery-public-data.hacker_news.full`
        where cast(timestamp as date) <= '2017-12-31' and type = 'story'
)
select *
    from a
    where array_length(title_match)>0 or array_length(text_match)>0
"""
hacker_news.estimate_query_size(tech_match)
kaggle_data = hacker_news.query_to_pandas_safe(tech_match, 6.0)
sys.getsizeof(kaggle_data)
kaggle_data.head(100)
kaggle_data.to_csv("kaggle_data_20180414_1358.csv")
