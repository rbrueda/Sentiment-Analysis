import praw
from datetime import datetime, timedelta
import pandas as pd
#preprocessing portion of code -- use re to detect regular expressions (in this case emoticons)
import re
import csv
import chardet


print(0)
credentials = []


with open('credentials.txt', 'r') as f:
    for content in f:
        #add to array of content
        credentials.append(content.strip())


#information with account and api information

#these are my ids for the reddit api
CLIENT_ID = credentials[0]
SECRET_KEY = credentials[1]

#print(sqlalchemy.__version__)

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
yesterday = datetime.utcnow() - timedelta(days=60)
date_limit = yesterday.strftime('%Y%m%d')
print(date_limit)

print(2)
# Fetch posts
posts_data = []
for term in search_terms:
    for submission in reddit.subreddit(subreddit).search(term, time_filter='day', limit=20):
        submission.comments.replace_more(limit=100)
        print(submission)
        #if datetime.utcfromtimestamp(submission.created_utc).strftime('%Y%m%d') == date_limit:
        posts_data.append({
            'title': submission.title,
            'description': submission.selftext,
            'comments': [comment.body for comment in submission.comments.list()],
            'subreddit': submission.subreddit.display_name,
            'karma': submission.score,
            'url': submission.url,
            'posted_date': datetime.utcfromtimestamp(submission.created_utc)
        })
        #print post_data -- this was just to track if it was working
        #before it was making too many requests causing a 429 error, which made it print nothing
        print(posts_data)

# Convert to DataFrame
df = pd.DataFrame(posts_data)

# Save DataFrame to a CSV file or database
df.to_csv(f'reddit_results.csv', index=False)


#preprocessing part of code
#code by: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
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

# Detect the encoding of the file
with open('reddit_results.csv', 'rb') as infile:
    rawdata = infile.read()
    result = chardet.detect(rawdata)

# Use the detected encoding to read the file and write to the output file with 'utf-8' encoding
with open('reddit_results.csv', 'r', encoding=result['encoding']) as infile, open('reddit_results_filtered.csv', 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        print(row)
        #replace the pattern in all columns for csv file
        modified_row = [re.sub(emoji_pattern, " ", value) for value in row]

        #two modifiable conditions adding later: 
        # 1. Convert comments from a list of strings to one string
        # 2. 

        writer.writerow(modified_row)

    
