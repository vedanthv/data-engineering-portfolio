import io
import pandas as pd # type: ignore
import requests # type: ignore
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.s3 import S3
from pandas import DataFrame
from os import path


@data_loader #type:ignore
def load_data_from_api(*args, **kwargs):
    url = 'https://raw.githubusercontent.com/mage-ai/datasets/master/restaurant_user_transactions.csv'
    response = requests.get(url)
    return pd.read_csv(io.StringIO(response.text), sep=',')

@test #type:ignore
def test_row_count(df, *args) -> None:
    assert len(df.index) >= 1000, 'The data does not have enough rows.'

def number_of_rows_per_key(df, key, column_name):
    data = df.groupby(key)[key].agg(['count'])
    data.columns = [column_name]
    return data


def clean_column(column_name):
    return column_name.lower().replace(' ', '_')


@transformer # type: ignore
def transform(df, *args, **kwargs):
    # Add number of meals for each user
    df_new_column = number_of_rows_per_key(df, 'user ID', 'number of meals')
    df = df.join(df_new_column, on='user ID')

    # Clean column names
    df.columns = [clean_column(col) for col in df.columns]

    return df.iloc[:100]

@test
def test_number_of_columns(df, *args) -> None:
    assert len(df.columns) >= 11, 'There needs to be at least 11 columns.'


if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_data_to_s3(df: DataFrame, **kwargs) -> None:
    """
    Template for exporting data to a S3 bucket.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#s3
    """
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    bucket_name = 'mage-to-s3'
    object_key = 'test_from_mage.csv'

    return S3.with_config(ConfigFileLoader(config_path, config_profile)).export(
        df,
        bucket_name,
        object_key,
    )
