import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv("/home/rocio/Documents/research/Data-To-Use/2024-03/2024-03-10_161913.csv")

# Define a function to replace quotes followed by commas with ";;;"
def replace_quotes_commas(comment):
    return comment.replace('",', ";;;").replace("',", ";;;")

# Apply the function to the comments column
df['comments'] = df['comments'].apply(replace_quotes_commas)

# Save the modified DataFrame to a new CSV file
df.to_csv("2024-03-10_161913.csv", index=False)
