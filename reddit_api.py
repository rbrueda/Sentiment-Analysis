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
#   - keep the counter and total --> uses this for the average results --> goes to data visualization
#   - place the responses in separate folders --> so no files will be overwriten


# #this will avoid the csv error -- if this doesnt fix the issue idk what will
csv.field_size_limit(131072)

#gets the last 2 weeks worth of data
def mergeData():
    #extract the files in a certain directory
    folder_name = '/home/rocio/Documents/Research/Reddit-Data'
    all_files = [os.path.join(folder_name, f) for f in os.listdir(folder_name) if f.endswith('.csv')]
    #gets the date 14 days ago
    timeframe = datetime.now() - timedelta(days=14)
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

    ["Poverty", "Inequality", "Discrimination", "Social justice", "Human rights", 
    "Homelessness", "Unemployment", "Education inequality", "Healthcare access", "Mental health stigma",
    "Civil rights movement", "Feminism", "LGBTQ+ rights", "Environmental activism", "Black Lives Matter", 
    "#MeToo movement", "Indigenous rights", "Disability rights",
    "Population trends", "Urbanization", "Rural communities", "Aging population", "Youth demographics", 
    "Migration patterns", "Refugee crisis", "Immigration policy",
    "Multiculturalism", "Cultural assimilation", "Cultural preservation", "Cultural heritage", 
    "Cultural identity", "Ethnic communities", "Intercultural communication",
    "Family structure", "Marriage trends", "Gender roles", "Parenting styles", "Education system", 
    "Healthcare system", "Criminal justice system", "Political institutions",
    "Community engagement", "Neighborhood revitalization", "Community organizing", "Grassroots movements", 
    "Social cohesion", "Community resilience",
    "Social networks", "Social support", "Interpersonal relationships", "Friendship", 
    "Community bonds", "Social capital", "Social isolation",
    "Social media impact", "Digital divide", "Online communities", "Technology addiction", 
    "Cyberbullying", "Privacy concerns", "Digital literacy",
    "Global interconnectedness", "Cultural exchange", "Global economy", "International relations", 
    "Transnational corporations", "Global governance", "Global citizenship",
    "Social progress", "Social reform", "Social innovation", "Social entrepreneurship", 
    "Sustainable development goals", "Advocacy", "Policy change"],

    ["Education", "Schools", "Teachers", "Students", "Classrooms", "Curriculum", "Learning", 
    "Educational technology", "Online learning", "Distance education", "E-learning", "Blended learning", 
    "MOOCs", "Virtual classrooms", "Remote learning", "Digital learning", "Pedagogy", "Andragogy", 
    "Teaching methods", "Instructional design", "Educational psychology", "Assessment", "Testing", 
    "Grading", "Standardized tests", "Alternative assessments", "Learning outcomes", "Educational standards", 
    "Curriculum development", "Education policy", "Education reform", "Educational equity", "Access to education", 
    "Quality education", "Inclusive education", "Special education", "Gifted education", "Early childhood education", 
    "Primary education", "Secondary education", "High school", "K-12 education", "Higher education", 
    "College", "University", "Community college", "Vocational education", "Technical education", 
    "STEM education", "STEAM education", "21st-century skills", "Critical thinking", "Problem-solving", 
    "Creativity", "Collaboration", "Communication skills", "Digital literacy", "Media literacy", 
    "Information literacy", "Financial literacy", "Civic education", "Global citizenship education", 
    "Environmental education", "Health education", "Physical education", "Arts education", 
    "Music education", "Language education", "Bilingual education", "Multilingual education", 
    "Teacher training", "Professional development", "Educational leadership", "School management", 
    "Parental involvement", "Home-school collaboration", "Education funding", "Public education", 
    "Private education", "Charter schools", "Home schooling", "Education technology companies", 
    "Educational research", "Educational conferences", "Education journals", "Education blogs", 
    "Education news", "Education advocacy", "Education grants" ],

    ["Creativity", "Creative thinking", "Innovation", "Imagination", "Originality", "Problem-solving", 
    "Critical thinking", "Divergent thinking", "Convergent thinking", "Lateral thinking", "Design thinking", 
    "Artistic expression", "Creative process", "Inspiration", "Ideation", "Brainstorming", "Mind mapping", 
    "Visualization", "Experimentation", "Risk-taking", "Playfulness", "Curiosity", "Open-mindedness", 
    "Flexibility", "Adaptability", "Resilience", "Resourcefulness", "Inventiveness", "Ingenuity", 
    "Entrepreneurship", "Intrapreneurship", "Creative industries", "Creative economy", "Creative class", 
    "Cultural creativity", "Creativity in education", "Creative teaching", "Fostering creativity", 
    "Creative environments", "Creative collaboration", "Interdisciplinary creativity", "Cross-disciplinary creativity", 
    "Digital creativity", "Media creativity", "Film creativity", "Music creativity", "Literary creativity", 
    "Visual arts creativity", "Performing arts creativity", "Design creativity", "Fashion creativity", 
    "Architecture creativity", "Creative writing", "Poetry", "Storytelling", "Narrative creativity", 
    "Creative problem-solving", "Creativity and innovation management", "Creative leadership", 
    "Creative teams", "Creative culture", "Creativity research", "Creativity measurement", 
    "Creativity assessment", "Assessing creative potential", "Assessing creative thinking", 
    "Assessing creative skills", "Assessing creative performance", "Assessing creative products"],

    ["Ethics", "Legal", "Morality", "Law", "Regulation", "Compliance", "Governance", "Policy", 
    "Ethical principles", "Legal principles", "Human rights", "Civil rights", "Privacy rights", 
    "Data protection", "Confidentiality", "Intellectual property", "Copyright", "Patents", 
    "Trademark", "Fair use", "Plagiarism", "Cybersecurity", "Data privacy", "Online safety", 
    "Surveillance", "Ethical behavior", "Legal framework", "Legal system", "Court system", 
    "Justice system", "Legal rights", "Legal obligations", "Legal responsibilities", 
    "Legal liability", "Legal precedent", "Legal precedent", "Case law", "Statutory law", 
    "Common law", "Constitutional law", "Criminal law", "Civil law", "Tort law", "Contract law", 
    "International law", "Humanitarian law", "Environmental law", "Labor law", "Employment law", 
    "Healthcare law", "Corporate law", "Business law", "Financial law", "Securities law", 
    "Tax law", "Immigration law", "Family law", "Property law", "Real estate law", 
    "Administrative law", "Regulatory law", "Ethical considerations", "Legal implications", 
    "Legal compliance", "Ethical dilemmas", "Legal disputes", "Legal issues", "Ethical issues", 
    "Legal analysis", "Ethical analysis", "Legal advice", "Legal counsel", "Ethical decision-making", 
    "Legal interpretation", "Legal research", "Ethical research", "Legal ethics", "Professional ethics", 
    "Corporate ethics", "Business ethics", "Medical ethics", "Research ethics", "Journalistic ethics", 
    "Ethics codes", "Professional standards", "Legal standards", "Ethical standards", 
    "Ethical guidelines", "Legal guidelines", "Ethical review", "Legal review", "Ethical oversight", 
    "Legal compliance", "Ethical training", "Legal training", "Ethical education", "Legal education"],
    
    ["Industry", "Manufacturing", "Production", "Factory", "Industrialization", "Industrial revolution", 
    "Industrial sector", "Industrial development", "Industrial engineering", "Industrial design", 
    "Industrial processes", "Industrial automation", "Industry 4.0", "Smart factories", 
    "Advanced manufacturing", "Mass production", "Lean manufacturing", "Quality control", 
    "Supply chain management", "Logistics", "Operations management", "Efficiency", 
    "Productivity", "Cost reduction", "Resource optimization", "Sustainability", 
    "Environmental impact", "Green manufacturing", "Circular economy", 
    "Renewable energy", "Clean technology", "Energy efficiency", "Waste management", 
    "Pollution control", "Emissions reduction", "Carbon footprint", "Industrial safety", 
    "Occupational health", "Workplace safety", "Safety regulations", "Industrial accidents", 
    "Risk management", "Emergency preparedness", "Disaster recovery", "Regulatory compliance", 
    "Industrial policy", "Government regulations", "Trade policies", "Tariffs", "Import/export", 
    "Globalization", "International trade", "Trade agreements", "Supply and demand", 
    "Market trends", "Market analysis", "Competitive analysis", "Market competition", 
    "Market segmentation", "Market share", "Market growth", "Market expansion", 
    "Market opportunities", "Market challenges", "Market forecasting", "Business strategy", 
    "Strategic planning", "Business development", "Market development", "Product development", 
    "Innovation", "Research and development", "Technology adoption", "Digital transformation", 
    "Data analytics", "Big data", "Artificial intelligence", "Machine learning", 
    "Internet of Things (IoT)", "Robotics", "Automation", "Cybersecurity", 
    "Information technology", "Cloud computing", "Blockchain", "Augmented reality", 
    "Virtual reality", "Smart technology", "Smart cities", "Smart infrastructure", 
    "Smart transportation", "Smart grid", "Smart homes", "Smart appliances", 
    "Smart sensors", "Smart devices", "Industry associations", "Trade organizations", 
    "Industry conferences", "Industry publications", "Industry news"]

    ]

    def contains_keyword(df, categorization_keywords):
        filtered_data = pd.DataFrame()


        # Iterate over each row in the DataFrame
        for index, row in df.iterrows(): 
            # Iterate over each column
            for column in df.columns: 

                # Check if the column is 'comments'
                if column == 'comments':
                    filtered_comments = []

                    #check if column section is a proper string
                    if isinstance(row[column], str):

                        string = make_quotes_same(row[column])
                        new_string = remove_illegal_decimal_literals(string)

                        i = 0

                        #";;;" acts as a delimiter to separate each comment
                        for comment in (new_string.split(";;;")):
                            print(f"comments {i}: {comment}")
                            i +=1
                            print()
                            # Check if any keyword is present in the comment
                            if any(keyword in comment for keyword in categorization_keywords):
                                # Append the comment to the filtered comments list
                                filtered_comments.append(comment)
                        # Update the value in the DataFrame with the filtered comments list
                        #creates a list of characters
                        filtered_comments = str(filtered_comments)
                        filtered_data.at[index, column] = filtered_comments
                # For other columnsfiltered_comments = str(filtered_comments)
                else:
                    # Check if the value in the column is a string and contains any keyword
                    if not pd.isna(row[column]) and isinstance(row[column], str) and any(keyword in row[column] for keyword in categorization_keywords):
                        # Update the value in the DataFrame with the original string
                        filtered_data.at[index, column] = row[column]

        # Ensure the data types of the columns remain consistent
        filtered_data = filtered_data.infer_objects()
        st.write(filtered_data)
        return filtered_data


    #todo: seems like there is an error with the categorization keywords -- there outputting the same results for all categories
    for i in range (0, len(categorization_keywords)):
        # Concatenate keywords into a regular expression pattern
        pattern = '|'.join(categorization_keywords[i])

        #check which category we are currently looking at
        if (i == 0):
            category = "society"

        elif (i == 1):
            category = "education"

        elif (i == 2):
            category = "creativity"
        
        elif (i == 3):
            category = "ethical"

        else:
            category = "industry"

        filtered_data = contains_keyword(df, pattern)
        sliceData(filtered_data, 50000, timestamp, credentials[5], category)
                
    
    




#function that will send information to IBM API -- parses max amount of characters each time
def sliceData(df, chunk_size, timestamp, credential, category):

    selected_columns = ["title", "description", "comments"]
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

    #todo: add this function outsie the if statement once todo below is fixed
    categorizeData(new_df, timestamp)

#option 1 --> biweekly data analysis
#todo: integrate categorize data for this -- once ";;;" are added to all data
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
    
