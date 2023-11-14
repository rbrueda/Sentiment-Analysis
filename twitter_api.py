import tweepy
import pandas as pd
import streamlit as st

consumer_key = '***REMOVED***'
#consumer_key = '***REMOVED***'

consumer_secret = '***REMOVED***'
#consumer_secret = '***REMOVED***'

access_token = '***REMOVED***'
#access_token = '***REMOVED***'

access_token_secret = '***REMOVED***'
#access_token_secret = '***REMOVED***'

auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret,
    access_token, access_token_secret
)

#try to regenerate keys changed to read and write autentication

api = tweepy.API(auth, wait_on_rate_limit=True)

search_query = "'Elon Musk''fired'-filter:retweets AND -filter:replies AND -filter:links"
no_of_tweets = 100

try: 
    tweets = api.search_tweets(q=search_query, count=no_of_tweets, tweet_mode='extended')

    attributes_container = [[tweet.user.name, tweet.created_at, tweet.favorite_count, tweet.source, tweet.full_text] for tweet in tweets]

    columns = ["User", "Date Created", "Number of Likes", "Source of Tweet", "Tweet"]

    tweet_df = pd.DataFrame(attributes_container, columns=columns)

    st.write(tweet_df)

except BaseException as e:
    print('Status Failed On, ', str(e))




#try to sign in again and see if public tweets work



