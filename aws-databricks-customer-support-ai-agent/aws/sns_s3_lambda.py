import json
import boto3
import pandas as pd
import uuid
from datetime import datetime
from io import BytesIO

s3 = boto3.client('s3')

BUCKET_NAME = "customer-support-ai"

def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    records = event.get('Records', [])
    batch = []

    for record in records:
        try:
            raw_body = record.get('body', '')

            print("RAW BODY:", raw_body)

            if not raw_body or raw_body.strip() == "":
                continue

            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                print("Not JSON, skipping")
                continue

            # Case 1: SNS -> SQS
            if 'Message' in body:
                try:
                    eventbridge_event = json.loads(body['Message'])
                except:
                    print("Invalid SNS Message")
                    continue

            # Case 2: Direct EventBridge (rare)
            elif 'detail' in body:
                eventbridge_event = body

            # Case 3: Already business data
            else:
                batch.append(body)
                continue

            # Extract detail
            detail = eventbridge_event.get('detail')
            if not detail:
                print("No detail field")
                continue

            batch.append(detail)

        except Exception as e:
            print(f"Error: {e}")
            continue

    if not batch:
        print("No valid records to process")
        return {"status": "no data"}

        # Convert to DataFrame
    df = pd.json_normalize(batch)

    if df.empty:
        print("Empty DataFrame")
        return {"status": "no data"}

    # Add partitions
    now = datetime.utcnow()
    year = now.year
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"

    df['year'] = year
    df['month'] = int(month)
    df['day'] = int(day)

    # S3 path
    s3_prefix = f"orders/year={year}/month={month}/day={day}/"

    # Chunking logic
    BATCH_SIZE = 100
    total_records = len(df)

    print(f"Total records: {total_records}")

    files_written = 0

    for i in range(0, total_records, BATCH_SIZE):
        chunk_df = df.iloc[i:i+BATCH_SIZE]

        buffer = BytesIO()
        chunk_df.to_parquet(buffer, index=False, compression='snappy')

        file_size_mb = len(buffer.getvalue()) / (1024 * 1024)

        file_name = f"{s3_prefix}batch_{uuid.uuid4()}.parquet"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=buffer.getvalue()
        )

        print(f"Written chunk {i//BATCH_SIZE + 1} | Records: {len(chunk_df)} | Size: {file_size_mb:.2f} MB")

        files_written += 1

        return {
            "status": "success",
            "total_records": total_records,
            "files_written": files_written
        }