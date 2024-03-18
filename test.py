import ast
import pandas as pd
import streamlit as st
import regex as re
import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features,CategoriesOptions,EmotionOptions,KeywordsOptions
import datetime
from ast import literal_eval

def remove_special_characters(input_string):
    # Use regex to replace all instances of special characters including square brackets with an empty string
    result_string = re.sub(r'[\\\@\&\$\[\]\u0000-\u001f]', '', input_string)
    return result_string


def make_quotes_same(input_string, target_quote='"'):
    if target_quote not in ('"', "'"):
        raise ValueError("Target quote must be either ' or \"")

    return input_string.replace("'", target_quote).replace('"', target_quote).replace("’", "'").replace('“', target_quote).replace('”', target_quote).replace("‘", "'")

#function that will read every 5000 characters
# Function to filter data
def sliceData(df, chunk_size, timestamp, credential):
    st.write(df)

    selected_columns = ["title", "description", "comments"]
    chunks_list = []  # List to accumulate chunks
    
    for col in selected_columns:
        # Check if the column has any non-empty strings
        if df[col].str.len().sum() > 0:
            # Loop until there are no more characters
            while any(df[col].str.len() > 0):
                # Get the first chunk of characters in each string
                df['current_character'] = df[col].str.slice(0, chunk_size)

                st.write(df)

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
    
    print("here")            
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
        # st.write(f"Chunk {idx + 1}:", chunk)
        #print(f"chunk {idx}:")

        string = ' '.join(chunk)
        #print(string)
        #converts json to string
        json_string = json.dumps(string)

        string = remove_special_characters(json_string)

        st.write(f"Chunk {idx+1}:", string)

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
            features=Features(keywords=KeywordsOptions(sentiment=True,emotion=True,limit=5))).get_result()

        json_extension = ".json"
        #save it to file path with ALL IBM responses
        json_file_path = f"/home/rocio/Documents/Research/Sentiment-Data/IBM-Responses/sentiment_{timestamp}_{counter}{json_extension}"

        print(f"current path: {json_file_path}")

        #gets the list of keywords that are popular in each reponse
        for keyword in response["keywords"]:
            text_items.add(str(keyword["text"]))


        # Calculate average emotion values for each keyword PER JSON
        sadness = sum(keyword.get("emotion", {}).get("sadness", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        joy = sum(keyword.get("emotion", {}).get("joy", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        fear = sum(keyword.get("emotion", {}).get("fear", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        disgust = sum(keyword.get("emotion", {}).get("disgust", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))
        anger = sum(keyword.get("emotion", {}).get("anger", 0) for keyword in response.get("keywords", [])) / len(response.get("keywords", []))

        #add it to a total sum FOR ALL JSONS PER DAY
        sadness_total += sadness
        joy_total += joy
        fear_total += fear
        disgust_total += disgust
        anger_total += anger

        print(f"sadness_total: {sadness_total}")

        # Write to JSON file for each response
        with open(json_file_path, 'w') as json_file:
            json.dump(response, json_file, indent=4)

        #starting counter for the amount of sentiment response  taken
        counter += 1


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
                    # print(f"{row[column]}, {column}")
                    # print()
                    # print(type(row[column]))
                    #if isinstance(row[column], list):
                    if isinstance(row[column], str):

                        string = make_quotes_same(row[column])

                        
                        print()
                        # Create a list to store filtered comments 
                        filtered_comments = []
                        # Iterate over each comment in the list
                        lst = ast.literal_eval(row[column])
                        for comment in (string.split("',") or string.split("\",")): 
                        # for comment in lst:
                        # for comment in row[column]:
                            print(f"comment: {comment}")
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
        return filtered_data


    # Function to check if any of the keywords are present in any column
    # def contains_keyword(row):
    #     st.write(f"row: ")
    #     return any(row.str.contains(pattern, case=False))

    for i in range (0, len(categorization_keywords)):
        # Concatenate keywords into a regular expression pattern
        pattern = '|'.join(categorization_keywords[i])

        # Check if any of the keywords are present in the text_column
        # filtered_data = df[df.apply(contains_keyword, axis=1)]
        filtered_data = contains_keyword(df, pattern)
        sliceData(filtered_data, 10000, timestamp, credentials[5])
                
    






    


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

    # this is a more efficient way to do the below code in which will allow for any size -- wont result to csv field limit error
    # Apply the function only to non-list columns
    # Use DataFrame.apply with the map method
    #for unicode pattern
    new_df = new_df.apply(lambda x: x.map(lambda elem: re.sub(emoji_pattern, ' ', str(elem)) if pd.notna(elem) and not isinstance(elem, list) else elem))

    # cleans the dataframe from escape characters
    new_df = new_df.replace(to_replace=r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*", value='', regex=True)
    # cleans the dataframe from hyperlinks
    new_df = new_df.replace(to_replace=r'\\[^\s]', value='', regex=True)
    # cleans the dataframe from asterisks
    new_df = new_df.replace(to_replace=r'\*+', value=' ', regex=True)
    #additonal characters that where not cleaned
    new_df = new_df.replace(to_replace=r'([*/<>#]|/|&#x200B;)+|\s{2,}', value=' ', regex=True)

    # Apply the function to each element in the "comments" column
    new_df['comments'] = new_df['comments'].apply(lambda comments: [re.sub(emoji_pattern, ' ', str(comment)) for comment in comments] if isinstance(comments, list) else comments)

    return new_df

credentials = []
with open('credentials.txt', 'r') as f:
    for content in f:
        #add to array of content
        credentials.append(content.strip())

df = pd.read_csv('/home/rocio/Documents/Research/Reddit-Data/reddit_posts_2024-03-01_215308.csv', encoding='utf-8')

new_df = filterData(df)

print(new_df)

#df.to_csv(csv_file_path1, index=False)
new_df.to_csv('/home/rocio/Documents/Research/Reddit-Data/hello.csv', index=False)
print("saved filter data to csv")


timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')

categorizeData(new_df, timestamp)


# selected_columns = ["title", "description", "comments"]
# subset_df = new_df.loc[:, selected_columns]

# chunk_size = 10000 #maximum amount of characters allowed per request ot the ibm api


# #this will slice data every 5000 characters and then make request to sentiment api
# sliceData(new_df, selected_columns, chunk_size, timestamp, credentials[5])