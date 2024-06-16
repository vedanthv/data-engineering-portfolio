-- create external table from csv
CREATE EXTERNAL table creator_analytics.channel_data
    (
        title string,
        description string,
        facebookProfileId string,
        metaD string,
        subscriberCountText string,
        subscriberCount bigint,
        keywords string
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    STORED AS TEXTFILE
    LOCATION 's3://yt-analytics/channel_metadata/';

-- create iceberg table
CREATE table creator_analytics.channel_data_iceberg
    (
        title string,
        description string,
        facebookProfileId string,
        metaD string,
        subscriberCountText string,
        subscriberCount bigint,
        keywords string
    )
      LOCATION 's3://yt-analytics/channel_data_iceberg/'
      TBLPROPERTIES ('table_type' ='ICEBERG');

-- backup of iceberg table for manipulations
CREATE table creator_analytics.channel_data_iceberg_manipulation
    (
        title string,
        description string,
        facebookProfileId string,
        metaD string,
        subscriberCountText string,
        subscriberCount bigint,
        keywords string
    )
      LOCATION 's3://yt-analytics/channel_data_iceberg/'
      TBLPROPERTIES ('table_type' ='ICEBERG');

-- insert data into the iceberg table
INSERT INTO creator_analytics.channel_data_iceberg
SELECT * FROM 
creator_analytics.channel_data

-- insert data from the stg table to the transformation table
INSERT INTO channel_data_iceberg_manipulation 
SELECT * FROM channel_data_iceberg

-- time travel based on partition
SELECT * FROM channel_data_iceberg_manipulation 
WHERE title = "Corey Schafer"

