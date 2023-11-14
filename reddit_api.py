import requests
import streamlit as st
import pandas as pd
import json
# doing a db libraries
# import sqlalchemy
# from sqlalchemy import create_engine, text
import os

#these are my ids for the reddit api
CLIENT_ID = 'kg6ykpAJcVRKtOLO8GbZ2g'
SECRET_KEY = 'rdk29dYcjhdm01Wn45VxI2g_HVhuZg'

#print(sqlalchemy.__version__)
print(os.getcwd())

with open('credentials.txt', 'r') as f:
    pw = f.read()


#db credentials
usr = 'root'
pwd = pw
host = '127.0.0.1'
port = 3306
dbName = 'redditdb'
tableName = 'reddit_credentials'




auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_KEY)

 #specifying a dictionary in which we are going to go in with a password
data = {
    'grant_type' : 'password',
    'username' : 'flamingolover4',
    'password' : pw
}

#identify the version of yoyr api
headers = {'User-Agent' : 'MyAPI/0.0.1'}

#innclude all our daa for the request
res = requests.post('https://www.reddit.com/api/v1/access_token', 
                     auth=auth, data=data, headers=headers)

TOKEN = res.json()['access_token']
print(TOKEN)

#this access token is something we need to add to ur header
# at this point we can access any token we would like
headers['Authorization'] = f'bearer {TOKEN}'

print(headers)

#this is just ot see if the api is working, will get all the information in your account
print(requests.get("https://oauth.reddit.com/api/v1/me", headers=headers).json())

#allows to get max requests
res = requests.get("https://oauth.reddit.com/r/ChatGPT", headers=headers, params={'limit':'1000'})
#, params={'limit':'100', 'after' : 't3_17evdt8'}
#get data after this post

#prints the results in json format
print(res.json())

#create a dataframe that filters certain information via specfied columns
df = pd.DataFrame(columns=['subreddit', 'title', 'selftext', 'upvote_ratio', 'ups', 'downs', 'score'])

#goes through each post per results in json format
for post in res.json()['data']['children']:

    print(post['data']) #just extracts the data in the post

    #creates a dataframe with these columns of data
    df = pd.concat([df, pd.DataFrame.from_records([{ 'subreddit' : post['data']['subreddit'], 'title' : post['data']['title'], 'selftext' : post['data']['selftext'], 'upvote_ratio' : post['data']['upvote_ratio'], 'ups' : post['data']['upvote_ratio'], 'downs' : post['data']['downs'], 'score' : post['data']['score']}])], ignore_index=True)

#see it visually on a dataframe on streamlit app
st.write(df)

#save content from df to csv
df.to_csv("reddit_result.csv", index=False)

print(post['kind'] + '_' + post['data']['id'])

#To do: get all reddit post about chat gpt and short data into a separate json file
#later: organize data into a database or dataframe and make a call to the ibm api ot get infomation about sentiment analysis, when we can make a call to power bi or any other tool to make a graph for us
# before power bi: make a graph on streamlit to see results

#goal: find a way to access comments in reddit


#sql stuff -- do later for make a dataset
# #create an engine object
# engine = create_engine(
#     f"mysql+mysqldb://{usr}:{pwd}@{host}:{port}/{dbName}",
#     echo=True,
#     future=True)

# #create table
# df.to_sql(name=tableName, con=engine, if_exists='replace')

# with engine.connect() as conn:
#     result = conn.execute(text("DESCRIBE tableName;"))
#     for row in result:
#         print(row)
    
# with engine.connect() as conn:
#     result = conn.execute(text("SELECT * FROM tableName"))
#     for row in result:
#         print(f"""
#             index: {row.index}
#             subreddit: {row.subreddit}
#             title: {row.title}
#             selftext: {row.selftext}
#             upvote_ratio: {row.count}
#             ups: {row.count}
#             downs: {row.}
#             score: {row.}

#               """)


