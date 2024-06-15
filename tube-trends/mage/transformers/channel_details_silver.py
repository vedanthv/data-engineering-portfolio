if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

def drop_columns(df):
    dropped_clean = df.drop(["meta.channelId","continuation","data","msg", 
    'meta.banner',"meta.videosCount","meta.isUnlisted",
    "meta.availableCountries","meta.tabs",
    "meta.channelHandle","meta.channelHandle",
    "meta.avatar","meta.banner","meta.mobileBanner","meta.tvBanner","meta.videosCountText"],axis = 1)
    return dropped_clean

@transformer
def transform(df, *args, **kwargs):
    # Specify your transformation logic here
    dropped_transform = drop_columns(df)
    return dropped_transform


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
