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
    Function for loading data from an API using http.client and converting it to a pandas DataFrame.
    """
    headers = {
        'x-rapidapi-key': "{{env.variable.rapidapikey}}",
        'x-rapidapi-host': "{{env.variable.rapidapi-host}}"
    }

    conn = http.client.HTTPSConnection("yt-api.p.rapidapi.com")

    conn.request("GET", "/channel/home?id=UC8butISFwT-Wl7EV0hUK0BQ", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    # Parse the response data if it's in JSON format
    try:
        parsed_data = json.loads(data)
    except json.JSONDecodeError:
        parsed_data = None

    conn.close()

    # Convert the parsed JSON data to a pandas DataFrame
    if isinstance(parsed_data, list):
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(parsed_data)
    elif isinstance(parsed_data, dict):
        # Normalize nested dictionaries
        df = pd.json_normalize(parsed_data)
    else:
        df = pd.DataFrame()

    return df

# Example usage
df = load_data_from_api()

print(df.columns)

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
