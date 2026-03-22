# Databricks notebook source
# DBTITLE 1,Imports
# MAGIC %pip install -U langchain langchain-community databricks-vectorsearch databricks-langchain langchain_openai
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Create Custom Text Column
from pyspark.sql.functions import concat, lit, to_json, struct, when

df = spark.table("customer_suppport_agent.raw.orders")

df = df.withColumn(
    "text",
    concat(
        lit("Order "),
        df.order_id,
        lit(" placed by customer "),
        df.customer_id,
        lit(" for product "),
        df.product_id,
        lit(". Order amount is "),
        df.order_amount,
        lit(" "),
        df.currency,
        lit(" with quantity "),
        df.quantity,
        lit(". Order status is "),
        df.order_status,
        lit(" and payment status is "),
        df.payment_status,
        lit(" using "),
        df.payment_method,
        lit(". Shipping to "),
        df.city,
        lit(", "),
        df.region,
        lit(", pincode "),
        df.pincode,
        lit(". Order date "),
        df.order_date,
        lit(" and delivery date "),
        df.delivery_date,
        lit(". Fulfilled by "),
        df.delivery_partner,
        lit(" via "),
        df.fulfillment_type,
        lit(". Ordered via "),
        df.order_channel,
        lit(" using "),
        df.device_type,
        lit(" on "),
        df.browser,
        lit("."),

        # Derived signals
        lit(" This is "),
        when(df.order_amount > 500, lit("a high value order.")).otherwise(lit("a regular order.")),

        lit(" Discount applied is "),
        df.discount,
        lit(" and tax is "),
        df.tax,
        lit(". Shipping cost is "),
        df.shipping_cost,
        lit("."),

        when(df.is_gift == True, concat(lit(" This is a gift order with message: "), df.gift_message)).otherwise(lit("")),

        when(df.coupon_code.isNotNull(), concat(lit(" Coupon used: "), df.coupon_code)).otherwise(lit("")),

        when(df.loyalty_points_used > 0, concat(lit(" Loyalty points used: "), df.loyalty_points_used)).otherwise(lit("")),

        lit(" Structured data: "),
        to_json(struct(
            "order_id",
            "customer_id",
            "product_id",
            "order_status",
            "order_amount",
            "currency",
            "payment_status",
            "city",
            "region",
            "order_date"
        ))
    )
)

# Metadata for filtering
df = df.withColumn(
    "metadata",
    struct(
        "customer_id",
        "order_status",
        "payment_status",
        "city",
        "region"
    )
)

df = df.limit(1000)

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.sql.functions import col

window = Window.orderBy("order_id")

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
    batch_df.select("order_id", "text", "embedding") \
        .write \
        .format("delta") \
        .mode("append") \
        .option("mergeSchema", "true").saveAsTable("customer_suppport_agent.raw.order_embeddings")

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(*) from customer_suppport_agent.raw.order_embeddings

# COMMAND ----------

# DBTITLE 1,Set CDF
# MAGIC %sql
# MAGIC ALTER TABLE customer_suppport_agent.raw.orders
# MAGIC SET TBLPROPERTIES (delta.enableChangeDataFeed = true)

# COMMAND ----------

# MAGIC %sql
# MAGIC OPTIMIZE customer_suppport_agent.raw.order_embeddings;

# COMMAND ----------

# DBTITLE 1,Create Vector Search Index
client.create_delta_sync_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.orders_index",
    source_table_name="customer_suppport_agent.raw.order_embeddings",
    pipeline_type="TRIGGERED",
    primary_key="order_id",
    embedding_source_column="text",
    embedding_model_endpoint_name="databricks-bge-large-en"
)

# COMMAND ----------

# DBTITLE 1,Create Client And Get Index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

index = client.get_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.orders_index"
)

# COMMAND ----------

# DBTITLE 1,Sync Index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

index = client.get_index(
    endpoint_name="vs_endpoint",
    index_name="customer_suppport_agent.raw.orders_index"
)

index.sync()

# COMMAND ----------

# DBTITLE 1,Use OpenAI via Lanchain for retrieval and invoking
from databricks_langchain import DatabricksVectorSearch
from langchain_openai import ChatOpenAI

# Retriever
vectorstore = DatabricksVectorSearch(
    index_name="customer_suppport_agent.raw.orders_index",
    endpoint="vs_endpoint"
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key="xxxxxxxxxxxxxxx"
)

# Query
query = "Orders fulfiled by Delhivery"

docs = retriever.invoke(query)
context = "\n".join([doc.page_content for doc in docs])

response = llm.invoke(f"""
Answer based on context:
{context}

Question: {query}
""")

print(response)