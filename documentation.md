# Documentation for Sentiment Analysis Project

## Oct 2023 - Nov 2023
- Used <span style="color: #d67fbb">praw</span> that will pass api keys and account information to fetch query to Reddit API
``` python
reddit = praw.Reddit(
    client_id = credentials[0],
    client_secret=credentials[1],
    password=credentials[2],
    user_agent=credentials[4],
    username=credentials[3]
)
```


- Iterated through each reddit submission to search through key terms to see if at least one of the search terms, **gpt, ai, generative ai, chatgpt**, are found 
``` python
for submission in reddit.subreddit(subreddit).search(query_string, time_filter='day', limit=20):

```

## Nov 2023 - Dec 2023
- Saved each request to external csv titled with timestamp when csv was created. Each csv contains real-time data
	- Each csv files contains columns: **title, description, comments, subreddit, karma, url, posted_date**
- Added function to filter through csv to check for emoji-patterns and substribute with blank space
- Used regex pattern from <href>https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python </href>

## Dec 2023 - Jan 2024
- Parsed dataset by splicing every 5000 characters (based on requirements of IBM NLP api) and converting data to a string. 
- Passed parsed data to IBM NLP api and saved sentiment analysis results to external json file
	- Json attributes for sentiment results are: **sadness, joy, fear, disgust, anger**
- Once all data has been called to IBM, I averaged all the results to get **daily** sentiment analysis results
- Visualized data using altair library and deployed platform in Streamlit framework
- Started working on daily scheduler based design and brainstormed ways to visualize the data over a long period of time (annual-based graph)


## Jan 2024 - Feb 2024
- modified code to avoid duplication of data continuously checking if submission.id is not found in the set unique_submission_id
```python
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

```
