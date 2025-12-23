# MAGIC %run "/Workspace/Users/vedanthbaliga21@gmail.com/Insurance-Operations-Intelligence-Lakehouse/data-ingestion/02_Data_Ingestion/01_autoloader_base"

# COMMAND ----------

VOLUME_BASE = "/Volumes/insurance/bronze/insurance_vol"

run_autoloader(
    spark,
    source_path=f"{VOLUME_BASE}/raw/policies",
    volume_base_path=VOLUME_BASE,
    dataset_name="policy",
    target_table="insurance.bronze.policy_bronze"
)

# COMMAND ----------

VOLUME_BASE = "/Volumes/insurance/bronze/insurance_vol"

run_autoloader(
    spark,
    source_path=f"{VOLUME_BASE}/raw/claims",
    volume_base_path=VOLUME_BASE,
    dataset_name="claims",
    target_table="insurance.bronze.claims_bronze"
)

# COMMAND ----------

VOLUME_BASE = "/Volumes/insurance/bronze/insurance_vol"

run_autoloader(
    spark,
    source_path=f"{VOLUME_BASE}/raw/billing",
    volume_base_path=VOLUME_BASE,
    dataset_name="billing",
    target_table="insurance.bronze.billing_bronze"
)