import json
import base64
import boto3

eventbridge = boto3.client("events")

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            payload = base64.b64decode(record['kinesis']['data'])
            order = json.loads(payload)

            print("Received:", order)

            response = eventbridge.put_events(
                Entries=[
                    {
                        "Source": "app.orders",
                        "DetailType": "OrderCreated",
                        "Detail": json.dumps(order),
                        "EventBusName": "default"
                    }
                ]
            )

            # Log full response
            print("EventBridge response:", json.dumps(response))

            # Check for failures explicitly
            if response.get("FailedEntryCount", 0) > 0:
                print("Failed entries detected:", response["Entries"])

        except Exception as e:
            print("Error processing record:", str(e))
            raise e