# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE TABLE customer_suppport_agent.raw.analytics_embeddings (
# MAGIC   session_id STRING,
# MAGIC   text STRING,
# MAGIC   embedding ARRAY<DOUBLE>)
# MAGIC USING delta
# MAGIC TBLPROPERTIES (
# MAGIC   'delta.enableChangeDataFeed' = 'true',
# MAGIC   'delta.enableDeletionVectors' = 'true',
# MAGIC   'delta.enableRowTracking' = 'true',
# MAGIC   'delta.feature.appendOnly' = 'supported',
# MAGIC   'delta.feature.changeDataFeed' = 'supported',
# MAGIC   'delta.feature.deletionVectors' = 'supported',
# MAGIC   'delta.feature.domainMetadata' = 'supported',
# MAGIC   'delta.feature.invariants' = 'supported',
# MAGIC   'delta.feature.rowTracking' = 'supported',
# MAGIC   'delta.minReaderVersion' = '3',
# MAGIC   'delta.minWriterVersion' = '7',
# MAGIC   'delta.parquet.compression.codec' = 'zstd')

# COMMAND ----------

# DBTITLE 1,Create Custom Text Column
from pyspark.sql.functions import concat, lit, to_json, struct, when,col,substring,concat_ws,coalesce

df = spark.sql(f'''select * from customer_suppport_agent.raw.user_activity_raw_intermediate where session_id not in (select session_id from customer_suppport_agent.raw.analytics_embeddings)''')

df = df.withColumn(
    "time_bucket",
    when(col("time_on_page").isNull(), "unknown session duration")
    .when(col("time_on_page") < 5, "very short session")
    .when(col("time_on_page") < 30, "short session")
    .when(col("time_on_page") < 120, "moderate session")
    .otherwise("long session")
)

df = df.withColumn(
    "scroll_bucket",
    when(col("scroll_depth").isNull(), "unknown scroll behavior")
    .when(col("scroll_depth") < 0.25, "low engagement")
    .when(col("scroll_depth") < 0.75, "medium engagement")
    .otherwise("high engagement")
)

df = df.withColumn(
    "load_bucket",
    when(col("load_time").isNull(), "unknown performance")
    .when(col("load_time") < 1, "fast load")
    .when(col("load_time") < 3, "average load")
    .otherwise("slow load")
)

# -------------------------
# 2. Clean columns
# -------------------------

def clean_col(c):
    return coalesce(col(c).cast("string"), lit("unknown"))

df = df.withColumn("error_message_trim", substring(col("error_message"), 1, 300)) \
       .withColumn("page_url_trim", substring(col("page_url"), 1, 200)) \
       .withColumn("referrer_trim", substring(col("referrer"), 1, 200))

# -------------------------
# 3. Build embedding text
# -------------------------

df = df.withColumn(
    "text",
    concat_ws("\n",
        col("customer_id"),
        # EVENT
        concat_ws(" ",
            lit("EVENT:"),
            clean_col("event_type"),
            lit("on"),
            clean_col("page_url_trim")
        ),

        concat_ws(" ",
            lit("REFERRER:"),
            clean_col("referrer_trim")
        ),

        # DEVICE
        concat_ws(" ",
            lit("DEVICE:"),
            clean_col("device_type"),
            lit("device using"),
            clean_col("browser"),
            lit("on"),
            clean_col("os")
        ),

        concat_ws(" ",
            lit("Network:"),
            clean_col("network"),
            lit("App version:"),
            clean_col("app_version"),
            lit("Screen:"),
            clean_col("screen_resolution")
        ),

        # BEHAVIOR
        concat_ws(" ",
            lit("USER BEHAVIOR: Session was"),
            col("time_bucket"),
            lit("with"),
            col("scroll_bucket")
        ),

        concat_ws(" ",
            lit("Click position at"),
            lit("("),
            clean_col("click_x"),
            lit(","),
            clean_col("click_y"),
            lit(")")
        ),

        # PERFORMANCE
        concat_ws(" ",
            lit("PERFORMANCE: Page had"),
            col("load_bucket")
        ),

        # OUTCOME
        concat_ws(" ",
            lit("OUTCOME: User"),
            when(col("conversion") == True, "converted").otherwise("did not convert")
        ),

        # ERROR
        concat_ws(" ",
            lit("ERROR: Code"),
            clean_col("error_code"),
            lit("Message"),
            coalesce(col("error_message_trim"), lit("none"))
        ),

        # EXPERIMENT
        concat_ws(" ",
            lit("EXPERIMENT:"),
            clean_col("experiment_id"),
            lit("Feature flag:"),
            clean_col("feature_flag"),
            lit("Campaign:"),
            clean_col("campaign_id")
        ),

        # CONTEXT
        concat_ws(" ",
            lit("CONTEXT: Location"),
            clean_col("location"),
            lit("Time"),
            clean_col("created_at")
        )
    )
)

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.sql.functions import col

window = Window.orderBy("session_id")

df = df.withColumn("row_num", row_number().over(window))

# COMMAND ----------

# DBTITLE 1,Define Batch Size
total_rows = df.count()
batch_size = 20

# COMMAND ----------

# DBTITLE 1,Construct Embeddings
from pyspark.sql.functions import expr

for start in range(1, total_rows + 1, batch_size):
    
    end = start + batch_size

    print(f"Processing rows {start} to {end}")

    batch_df = df.filter(
        (df.row_num >= start) & (df.row_num < end)
    )

    batch_df = batch_df.coalesce(2)

    batch_df = batch_df.withColumn(
        "embedding",
        expr("ai_query('databricks-bge-large-en', text)")
    )

    # Write incrementally
    batch_df.select("session_id", "text", "embedding") \
        .write \
        .format("delta") \
        .mode("append") \
        .option("mergeSchema", "true").saveAsTable("customer_suppport_agent.raw.analytics_embeddings")

# COMMAND ----------

# MAGIC %pip install -U langchain langchain-community databricks-vectorsearch databricks-langchain langchain_openai
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Create Vector Search Index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

client.create_delta_sync_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.analytics_index",
    source_table_name="customer_suppport_agent.raw.analytics_embeddings",
    pipeline_type="TRIGGERED",
    primary_key="session_id",
    embedding_source_column="text",
    embedding_model_endpoint_name="databricks-bge-large-en"
)

# COMMAND ----------

# DBTITLE 1,Create Client And Get Index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

index = client.get_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.analytics_index"
)

# COMMAND ----------

# DBTITLE 1,Sync Index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

index = client.get_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.analytics_index"
)

index.sync()

# COMMAND ----------

# DBTITLE 1,Use OpenAI via Lanchain for retrieval and invoking
from databricks_langchain import DatabricksVectorSearch
from langchain_openai import ChatOpenAI

# Retriever
vectorstore = DatabricksVectorSearch(
    index_name="customer_suppport_agent.raw.analytics_index",
    endpoint="vs_endpoint"
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key="xxxxxxxxxxxxxxxxxxxxxxx"
)

# Query
query = "Give me summary of user analytics for C101"

docs = retriever.invoke(query)
context = "\n".join([doc.page_content for doc in docs])

response = llm.invoke(f"""
Answer based on context:
{context}

Question: {query}
""")

print(response)