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
import ast
import os

#todo: work on biweekly data 
#   - add a function that merges multiple csv files
#   - place the responses in separate folders --> so no files will be overwriten
#   - change the keywords
#   - do a re.search for higher efficiency


# #this will avoid the csv error -- if this doesnt fix the issue idk what will
csv.field_size_limit(131072)

#gets the last 2 weeks worth of data
def mergeData():
    #extract the files in a certain directory
    folder_name = '/home/rocio/Documents/Research/Reddit-Data'
    all_files = [os.path.join(folder_name, f) for f in os.listdir(folder_name) if f.endswith('.csv')]
    #gets the date 14 days ago
    timeframe = datetime.now() - timedelta(days=14) #1-15 15-30
    timeframe= timeframe.strftime('%Y-%m-%d')
    timeframe = datetime.strptime(timeframe, '%Y-%m-%d')


    biweekly_data = []
    #goes through all the files and checks if any of them are from 14 days ago
    for file in all_files:
        file = str(file)
        data = file.replace("/home/rocio/Documents/Research/Reddit-Data/", "").replace(".csv", "").replace("reddit_posts_", "")
        match = re.search(r"\d+-(\d+)-(\d+)", data)
        if match:
            fileTime = match.group(0)
            fileTime = datetime.strptime(fileTime, '%Y-%m-%d')
            print(f"datetime: {datetime}")
            if (fileTime >= timeframe):
                #append the file to biweekly_data list
                biweekly_data.append(file)

    # Initialize an empty list to store DataFrames
    dataframes_list = []

    # Loop over the list of file paths & read each file into a DataFrame
    for file in biweekly_data:
        df = pd.read_csv(file)
        dataframes_list.append(df)

    # Concatenate all DataFrames into one
    if (dataframes_list): #if dataframes_list is not null
        big_dataframe = pd.concat(dataframes_list, ignore_index=True)
        # Save the concatenated DataFrame to a new CSV file
        big_csv_filename = 'combined_reddit_data.csv'
        bi_weekly_directory = '/home/rocio/Documents/Research/Biweekly-Reddit-Data'
        big_dataframe.to_csv(os.path.join(folder_name, big_csv_filename), index=False)
        print(f"All data has been combined and written to {big_csv_filename}")
        return big_dataframe
    else:
        print("nothing in dataframe")
        return None

# Function to remove escape characters
def remove_escape_chars(text):
    return re.sub(r'\\.', '', text)

def filterData(df):
    # preprocessing part of code
    # emoji pattern code by: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
    #http links pattern code by: https://stackoverflow.com/questions/6718633/python-regular-expression-again-match-url 
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


    #replaces emoji patterns
    new_df = new_df.apply(lambda x: x.map(lambda elem: re.sub(emoji_pattern, ' ', str(elem)) if pd.notna(elem) and not isinstance(elem, list) else elem))

    # cleans the dataframe from hyperlinks -- issues with this!
    new_df = new_df.replace(to_replace=r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*", value='', regex=True)
    
    #clearns dataframe from escape characters?
    new_df = new_df.replace(to_replace=r'\\[^\s]', value='', regex=True)
    
    # cleans the dataframe from asterisks
    new_df = new_df.replace(to_replace=r'\*+', value=' ', regex=True)
    
    #additonal characters that were not cleaned
    new_df = new_df.replace(to_replace=r'([*/<>#]|/|&#x200B;)+|\s{2,}', value=' ', regex=True)

    # Apply the function to each element in the "comments" column
    new_df['comments'] = new_df['comments'].apply(lambda comments: [re.sub(emoji_pattern, ' ', str(comment)) for comment in comments] if isinstance(comments, list) else comments)

    return new_df




# make biweekly average function -- bar graph 
def dataVisualization(counter, sadness_total, joy_total, fear_total, disgust_total, anger_total, timestamp, category):
    #save it in a folder -- biweeklt sentiment results

    #will create our averages
    sadness_average = sadness_total/counter
    joy_average = joy_total/counter
    fear_average = fear_total/counter
    disgust_average = disgust_total/counter
    anger_average = anger_total/counter

    #total sentiment results in json format
    sentiment_results = {
        "emotion": {
            "document": {
                "emotion": {
                    "sadness": sadness_average,
                    "joy": joy_average,
                    "fear": fear_average,
                    "disgust": disgust_average,
                    "anger": anger_average
                }
            }
        }
    }

    json_path = '/home/rocio/Documents/Research/Sentiment-Data/Biweekly-Responses/' + "sentiment_" + timestamp + "_" + category + ".json"
    #write sentiment results in json 
    with open(json_path, 'w') as f:
        json.dump(sentiment_results, f)

    #create a dataframe with the results
    data = pd.DataFrame({
    'Category':['Sadness', 'Joy', 'Fear', 'Disguist', 'Anger'],
    'Value':[sadness_average, joy_average, fear_average, disgust_average, anger_average]

    })

    # Specify the color for each category
    color_scale = alt.Scale(domain=['Sadness', 'Joy', 'Fear', 'Disguist', 'Anger'],
                            range=['blue', 'yellow', 'purple', 'green', 'red'])


    # Create Altair bar chart - this is currently getting daily sentiment analysis (try to get monnnthly )
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Category', title='Sentiment'), 
        y=alt.Y('Value', title='Value of Sentiment (0 to 1)'),
        tooltip=['Category', 'Value'],
        color=alt.Color('Category:N', scale=color_scale)  # Specify the color scale
    ).properties(
        #todo: create the title to a better formatted date, for ex. Dec 2023 -- we would need to parse timestamp 12-03..
        title=timestamp,
        width=700,
        height=400
    )

    # Display the chart using st.altair_chart
    st.altair_chart(chart, use_container_width=True)


def remove_special_characters(input_string):
    # Use regex to replace all instances of special characters including square brackets with an empty string
    result_string = re.sub(r'[\\\@\&\$\[\]\u0000-\u001f]', '', input_string)
    return result_string


def make_quotes_same(input_string, target_quote='"'):
    if target_quote not in ('"', "'"):
        raise ValueError("Target quote must be either ' or \"")

        #'s . 't, 'm

    return input_string.replace("'", target_quote).replace('"', target_quote).replace('“', target_quote).replace('”', target_quote).replace("‘", "'")


def remove_illegal_decimal_literals(input_string):
    # Define a regular expression pattern to match illegal decimal literals
    pattern = r'(?<!\d)[+-]?\d+\.\d+\b(?!\.\d+)'
    
    # Use re.sub() to replace illegal decimal literals with an empty string
    result = re.sub(pattern, '', input_string)
    
    return result



def categorizeData(df, timestamp):
    #all the keywords in order to categorize the data
    #index 0: society
    #index 1: education
    #index 2: creativity
    #index 3: ethical / legal
    #index 4: industry
    categorization_keywords = [
    ["Poverty", "Inequality", "Discrimination", "Social", "Justice" "Human", "Rights" 
    "Homelessness", "Unemployment", "Inequality", "Healthcare", "Access", "Mental", "health", "stigma"
    "Civil", "movement" "Feminism", "LGBTQ+", "Activism", "Environmental", "Environment", "society" "Lives", "Matter" 
    "#MeToo", "Indigenous", "Disability", "handicap", "trends", "communities"
    "Population", "Urbanization", "Rural", "Aging", "Youth", "demographics"
    "Migration", "patterns", "Refugee", "crisis", "Immigration", "policy",
    "Multiculturalism", "Cultural", "Assimilation" "preservation", "heritage", 
    "identity", "Ethnic", "Intercultural", "communication", "Family", "structure", "Marriage", "Gender",  "roles", "Parenting", "styles", "system", 
    "Political", "institutions", "Community", "engagement", "Neighborhood", "revitalization", "organizing", "organize", 
    "cohesion", "resilience", "networks", "support", "Interpersonal", "relationships", "Friendship", 
    "bonds", "capital", "isolation", "media", "impact", "Digital", "divide", "Online", "Technology", "addiction", 
    "Cyberbullying", "Privacy", "concerns", "literacy", "global", "interconnectedness", "exchange", "economy", "International", "relations", 
    "Transnational", "corporations", "governance", "citizenship",
    "progress", "reform", "innovation", "entrepreneurship", 
    "Sustainable", "development", "goals", "Advocacy", "change"],

    ["Education", "Schools", "Teachers", "Students", "Classrooms", "Curriculum", "Learning", 
    "Educational", "technology", "Online", "Distance", "E-learning", "Blended", 
    "MOOCs", "Virtual", "classrooms", "Remote", "Digital" "Pedagogy", "Andragogy", 
    "Teaching", "methods", "Instructional", "design", "psychology", "Assessment", "Testing", 
    "Grading", "standard" "Standardized", "standards", "test", "tests", "Alternative", "assessments", "outcomes", 
    "Curriculum", "development", "policy", "reform", "equity", "Access", 
    "Quality", "Special", "Gifted", "childhood", "Primary", "Secondary", "High school", "K-12", 
    "College", "University", "Community college", "Vocational", "Technical", 
    "STEM", "STEAM", "skills", "Critical", "Problem-solving", "Creativity", "Collaboration", "Communication", "literacy", "Media", 
    "Information", "Financial", "Civic", "language", "Bilingual", "Multilingual", 
    "Teacher", "training" "Professional", "leadership", "management", "school"
    "Parental", "involvement", "Home-school", "Charter", "Home schooling", "smart"
    "Educational research", "Educational conferences", "Education journals", "Education blogs", 
    "news", "scholarships" ],
    [
    "Creativity", "Creative", "thinking", "Innovation", "Imagination", 
    "Originality", "Problem-solving", "art", "Critical", "thinking", 
    "Divergent", "Convergent", "Lateral", "Design", "Artistic", 
    "Creative", "Inspiration", "Ideation", "Brainstorming", 
    "Visualization", "Experimentation", "Risk-taking", "Playfulness", 
    "Curiosity", "Open-mindedness", "Flexibility", "Adaptability", 
    "Resilience", "Resourcefulness", "Inventiveness", "Ingenuity", 
    "Entrepreneurship", "Intrapreneurship", "collaboration", 
    "Interdisciplinary", "Media", "Film", "Music", "Literary", 
    "Visual arts", "Performing arts", "Fashion", "Architecture", 
    "Poetry", "Storytelling", "Ingenuity", "Insight", "Intuition", 
    "Introspection", "Expression", "Vision", "Aesthetic", 
    "Experimentation", "Adaptation", "Intrepidness", "Discovery", 
    "Revelation", "Renewal", "Fusion", "Evolution", "Harmony", 
    "Fusion", "Fusion", "Perception", "Exploration", 
    "Interpretation", "Revelation", "Embellishment", 
    "Transformation", "Reconstruction", "Metamorphosis", "Revelation"
    ],

    ["Ethics", "Legal", "Morality", "Law", "Regulation", "Compliance", "Governance", "Policy", 
    "principles", "justice", "criminal", "rights", "Civil", "Privacy", 
    "protection", "Confidentiality", "property", "Copyright", "Patents", 
    "Trademark", "Fair use", "Plagiarism", "Cybersecurity", "Data", "safety", "system"
    "Surveillance", "Ethical", "behavior", "Court", "obligations", "responsibilities", 
    "liability", "precedent", "Case", "Statutory", "Constitutional", "Criminal", "Tort", "Contract", 
    "International", "Humanitarian", "Environmental", "Labor", "Employment", 
    "Corporate", "Securities", "Regulatory", "implications", "compliance", "dilemmas", "disputes", "issues", 
    "Legal analysis", "counsel", "standards", "standard", "guidelines"],
    
    ["Industry", "Manufacturing", "Production", "Factory", "Industrialization", "revolution", "industrial", 
    "sector", "development", "engineering", "design", 
    "processes", "automation", "Logistics", "Operations", "Efficiency", "Productivity", 
    "Cost reduction", "Resource optimization", "Sustainability", 
    "impact", "economy", "Renewable", "technology", "management", 
    "control", "Emissions", "Carbon footprint", "safety", "Industrial"
    "compliance", "policy", "regulations", "trade", "Tariffs", "Import", "export", 
    "Globalization", "International", "agreements", "Supply", "demand", 
    "analysis", "Market competition", "market", "capital", "firm", "firms",
    "share", "forecasting", "Innovation", "Research", "Digital", "transformation", 
    "analytics", "data", "Artificial intelligence", "Machine learning", 
    "Internet of Things", "IoT" "Robotics", "Automation", "Cybersecurity", 
    "Information technology", "IT" "Cloud computing", "Blockchain", "Augmented reality", 
    "Virtual reality", "Smart technology", "Smart cities", "Smart infrastructure", 
    "Smart transportation", "Smart grid", "Smart homes", "Smart appliances", 
    "Smart sensors", "Smart devices", "Industry associations", 
    "Industry conferences", "Industry publications", "Industry news"]

    ]

    category = {
        0 : 'society',
        1 : 'education',
        2 : 'creativity',
        3 : 'ethical',
        4 : 'industry'

    }

    new_df = df


    def contains_keyword(df, categorization_keywords):
        #make an array of empty dataframes
        filtered_data = [pd.DataFrame() for i in range(len(categorization_keywords))]
        
        #make a 2d array for empty filtered comments
        filtered_comments = [[] for i in range(len(categorization_keywords))]

        # Iterate over each row in the DataFrame
        for index, row in df.iterrows(): 
            # Iterate over each column
            for column in df.columns: 

                #iterate through every category here
                for i in range (0, len(categorization_keywords)):
                    pattern = re.compile('|'.join(categorization_keywords[i]), flags=re.IGNORECASE)

                    # Check if the column is 'comments'
                    if column == 'comments':
                        filtered_comments[i] = []

                        #if filteredcomments is not in list form
                        if not isinstance(filtered_comments[i], list):
                            filtered_comments[i] = eval(filtered_comments[i])


                        #check if column section is a proper string
                        if isinstance(row[column], str):

                            string = make_quotes_same(row[column])
                            new_string = remove_illegal_decimal_literals(string)

                            k = 0

                            #";;;" acts as a delimiter to separate each comment
                            for comment in (new_string.split(";;;")):
                                print(f"comments {k}: {comment}")
                                k +=1
                                print()
                                print(f"category: {category}")
                                # Check if any keyword is present in the comment
                                # if any(keyword in comment for keyword in categorization_keywords):
                                if (bool(pattern.search(string)) == True):
                                    # Append the comment to the filtered comments list
                                    filtered_comments[i].append(comment)
                            # Update the value in the DataFrame with the filtered comments list
                            #creates a list of characters
                            filtered_comments[i] = str(filtered_comments[i])
                            filtered_data[i].at[index, column] = filtered_comments[i]
                    # For other columnsfiltered_comments = str(filtered_comments)
                    else:
                        # Check if the value in the column is a string and contains any keyword
                        if not pd.isna(row[column]) and isinstance(row[column], str) and (bool(pattern.search(row[column])) == True):
                            # Update the value in the DataFrame with the original string
                            filtered_data[i].at[index, column] = row[column]
        

        #iterate through all the dataframes made with the different categories and get sentiment results
        for i in range(0, len(categorization_keywords)):
            filtered_data[i] = filtered_data[i].infer_objects()
            sliceData(filtered_data[i], 50000, timestamp, credentials[5], category[i])
                

    contains_keyword(new_df, categorization_keywords)


#function that will send information to IBM API -- parses max amount of characters each time
def sliceData(df, chunk_size, timestamp, credential, category):
    st.write(category)
    st.write(df)

    selected_columns = df.columns
    chunks_list = []  # List to accumulate chunks
    
    for col in selected_columns:
        # Check if the column has any non-empty strings
        if df[col].str.len().sum() > 0:
            # Loop until there are no more characters
            while any(df[col].str.len() > 0):
                # Get the first chunk of characters in each string
                df['current_character'] = df[col].str.slice(0, chunk_size)

                # Filter out empty and NaN cells
                non_empty_chunk = df['current_character'][(df['current_character'] != '') & df['current_character'].notna()].tolist()


                # Truncate chunks at last space if necessary
                for i, chunk in enumerate(non_empty_chunk):
                    if not chunk.endswith(" "):
                        last_space_index = chunk.rfind(" ")
                        if last_space_index != -1:
                            non_empty_chunk[i] = chunk[:last_space_index]
                            if i + 1 < len(non_empty_chunk):
                                non_empty_chunk[i + 1] = chunk[last_space_index + 1:] + " " + non_empty_chunk[i + 1]
                            else:
                                break

                # Append non-empty chunks
                if non_empty_chunk:
                    chunks_list.append(non_empty_chunk)
                else:
                    break

                # Update the DataFrame
                chunk_size = sum(len(chunk) for chunk in non_empty_chunk)
                df[col] = df[col].str.slice(chunk_size)

    counter = 0
    sadness_total = 0
    joy_total = 0
    fear_total = 0
    disgust_total = 0
    anger_total = 0

    # initialize a set of keywords in the responses from IBM   
    text_items = set()

    # Display or process the accumulated chunks
    for idx, chunk in enumerate(chunks_list):

        string = ' '.join(chunk)
        #converts json to string
        json_string = json.dumps(string)

        string = remove_special_characters(json_string)

        if (string == "" or string == " " or len(string) < 200):
            continue

        #find api key and enter it inside the curly braces
        authenticator = IAMAuthenticator(credential)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            version='2022-04-07',
            authenticator=authenticator
        )

        response = natural_language_understanding.analyze(
            # url='www.ibm.com',
            text = json_string,
            # features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=5))).get_result()
            features = Features(emotion=EmotionOptions())).get_result()


        json_extension = ".json"
        #save it to file path with ALL IBM responses
        json_file_path = f"/home/rocio/Documents/Research/Sentiment-Data/IBM-Responses/sentiment_{timestamp}_{counter}_{category}{json_extension}"

        print(f"current path: {json_file_path}")

        sadness = response['emotion']['document']['emotion']['sadness']
        joy = response['emotion']['document']['emotion']['joy']
        fear = response['emotion']['document']['emotion']['fear']
        disgust = response['emotion']['document']['emotion']['disgust']
        anger = response['emotion']['document']['emotion']['anger']

        #add it to a total sum FOR ALL JSONS PER DAY
        sadness_total += sadness
        joy_total += joy
        fear_total += fear
        disgust_total += disgust
        anger_total += anger

        # Write to JSON file for each response
        with open(json_file_path, 'w') as json_file:
            json.dump(response, json_file, indent=4)

        #starting counter for the amount of sentiment response  taken
        counter += 1

    dataVisualization(counter, sadness_total, joy_total, fear_total, disgust_total, anger_total, timestamp, category)




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

# Calculate date range for "yesterday" (or adjust to the specific day you're fetching for)
yesterday = datetime.utcnow() - timedelta(days=60) #this will extract posts from the last 60 days 
date_limit = yesterday.strftime('%Y%m%d')
timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
timeframe = datetime.utcnow() - timedelta(days=1)

def queryReddit():
    # Fetch posts
    posts_data = []
    # Create a query string with logical OR between search terms
    query_string = " OR ".join(search_terms)

    #place in a set for time complexity - will search in O(1)
    unique_submission_ids = set()

    for submission in reddit.subreddit(subreddit).search(query_string, time_filter='day', limit=20):
        try:
            submission.comments.replace_more(limit=20)
            
            submission_date = datetime.utcfromtimestamp(submission.created_utc)
            
            if submission_date > timeframe: #check if data follows in timeframe - probably dont need since search function already does this

                # Check if the submission ID is not already in the set to avoid duplicates
                if submission.id not in unique_submission_ids:
                    posts_data.append({
                        'title': submission.title,
                        'description': submission.selftext,
                        'comments': [";;;".join(comment.body for comment in submission.comments.list())],
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

    return posts_data

#ask the user for making new query to reddit, or getting biweekly code results

option_result = input("Enter 0 for daily result from reddit query\nEnter 1 for biweekly code analysis\n")
print(option_result)

#option 0 --> real time daily data from reddit
if (option_result == "0"):
    print("here")
    posts_data = queryReddit()
    # Convert to DataFrame
    df = pd.DataFrame(posts_data)


    csv_file_path = 'reddit_posts_'+timestamp+'.csv'
    #raw data path
    csv_file_path1 = '/home/rocio/Documents/Research/Raw-Reddit-Data/'+csv_file_path

    #go from df -> csv
    df.to_csv(csv_file_path1, index=False)

    #go from csv -> df
    df = pd.read_csv(csv_file_path1, encoding='utf-8')

    #filtered data path
    csv_file_path2 = '/home/rocio/Documents/Research/Reddit-Data/'+csv_file_path

    new_df = filterData(df)

    new_df.to_csv(csv_file_path2, index=False)
    print("saved filter data to csv")

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

    categorizeData(new_df, timestamp)

#option 1 --> biweekly data analysis
else:
    df = mergeData()
    if (df.empty):
        raise Exception("There must be at least 1 file to parse through")
        sys.exit(0)
    print(f"df components: {df}")


# Setup logging
date=datetime.utcnow()
name = f"/home/rocio/Documents/Research/Reddit-Data/reddit-data_{timestamp}.log"
logging.basicConfig(filename=name, level=logging.INFO)

def main():
    # Your script logic here
    logging.info(f"Script run at {datetime.now()}")

if __name__ == "__main__":
    main()
    
