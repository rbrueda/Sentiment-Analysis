import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features,CategoriesOptions,EmotionOptions,KeywordsOptions
import pandas as pd
import numpy as np
from datetime import datetime

credentials = []

with open('credentials.txt', 'r') as f:
    for content in f:
        #add to array of content
        credentials.append(content.strip())

#opens the csv file as a dataframe
df = pd.read_csv('reddit_results.csv')


#find api key and enter it inside the curly braces
authenticator = IAMAuthenticator(credentials[5])
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=authenticator
)

#get content in selftext -- for fture we will extract timestamp and comments content
text = df.loc[3,"description"]
#get all content in this columns and set to a new df called df2
df2 = df['description'].dropna(how = 'all')
df_text = df2.to_json()

response = natural_language_understanding.analyze(
    # url='www.ibm.com',
    text = df_text,
    features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=5))).get_result()

print(json.dumps(response, indent=2))

# Specify the file path
json_file_path = "example.json"

# Write to JSON file
with open(json_file_path, 'w') as json_file:
    json.dump(response, json_file, indent=4)

print(f"Data has been written to {json_file_path}")
