import pandas as pd
import streamlit as st

#this code will parse through yearly data for relevant dates

df = pd.DataFrame()

#convert a csv file to a dataframe and perform operations onto it
csv_file_path1 = '/home/rocio/Documents/research/Data-To-Use/2024-01-29-20-30-02.csv'

# #go from df -> csv
df = pd.read_csv(csv_file_path1, encoding='utf-8')

#df = df[df['posted_date'].str.contains('2024-09-01|2023-05-04|2023-05-05|2023-05-06|2023-05-07|2023-05-08|2023-05-09|2023-05-10|2023-05-11|2023-05-12|2023-05-13|2023-05-14')]

#todo: make a method that traverses through all monthly data and get sentiment result
#todo: add an other category -- verify this!!

st.write(df['posted_date'])

for index, row in df.iterrows():
    data = []

    csv_file_path1 = '/home/rocio/Documents/research/Data-To-Sort/'+str(row['posted_date'])+'.csv'


    data.append({
                            'title': row['title'],
                            'description': row['description'],
                            'comments': row['comments'],
                            'subreddit': row['subreddit'],
                            'karma': row['karma'],
                            'url': row['url'],
                            'posted_date': row['posted_date']
                        })
        
    df = pd.DataFrame(data)

    # go from df -> csv
    df.to_csv(csv_file_path1, index=False)
        
        
    st.write(df)

    # # #go from df -> csv
    # row.to_csv(csv_file_path1, index=False)