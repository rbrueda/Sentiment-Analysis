import praw
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Your existing Reddit data fetching logic
#this is going to make a system call to the reddit_api in order ot make our new filtered dataframe
#exec(open("reddit_api.py").read())

#import the posts_data variable from the test.py file
import reddit_api
from reddit_api import new_df #this imports the data from the test.py file

# Assuming df is your DataFrame


# Assuming df is your DataFrame
# df = pd.DataFrame(posts_data)

@app.route('/')
def hello_world():
    return "Hello World"

@app.route('/getRedditData', methods=['GET'])
def get_reddit_data():
    return jsonify(new_df.to_dict(orient='records'))  # Converts DataFrame to JSON response

@app.route('/listFiles', methods=['GET'])
def list_files():
    directory = '/home/rocio/Documents/Research/Reddit-Data'  # Replace with your directory path
    files = os.listdir(directory)
    csv_files = [file for file in files if file.endswith('.csv')]
    log_files = [file for file in files if file.endswith('.log')]
    return jsonify({'csv_files': csv_files, 'log_files': log_files})

@app.route('/getCSVData/<filename>', methods=['GET'])
def get_csv_data(filename):
    filepath = os.path.join('/home/rocio/Documents/Research/Reddit-Data', filename)
    if os.path.exists(filepath) and filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
        return jsonify(df.to_dict(orient='records'))
    else:
        return jsonify({"error": "File not found or is not a CSV file"}), 404

if __name__ == '__main__':
    #print("Starting Flask app on http://0.0.0.0:5000/")
    app.run(debug=True, host='0.0.0.0', port=5001)