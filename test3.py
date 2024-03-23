import re
import pandas as pd

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

    # cleans the dataframe from hyperlinks
    new_df = new_df.replace(to_replace=r"\[?(https?://)?\S+\]?\(?(https?://)?\S+\)?", value='', regex=True)
    new_df = new_df.replace(to_replace=r'\\[^\s]', value='', regex=True)
    # cleans the dataframe from asterisks
    new_df = new_df.replace(to_replace=r'\*+', value=' ', regex=True)
    #additonal characters that where not cleaned
    new_df = new_df.replace(to_replace=r'([*/<>#]|/|&#x200B;)+|\s{2,}', value=' ', regex=True)
    new_df = new_df.replace('*', '')


    # Apply the function to each element in the "comments" column
    new_df['comments'] = new_df['comments'].apply(lambda comments: [re.sub(emoji_pattern, ' ', str(comment)) for comment in comments] if isinstance(comments, list) else comments)

    return new_df


