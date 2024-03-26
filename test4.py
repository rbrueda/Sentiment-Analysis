import pandas as pd
import os
import timedelta
from datetime import time, timedelta,datetime

#! note: this process is pretty slow --> takes around 30 seconds to complete. Also the csv file is so large i am not able to load it
#get the last 2 weeks work of data
#todo: add this code to our new data
#todo: add ";;;" to all datasets affected
def mergeData():
    folder_name = '/home/rocio/Documents/Research/Reddit-Data'
    all_files = [os.path.join(folder_name, f) for f in os.listdir(folder_name) if f.endswith('.csv')]
    timeframe = datetime.now() - timedelta(days=14)
    timeframe= timeframe.strftime('%Y-%m-%d_%H%M%S')

    biweekly_data = []
    for file in all_files:
        file = str(file)
        data = file.replace("/home/rocio/Documents/Research/Reddit-Data/", "").replace(".csv", "")
        if (data >= timeframe):
            biweekly_data.append(file)

    print(biweekly_data)

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

df = mergeData()
if (df.empty):
    raise Exception("There must be at least 1 file to parse through")
    sys.exit(0)
print(f"df components: {df}")