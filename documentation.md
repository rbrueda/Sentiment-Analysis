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
- For each post, the data is added to a list of objects called **"posts_data"**
``` python
for submission in reddit.subreddit(subreddit).search(query_string, time_filter='day', limit=20):

```

## Nov 2023 - Dec 2023
- Added the list of posts from the Reddit API request to a Pandas dataframe where each dataframe will contain the **real-time** data
- The dataframe is then converted to an external csv titled with current timestamp
	- Each csv files contains columns: **title, description, comments, subreddit, karma, url, posted_date**
 	- The csv files are added to "Raw-Reddit-Data" directory, where the **raw data** is retrieved
- Added function to filter through dataframe to check for emoji-patterns and substribute with blank space, this will return a **new filtered dataframe**
	- For the implementation, used regex pattern from <href>https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python </href>
- Once data is filtered, the new dataframe is converted to a **filtered** csv file which is added to "Sentiment-Data" directory

## Dec 2023 - Jan 2024
- Parsed dataset by splicing every 10000 characters (based on requirements of IBM NLP api) and converting data to a **string**. 
- Passed parsed data to IBM NLP api and saved sentiment analysis results to external json file, saved in "Sentiment-Data" directory
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
- Started working on finding a way to parse through characters in sliceData() function without slicing between words 

## Mar 2024 - May 2024
- Worked on finding a way to parse through characters in ```sliceData()``` function without slicing between words
	- Used delimiter ";;;" to separate individual comments
 - sample code:
```python
for comment in (new_string.split(";;;")):
	#........
	#checks if string is found in certain category of keywords (using re.compile), it is added to its corresponding list
```
- Started working on categorizing data
	- Categories used: society, education, creativity, ethical, industry, other
- Got overall emotion results from IBM to work using the following syntax:
```python
features = Features(emotion=EmotionOptions())).get_result()
```

## April 2024 - May 2024
- finalized categorizing data
- worked on retrieving data from the following months: Jan 2023 - May 2024
	- each dataset retrieved has at least **2** datapoints
 - got visualization of data for each month using **Altair** for data visualization and Streamlit as the framework to deploy python script
- Example bar graph retrieved in April 2023 (category: Creativity)
![visualization (14)](https://github.com/user-attachments/assets/325bd454-6064-404b-8c7e-7784b06c7832)
   
## June 2024 - July 2024
- Worked on documentation for results achieved for each month
- Worked on Power BI visualizating on graphs
- Sample graph shown below:
![image](https://github.com/user-attachments/assets/cb0e1f47-8d4a-4eca-abc2-c6f079bc2d03)

## August 2024 (current)
- working on machine-learning tasks
- vectorized Reddit comments, converted to a PCA, and then used k-means to partition data into **5** clusters
