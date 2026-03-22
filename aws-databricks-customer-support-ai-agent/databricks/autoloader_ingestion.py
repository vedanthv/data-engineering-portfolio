# Databricks notebook source
# MAGIC %md
# MAGIC ### Orders

# COMMAND ----------

df = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "parquet") \
    .option("cloudFiles.schemaLocation", "s3://customer-support-ai/") \
    .option("cloudFiles.inferColumnTypes", "true") \
    .load("s3://customer-support-ai/orders/")

# COMMAND ----------

df.writeStream \
    .format("delta") \
    .option("checkpointLocation", "s3://customer-support-ai/checkpoints/") \
    .trigger(availableNow=True) \
    .table("customer_suppport_agent.raw.orders")

# COMMAND ----------

# MAGIC %md
# MAGIC ## User Activity / Analytics

# COMMAND ----------

df = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "parquet") \
    .option("cloudFiles.schemaLocation", "s3://customer-support-ai-user-activity/") \
    .option("cloudFiles.inferColumnTypes", "true") \
    .load("s3://customer-support-ai-user-activity/2026")

# COMMAND ----------

df.writeStream \
    .format("delta") \
    .option("checkpointLocation", "s3://customer-support-ai-user-activity/checkpoints/") \
    .option("mergeSchema", "true")\
    .trigger(availableNow=True) \
    .table("customer_suppport_agent.raw.user_activity")

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from customer_suppport_agent.raw.user_activity

# COMMAND ----------

# DBTITLE 1,Convert detail column to individual columns
# MAGIC %sql
# MAGIC create or replace table customer_suppport_agent.raw.user_activity_raw_intermediate as
# MAGIC select
# MAGIC   parsed_detail.ad_id,
# MAGIC   parsed_detail.app_version,
# MAGIC   parsed_detail.browser,
# MAGIC   parsed_detail.campaign_id,
# MAGIC   parsed_detail.click_x,
# MAGIC   parsed_detail.click_y,
# MAGIC   parsed_detail.conversion,
# MAGIC   parsed_detail.created_at,
# MAGIC   parsed_detail.customer_id,
# MAGIC   parsed_detail.device_id,
# MAGIC   parsed_detail.device_type,
# MAGIC   parsed_detail.error_code,
# MAGIC   parsed_detail.error_message,
# MAGIC   parsed_detail.event_id,
# MAGIC   parsed_detail.event_type,
# MAGIC   parsed_detail.experiment_id,
# MAGIC   parsed_detail.feature_flag,
# MAGIC   parsed_detail.ip_address,
# MAGIC   parsed_detail.lat,
# MAGIC   parsed_detail.load_time,
# MAGIC   parsed_detail.location,
# MAGIC   parsed_detail.lon,
# MAGIC   parsed_detail.network,
# MAGIC   parsed_detail.os,
# MAGIC   parsed_detail.page_url,
# MAGIC   parsed_detail.referrer,
# MAGIC   parsed_detail.screen_resolution,
# MAGIC   parsed_detail.scroll_depth,
# MAGIC   parsed_detail.session_id,
# MAGIC   parsed_detail.time_on_page,
# MAGIC   parsed_detail.user_id
# MAGIC from (
# MAGIC   select
# MAGIC     from_json(detail, 'ad_id STRING,app_version STRING,browser STRING,campaign_id STRING,click_x INT,click_y INT,conversion BOOLEAN,created_at STRING,customer_id STRING,device_id STRING,device_type STRING,error_code STRING,error_message STRING,event_id STRING,event_type STRING,experiment_id STRING,feature_flag STRING,ip_address STRING,lat DOUBLE,load_time DOUBLE,location STRING,lon DOUBLE,network STRING,os STRING,page_url STRING,referrer STRING,screen_resolution STRING,scroll_depth DOUBLE,session_id STRING,time_on_page INT,user_id STRING') as parsed_detail
# MAGIC   from customer_suppport_agent.raw.user_activity
# MAGIC   where detail is not null and length(detail) > 10
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from customer_suppport_agent.user_activity_raw_intermediate