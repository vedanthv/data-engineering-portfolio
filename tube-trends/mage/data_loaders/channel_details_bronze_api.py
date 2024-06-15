import io
import pandas as pd
import requests
import http.client
import json

conn = http.client.HTTPSConnection("yt-api.p.rapidapi.com")

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@data_loader
def load_data_from_api(*args, **kwargs):
    """
    Function for loading channel metadata from API using http.client and converting it to a pandas DataFrame.
    """
    headers = {
        'x-rapidapi-key': "2781ae1228mshc6f17aab7ec0136p15b6cfjsn2c26196d15cc",
        'x-rapidapi-host': "yt-api.p.rapidapi.com"
    }
    
    base_path = "/channel/home?id="
    conn = http.client.HTTPSConnection("yt-api.p.rapidapi.com")

    # Initialize an empty list to store DataFrames for each channel
    dfs = []

    for channel_id in channel_ids:
        conn.request("GET", base_path + channel_id, headers=headers)
        res = conn.getresponse()
        data = res.read()

        # Parse the response data if it's in JSON format
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError:
            parsed_data = None

        # Convert the parsed JSON data to a pandas DataFrame
        if isinstance(parsed_data, list):
            df = pd.DataFrame(parsed_data)
        elif isinstance(parsed_data, dict):
            df = pd.json_normalize(parsed_data)
        else:
            df = pd.DataFrame()

        dfs.append(df)

    conn.close()

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df

# Example usage
channel_ids = ["UCCezIgC97PvUuR4_gbFUs5g","UCh9nVJoWXmFb7sLApWGcLPQ","UCAq9f7jFEA7Mtl3qOZy2h1A","UCAEOtPgh29aXEt31O17Wfjg"]

df = load_data_from_api(channel_ids)

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
