import praw
from datetime import datetime, timedelta
import pandas as pd
#preprocessing portion of code -- use re to detect regular expressions (in this case emoticons)
import re
import csv
import chardet

import logging
from datetime import datetime
import sys
import schedule
from datetime import time, timedelta,datetime

import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features,CategoriesOptions,EmotionOptions,KeywordsOptions
import numpy as np
#this is where i was thinking we can deploy our app -- will allow us to get visualizations
import streamlit as st
#this is to visualize graph on streamlit
import altair as alt
import regex


# #this will avoid the csv error -- if this doesnt fix the issue idk what will
csv.field_size_limit(131072)

def filterData(df):
    # preprocessing part of code
    # code by: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
    emoji_pattern = re.compile("["
                            u"\U0001F600-\U0001F64F"  # emoticons
                            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                            u"\U0001F680-\U0001F6FF"  # transport & map symbols
                            u"\U0001F700-\U0001F77F"  # alchemical symbols
                            u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                            u"\U00002702-\U000027B0"  # Dingbats
                            u"\U000024C2-\U0001F251" 
                            "]+", flags=re.UNICODE)

    columns_to_include = ['title', 'description', 'comments', 'posted_date']
    new_df = df[columns_to_include]

    # this is a more efficient way to do the below code in which will allow for any size -- wont result to csv field limit error
    # Apply the function only to non-list columns
    # Use DataFrame.apply with the map method
    new_df = new_df.apply(lambda x: x.map(lambda elem: re.sub(emoji_pattern, ' ', str(elem)) if pd.notna(elem) and not isinstance(elem, list) else elem))

# Apply the function to each element in the "comments" column
    new_df['comments'] = new_df['comments'].apply(lambda comments: [re.sub(emoji_pattern, ' ', str(comment)) for comment in comments] if isinstance(comments, list) else comments)



    return new_df

# make monthly average function -- bar graph 
def monthlySentiment(counter, sadness_total, joy_total, fear_total, disgust_total, anger_total, timestamp):
    #will create our averages
    sadness_average = sadness_total/counter
    joy_average = joy_total/counter
    fear_average = fear_total/counter
    disgust_average = disgust_total/counter
    anger_average = anger_total/counter

    data = pd.DataFrame({
    'Category':['Sadness', 'Joy', 'Fear', 'Disguist', 'Anger'],
    'Value':[sadness_average, joy_average, fear_average, disgust_average, anger_average]

    })

    # Create Altair bar chart - this is currently getting daily sentiment analysis (try to get monnnthly )
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Category', title='Sentiment'), 
        y=alt.Y('Value', title='Value of Sentiment (0 to 1)'),
        tooltip=['Category', 'Value']
    ).properties(
        #TO DO: create the title to a better formatted date, for ex. Dec 2023 -- we would need to parse timestamp 12-03..
        title=timestamp,
        width=700,
        height=400
    )

    # Display the chart using st.altair_chart
    st.altair_chart(chart, use_container_width=True)


    #TO DO: visualization idea: would add these averages to an exitsting line graph thta has sadnesses from other months (show trend)


#function that will read every 5000 characters
# Function to filter data
def sliceData(df, selected_columns, chunk_size, timestamp, credential):
    chunks_list = []  # List to accumulate chunks
    
        # Iterate over selected columns
    for col in selected_columns:
    
        # Check if the column has any non-empty strings
        if df[col].str.len().sum() > 0:

            # Loop until there are no more characters
            while any(df[col].str.len() > 0):
                
                # Get the first chunk of characters in each string
                df['current_character'] = df[col].str.slice(0, chunk_size)

                # to not append a cell that either has "" string or NaN cell value
                non_empty_chunk = df['current_character'][(df['current_character'] != '') & df['current_character'].notna()].tolist()
                
                #Note: seems like when passing comments in the api, there were words that were cropped off, hence I check all indexes in each chunk -- there still might be an issue with this tho

                # Check if it's the last chunk, and if not, truncate to the last existing space
                for i, chunk in enumerate(non_empty_chunk):
                    #checks if it is last index in the list
                    #if i == len(non_empty_chunk) - 1 and not chunk.endswith(" "):
                    if not chunk.endswith(" "):
                        #finds the last occurence of " "
                        last_space_index = chunk.rfind(" ")
                        #if space is found, concatenate the string from that occurence
                        if last_space_index != -1:
                            non_empty_chunk[i] = chunk[:last_space_index]
                            if (i+1 < len(non_empty_chunk)):
                                #bring truncated part ot next index so we dont lose the word 
                                non_empty_chunk[i+1] = str(chunk[last_space_index:]) + " " + non_empty_chunk[i+1]

                #checks if the chunk has content
                if non_empty_chunk:
                    chunks_list.append(non_empty_chunk)

                # find the updated length of non_empty_chunk
                non_empty_chunk_size = sum(len(chunk) for chunk in non_empty_chunk)
                #remove everything from non_empty_chunk from df
                df[col] = df[col].str.slice(non_empty_chunk_size)
    
                
    counter = 1
    sadness_total = 0
    joy_total = 0
    fear_total = 0
    disgust_total = 0
    anger_total = 0

    # Display or process the accumulated chunks
    for idx, chunk in enumerate(chunks_list):
        st.write(f"Chunk {idx + 1}:", chunk)
        #print(f"chunk {idx}:")

        string = ' '.join(chunk)
        #print(string)
        #converts json to string
        json_string = json.dumps(string)
        print(f"json_string: " + json_string)

        #find api key and enter it inside the curly braces
        authenticator = IAMAuthenticator(credential)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2022-04-07',
            authenticator=authenticator
        )

        response = natural_language_understanding.analyze(
            # url='www.ibm.com',
            text = json_string,
            features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=5))).get_result()

        json_extension = ".json"
        json_file_path = f"/home/rocio/Documents/Research/Sentiment-Data/sentiment_{timestamp}_{counter}{json_extension}"

        print(json_file_path)

        # Calculate average emotion values for each keyword PER JSON
        sadness = sum(keyword.get("emotion", {}).get("sadness", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        joy = sum(keyword.get("emotion", {}).get("joy", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        fear = sum(keyword.get("emotion", {}).get("fear", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        disgust = sum(keyword.get("emotion", {}).get("disgust", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        anger = sum(keyword.get("emotion", {}).get("anger", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))

        #add it to a total sum FOR ALL JSONS PER MONTH
        sadness_total += sadness
        joy_total += joy
        fear_total += fear
        disgust_total += disgust
        anger_total += anger



        # Write to JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(response, json_file, indent=4)



        #starting counter for the amount of sentiment response  taken
        counter += 1

    monthlySentiment(counter, sadness_total, joy_total, fear_total, disgust_total, anger_total, timestamp)



# print(0)
credentials = []

#create a scheduler


#schedule every month to do this task. Note 1 month = 4 weeks
#   schedule.every(4).weeks.do(job)
#this will create an endless loop for our function -- it will be running program constantly
#while True:
#   schedule.run_pending()
#   time.sleep(1)

#add a our job function for the code below
# def job():
#     print("Making monthly request ot the reddit api")
with open('credentials.txt', 'r') as f:
    for content in f:
        #add to array of content
        credentials.append(content.strip())


#information with account and api information

#these are my ids for the reddit api
CLIENT_ID = credentials[0]
SECRET_KEY = credentials[1]

# #print(sqlalchemy.__version__)

#db credentials
# usr = 'root'
# pwd = credentials[2] #password to enter database -- wont need until later
# host = '127.0.0.1'
# port = 3306
# dbName = 'redditdb'
# tableName = 'reddit_credentials'

#to get comments
reddit = praw.Reddit(
    client_id = credentials[0],
    client_secret=credentials[1],
    password=credentials[2],
    user_agent=credentials[4],
    username=credentials[3]
)


# Define the terms to search for and the subreddit
search_terms = ['gpt', 'ai', 'generative ai', 'chatgpt']
subreddit = 'all'  # Or specify a subreddit
print(1)

# Calculate date range for "yesterday" (or adjust to the specific day you're fetching for)
yesterday = datetime.utcnow() - timedelta(days=60) #this will extract posts from the last 60 days 
date_limit = yesterday.strftime('%Y%m%d')
timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
timeframe = datetime.utcnow() - timedelta(days=1)
# print(date_limit)

# thru this new change in an hour

print(2)
# Fetch posts

#should I scrape data per day?
posts_data = []
# Create a query string with logical OR between search terms
query_string = " OR ".join(search_terms)

#place in a set for time complexity - will search in O(1)
unique_submission_ids = set()
#print(f"print test: {reddit.subreddit(subreddit)}")
#for term in search_terms: this wouldn't be necessary
    #instead of month -- try per week -- or make scheduler per week (work on tomorrow) - search all terms at once
for submission in reddit.subreddit(subreddit).search(query_string, time_filter='day', limit=20):
    #print(f"submission: {submission}")
    try:
        submission.comments.replace_more(limit=20)
        
        submission_date = datetime.utcfromtimestamp(submission.created_utc)
        
        if submission_date > timeframe: #check if data follows in timeframe - probably dont need since search function already does this

            # Check if the submission ID is not already in the set to avoid duplicates
            if submission.id not in unique_submission_ids:
                posts_data.append({
                    'title': submission.title,
                    'description': submission.selftext,
                    'comments': [comment.body for comment in submission.comments.list()],
                    'subreddit': submission.subreddit.display_name,
                    'karma': submission.score,
                    'url': submission.url,
                    'posted_date': datetime.utcfromtimestamp(submission.created_utc)
                })

                # Add the submission ID to the set to track uniqueness
                unique_submission_ids.add(submission.id)
        
        # Print post_data for debugging
        print(posts_data)
        
    except praw.exceptions.APIException as e:
        if e.response.status_code == 429:
            # Sleep for a short duration and then retry
            time.sleep(5)
        else:
            # Handle other API exceptions
            print(f"API Exception: {e}")


# Convert to DataFrame
df = pd.DataFrame(posts_data)

#ensure code is not in random order

# # Sort the DataFrame by 'posted_date'
# df.sort_values(by='posted_date', inplace=True)

# # Reset the index after sorting
# df.reset_index(drop=True, inplace=True)

csv_file_path = 'reddit_posts_'+timestamp+'.csv'
csv_file_path1 = '/home/rocio/Documents/Research/Raw-Reddit-Data/'+csv_file_path
#csv to write to
#print(csv_file_path1)
df.to_csv(csv_file_path1, index=False)

#think this might fix issue with filtering dataframe -- make it a specfic encoding 
df = pd.read_csv(csv_file_path1, encoding='utf-8')

csv_file_path2 = '/home/rocio/Documents/Research/Reddit-Data/'+csv_file_path

new_df = filterData(df)

#df.to_csv(csv_file_path1, index=False)
new_df.to_csv(csv_file_path2, index=False)
print("saved filter data to csv")

# date = date_limit
# dateTimeFrame = datetime.utcnow()

# dt_str = str(dateTimeFrame)


#TO DO- convert this into a function (call this filteredData)

# Save DataFrame to a CSV file or database

# read the csv
# df = pd.read_csv('reddit_results.csv', encoding='utf-8')



#get content in title, description and comments from our filtered df 
selected_columns = ["title", "description", "comments"]
subset_df = new_df.loc[:, selected_columns]

chunk_size = 10000 #maximum amount of characters allowed per request ot the ibm api

#this will slice data every 5000 characters and then make request to sentiment api
sliceData(subset_df, selected_columns, chunk_size, timestamp, credentials[5])


# Setup logging
date=datetime.utcnow()
name = f"/home/rocio/Documents/Research/Reddit-Data/reddit-data_{timestamp}.log"
logging.basicConfig(filename=name, level=logging.INFO)

def main():
    # Your script logic here
    logging.info(f"Script run at {datetime.now()}")

if __name__ == "__main__":
    main()
    
