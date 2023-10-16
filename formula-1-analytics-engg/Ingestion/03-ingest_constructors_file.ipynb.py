# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest constructors JSON File

# COMMAND ----------

constructors_schema = "constructorId INT, constructorRef STRING, name STRING, nationality STRING, url STRING"

# COMMAND ----------

# MAGIC %fs
# MAGIC ls /mnt/formula1dlvb/raw

# COMMAND ----------

constructors_df = spark.read.schema(constructors_schema).json("/mnt/formula1dlvb/raw/constructors.json")

# COMMAND ----------

display(constructors_df)

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Drop Unwanted Columns

# COMMAND ----------

from pyspark.sql.functions import col

# COMMAND ----------

constructors_dropped_df = constructors_df.drop(col('url'))

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Rename Columns and Add IngestionDate

# COMMAND ----------

from pyspark.sql.functions import current_timestamp

# COMMAND ----------

constructor_final_df = constructors_dropped_df.withColumnRenamed("constructorId","constructor_id")\
                                              .withColumnRenamed("constructorRef","constructor_ref")\
                                              .withColumn("ingestion_date",current_timestamp())  

# COMMAND ----------

constructor_final_df.write.mode('overwrite').parquet("/mnt/formulaa1dlvb/processed/constructors")

# COMMAND ----------

display(constructor_final_df)

# COMMAND ----------

