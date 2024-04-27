import boto3
import json
import pandas as pd
# import json

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
   
    
    target_bucket = 'YOUR_BUCKET'
    copy_source = {'Bucket': source_bucket, 'Key': object_key}
    
    target_file_name = object_key[:-5]
    print(target_file_name)
    
    waiter = s3_client.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=object_key)
    
    response = s3_client.get_object(Bucket=source_bucket, Key=object_key)
    print(response)
    data = response['Body']
    print(data)
    data = response['Body'].read().decode('utf-8')
    print(data)
    data = json.loads(data)
    print(data)
    
    f = []
    for i in data:
        f.append(i)
    df = pd.DataFrame(f)
    # Select specific columns
    print(df)
    
    # Convert DataFrame to CSV format
    csv_data = df.to_csv(index=True)
    
    # Upload CSV to S3
    bucket_name = target_bucket
    object_key = f"{target_file_name}.csv"
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_data)
    
    return {
        'statusCode': 200,
        'body': json.dumps('CSV conversion and S3 upload completed successfully')
    }
