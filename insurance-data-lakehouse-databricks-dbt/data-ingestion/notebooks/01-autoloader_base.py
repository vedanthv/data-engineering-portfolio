from pyspark.sql.functions import current_timestamp

def run_autoloader(
    spark,
    source_path: str,
    volume_base_path: str,
    dataset_name: str,
    target_table: str
):
    checkpoint_path = f"{volume_base_path}/checkpoints/{dataset_name}"
    schema_location = f"{volume_base_path}/schemas/{dataset_name}"

    (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", schema_location)
        .load(source_path)
        .writeStream
        .trigger(availableNow=True)
        .option("checkpointLocation", checkpoint_path)
        .toTable(target_table)
    )
