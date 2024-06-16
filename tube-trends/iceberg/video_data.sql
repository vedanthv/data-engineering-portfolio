-- create table from S3
CREATE EXTERNAL table creator_analytics.video_data
    (
        channelId string,
        description string,
        length_of_video string,
        publishedDate date,
        publishedAt timestamp,
        publishedTimeText string,
        title string,
        videoId string,
        viewCount bigint
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    STORED AS TEXTFILE
    LOCATION 's3://yt-analytics/videos_metadata/';

-- create iceberg table schema
CREATE table creator_analytics.video_data_iceberg
    (
        channelId string,
        description string,
        length_of_video string,
        publishedDate date,
        publishedAt timestamp,
        publishedTimeText string,
        title string,
        videoId string,
        viewCount bigint
    )
      LOCATION 's3://yt-analytics/video_data_iceberg/'
      TBLPROPERTIES ('table_type' ='ICEBERG');

-- create manipulation table
CREATE table creator_analytics.video_data_iceberg_manipulation
    (
        channelId string,
        description string,
        length_of_video string,
        publishedDate date,
        publishedAt timestamp,
        publishedTimeText string,
        title string,
        videoId string,
        viewCount bigint
    )
      LOCATION 's3://yt-analytics/videos_metadata_iceberg/'
      TBLPROPERTIES ('table_type' ='ICEBERG');

-- insert data into iceberg table
INSERT INTO creator_analytics.video_data_iceberg
SELECT * FROM 
creator_analytics.video_data
