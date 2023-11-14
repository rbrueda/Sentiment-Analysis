import tweepy
import pandas as pd
import streamlit as st

consumer_key = 'ptSG5Ej39umE8VY6W2EQmebKp'
#consumer_key = 'NP8h5F05uUQi4uj68HELzMMfc'

consumer_secret = 'ynsj4OQk8N9k0JwZGhNGPfn5pxgK9wbzTXc5gKGAxhZkY96rLk'
#consumer_secret = 'a8AueLSUR0fOXfaXA8HYWi3StFOUx84DLLZehQYS2NlyAy9Iq1'

access_token = '1102328244035076101-hHzndiEgzxyWPQcCAfVoQuQ9WzJ7mp'
#access_token = '1708998573474406400-jyb7nRyzyKL2mfa4LQolP2puPbKdYT'

access_token_secret = '5HKDyE5LodEqsSDUQEmgC2fG15e2ZuzSK8Biv15aVYGoJ'
#access_token_secret = 'vRaobDNX2kdm04lojvxSNB1wkTNCIFQWLgCZPbnOepUAi'

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



