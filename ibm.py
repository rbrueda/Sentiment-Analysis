import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features,CategoriesOptions,EmotionOptions,KeywordsOptions
import pandas as pd
import numpy as np
from datetime import datetime

#opens the csv file as a dataframe
df = pd.read_csv('reddit_result.csv')


#find api key and enter it inside the curly braces
authenticator = IAMAuthenticator('KmmH50mQGUkBkAZSb80T6vrWaPt-pJRie0oPXuwJNNSO')
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=authenticator
)

#get content in selftext -- for fture we will extract timestamp and comments content
text = df.loc[3,"selftext"]
#get all content in this columns and set to a new df called df2
df2 = df['selftext'].dropna(how = 'all')
df_text = df2.to_string()
print(df_text)




response = natural_language_understanding.analyze(
    # url='www.ibm.com',
    text = df_text,
    features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=5))).get_result()

print(json.dumps(response, indent=2))
