# Databricks notebook source
# MAGIC %md 
# MAGIC # Ingest Circuits file

# COMMAND ----------

display(dbutils.fs.mounts())

# COMMAND ----------

# MAGIC %fs
# MAGIC ls /mnt/formula1dlvb/raw

# COMMAND ----------

circuits_df = spark.read.option("header",True).option("inferSchema",True).csv("dbfs:/mnt/formula1dlvb/raw/circuits.csv")

# inferSchema goes through the data, identify what the schema is and apply it to the data.The complete data is read and this is not suitable in production environment and it can slow down reads.

# COMMAND ----------

type(circuits_df)

# COMMAND ----------

display(circuits_df)

# COMMAND ----------

circuits_df.printSchema()

# COMMAND ----------

display(circuits_df.describe())

# COMMAND ----------

# MAGIC %md
# MAGIC **Schema Definition**

# COMMAND ----------

# struct_type -> row
# struct_field -> column

from pyspark.sql.types import StructType,StructField,IntegerType, StringType, DoubleType

# COMMAND ----------

circuits_schema = StructType(fields = [
    StructField("circuitId",IntegerType(),False),
    StructField("circuitRef",StringType(),True),
    StructField("name",StringType(),True),
    StructField("location",StringType(),True),
    StructField("country",StringType(),True),
    StructField("lat",StringType(),True),
    StructField("lng",StringType(),True),
    StructField("alt",IntegerType(),True),
    StructField("url",StringType(),True)
])

# COMMAND ----------

circuits_df = spark.read.option("header",True).schema(circuits_schema).csv("dbfs:/mnt/formula1dlvb/raw/circuits.csv")

# COMMAND ----------

circuits_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC **Selecting Only Required Columns**

# COMMAND ----------

circuits_selected = circuits_df.select("circuitId","circuitRef","name","location","lat","lng","alt")

# COMMAND ----------

from pyspark.sql.functions import col

# COMMAND ----------

circuits_selected = circuits_df.select(col("circuitId"),col("circuitRef"),col("name"),col("location").alias("race_location"),col("lat"),col("lng"),col("alt"))

# COMMAND ----------

display(circuits_selected)

# COMMAND ----------

# MAGIC %md
# MAGIC **Renaming Columns**

# COMMAND ----------

circuits_renamed_df = circuits_selected\
.withColumnRenamed("circuitId","circuit_id")\
.withColumnRenamed("lat","latitude")\
.withColumnRenamed("lng","longitude")\
.withColumnRenamed("alt","altitude")


# COMMAND ----------

display(circuits_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Add Columns

# COMMAND ----------

from pyspark.sql.functions import current_timestamp,lit

# COMMAND ----------

circuits_final_df = circuits_renamed_df.withColumn("ingestion_date",current_timestamp()).withColumn("env",lit("Production"))

# COMMAND ----------

display(circuits_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Write to Parquet file

# COMMAND ----------

circuits_final_df.write.mode("overwrite").parquet("dbfs:/mnt/formula1dlvb/processed/circuits")

# COMMAND ----------

# MAGIC %fs
# MAGIC ls "dbfs:/mnt/formula1dlvb/processed/circuits"

# COMMAND ----------

df = spark.read.parquet("dbfs:/mnt/formula1dlvb/processed/circuits")

# COMMAND ----------

display(df)

# COMMAND ----------

