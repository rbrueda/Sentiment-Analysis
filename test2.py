from datetime import time, timedelta,datetime
import pandas as pd
import re
import streamlit as st


csv_file_path2 = '/home/rocio/Documents/Research/Reddit-Data/reddit_posts_2023-12-13_202128.csv'
df = pd.read_csv(csv_file_path2, encoding='utf-8')

st.write(df)

column_name = 'posted_date'

# Check if the specified column exists in the DataFrame
if column_name in df.columns:
    # Print all values in the specified column
    print(df[column_name].values)

