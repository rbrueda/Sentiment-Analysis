import praw
from datetime import datetime, timedelta
import pandas as pd
print(0)
reddit = praw.Reddit(client_id='XBx9fm54Z-Tv_sGiRIT5Cg', 
                     client_secret='kCpzwMLu4xEi4cMPvZIqUdJ3Ms8_vQ', 
                     user_agent='your_user_agent')

# Define the terms to search for and the subreddit
search_terms = ['gpt', 'ai', 'generative ai', 'chatgpt']
subreddit = 'all'  # Or specify a subreddit
print(1)

# Calculate date range for "yesterday" (or adjust to the specific day you're fetching for)
yesterday = datetime.utcnow() - timedelta(days=365)
date_limit = yesterday.strftime('%Y%m%d')
print(2)
# Fetch posts
posts_data = []
for term in search_terms:
    for submission in reddit.subreddit(subreddit).search(term, time_filter='day', limit=100):
        submission.comments.replace_more(limit=100)
        print(submission)
        if datetime.utcfromtimestamp(submission.created_utc).strftime('%Y%m%d') == date_limit:
            posts_data.append({
                'title': submission.title,
                'description': submission.selftext,
                'comments': [comment.body for comment in submission.comments.list()],
                'subreddit': submission.subreddit.display_name,
                'karma': submission.score,
                'url': submission.url,
                'posted_date': datetime.utcfromtimestamp(submission.created_utc)
            })

# Convert to DataFrame
df = pd.DataFrame(posts_data)

# Save DataFrame to a CSV file or database
df.to_csv(f'reddit_posts_{date_limit}.csv', index=False)