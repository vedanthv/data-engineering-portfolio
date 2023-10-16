# Databricks notebook source
# MAGIC %md
# MAGIC ## Ingest and Process Races File

# COMMAND ----------

from pyspark.sql.types import StructType,IntegerType,StringType,DateType,StructField

# COMMAND ----------

races_schema = StructType(fields = [StructField("raceId",IntegerType(),False),
                                    StructField("year",IntegerType(),True),
                                    StructField("round",IntegerType(),True),
                                    StructField("circuitId",IntegerType(),True),
                                    StructField("name",StringType(),True),
                                    StructField("date",DateType(),True),
                                    StructField("time",StringType(),True),
                                    StructField("url",StringType(),True)
                                    
])

# COMMAND ----------

# MAGIC %fs
# MAGIC ls dbfs:/mnt/formula1dlvb/raw/

# COMMAND ----------

races_df = spark.read.option("header",True).schema(races_schema).csv("dbfs:/mnt/formula1dlvb/raw/races.csv")

# COMMAND ----------

display(races_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Adding the ```race_timestamp``` and ```ingestion_date``` columns

# COMMAND ----------

from pyspark.sql.functions import current_timestamp,to_timestamp,concat,col,lit

# COMMAND ----------

races_with_timestamp_df = races_df.withColumn("ingestionDate",current_timestamp()).withColumn("race_timestamp",to_timestamp(concat(col("date"),lit(' '),col('time')),'yyyy-MM-dd HH:mm:ss'))

# COMMAND ----------

display(races_with_timestamp_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Selecting Only Required Columns

# COMMAND ----------

races_selected_df = races_with_timestamp_df.select(col('raceId').alias('race_id'),col('year').alias('race_year'),col('round'),col('circuitId').alias('circuit_id'),col('name'),col('ingestionDate').alias('ingestion_date'),col('race_timestamp'))

# COMMAND ----------

display(races_selected_df)

# COMMAND ----------

races_selected_df.write.mode('overwrite').parquet('/mnt/formula1dlvb/processed/races')

# COMMAND ----------

# MAGIC %fs
# MAGIC ls "/mnt/formula1dlvb/processed/races"

# COMMAND ----------

# MAGIC %md 
# MAGIC ### Partitioning by ```race_year```

# COMMAND ----------

# takes long time as spark creates one folder per race year
races_selected_df.write.mode('overwrite').partitionBy('race_year').parquet('/mnt/formula1dlvb/processed/races')

# COMMAND ----------

# MAGIC %fs
# MAGIC ls "/mnt/formula1dlvb/processed/races"

# COMMAND ----------

