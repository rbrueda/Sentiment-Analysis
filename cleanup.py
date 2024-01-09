import requests
import pandas as pd

def truncate_large_cells(data, max_length=5000):
    """ Truncate strings in DataFrame cells to max_length. """
    for col in data.columns:
        # Check if the column is of object type (i.e., likely a string)
        if data[col].dtype == object:
            # Truncate strings to max_length
            data[col] = data[col].apply(lambda x: x[:max_length] if isinstance(x, str) else x)
    return data


#for getting the list of filenames
url1 = "http://54.89.222.165/listFiles"

#probably should do error handling here but this gets the filenames in one array
csvFiles = requests.get(url1).json()['csv_files']

numberOfFiles = 10

for i in range(numberOfFiles):
    csvFilename = csvFiles[i]
    print(csvFilename)

    url2 = f"http://54.89.222.165/getCSVData/{csvFilename}"
    data = requests.get(url2)

    if data.status_code == 200:
        json_data = data.json()

        df = pd.DataFrame(json_data)

        # Apply truncation to DataFrame
        df = truncate_large_cells(df)

        # Save the truncated DataFrame to CSV
        df.to_csv(f'{csvFilename}', index=False)

        print(f"Data has been written to {csvFilename}")
    else:
        print("Failed to fetch data. Status code:", data.status_code)

