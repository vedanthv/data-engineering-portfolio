# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest and Transform Drivers File

# COMMAND ----------

from pyspark.sql.types import StructType,StructField,IntegerType, StringType,DateType

# COMMAND ----------

name_schema = StructType(fields = [StructField("forename",StringType(),True),
                                   StructField("surname",StringType(),True)
                                   ])

# COMMAND ----------

drivers_schema = StructType(fields = [StructField("driverId",IntegerType(),False),
                                      StructField("driverRef",StringType(),True),
                                      StructField("number",IntegerType(),True),
                                      StructField("code",StringType(),True),
                                      StructField("name",name_schema),
                                      StructField("dob",DateType(),True),
                                      StructField("nationality",StringType(),True),
                                      StructField("url",StringType(),True)
                                      ])

# COMMAND ----------

# MAGIC %fs
# MAGIC ls dbfs:/mnt/formula1dlvb/processed/

# COMMAND ----------

drivers_df = spark.read.schema(drivers_schema).json("dbfs:/mnt/formula1dlvb/raw/drivers.json")

# COMMAND ----------

drivers_df.printSchema()

# COMMAND ----------

display(drivers_df)

# COMMAND ----------

from pyspark.sql.functions import col,concat,current_timestamp,lit

# COMMAND ----------

drivers_col_rename_df = drivers_df.withColumnRenamed("driverId","driver_id") \
                                  .withColumnRenamed("driverRef","driver_ref") \
                                  .withColumn("ingestion_date",current_timestamp()) \
                                  .withColumn("name",concat(col("name.forename"),lit(" "),concat(col("name.surname"))))      

# COMMAND ----------

display(drivers_col_rename_df)

# COMMAND ----------

drivers_final_df = drivers_col_rename_df.drop(col("url"))

# COMMAND ----------

drivers_final_df.write.mode("overwrite").parquet("dbfs:/mnt/formula1dlvb/processed/drivers")

# COMMAND ----------

