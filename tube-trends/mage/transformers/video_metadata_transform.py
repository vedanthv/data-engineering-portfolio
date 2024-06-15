import json
import pandas as pd
from pandas import json_normalize

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    df = json_normalize(data, sep='_')
    normalized_df_data = df['data'].apply(pd.Series).stack().reset_index(level=1, drop=True).apply(pd.Series)
    normalized_df_data.drop(["type","thumbnail","richThumbnail"],axis = 1,inplace = True)
    
    df_channel_id = df["meta_channelId"].to_frame()
    final_df = df_channel_id.join(normalized_df_data)

    return final_df

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
