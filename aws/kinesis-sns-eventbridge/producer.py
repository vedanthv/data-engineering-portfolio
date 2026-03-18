import json
import boto3
import uuid
import time
import random

kinesis = boto3.client("kinesis", region_name="us-east-1")

STREAM_NAME = "orders-stream"

def generate_order():
    return {
        "order_id": str(uuid.uuid4()),
        "amount": random.randint(100, 1000),
        "customer_email": "test@gmail.com"
    }

while True:
    order = generate_order()

    response = kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(order),
        PartitionKey=order["order_id"]
    )

    print("Sent:", order)

    time.sleep(2)  # wait 2 seconds between messages