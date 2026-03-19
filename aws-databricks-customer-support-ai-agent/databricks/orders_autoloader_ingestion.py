# Databricks notebook source
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

# MAGIC %sql
# MAGIC select count(*) from customer_suppport_agent.raw.orders