from faker import Faker
import random
import uuid
from datetime import date, timedelta,datetime
import pandas as pd

fake = Faker()

OUTPUT_PATH = "/Volumes/insurance/bronze/insurance_vol/raw/policies"

try:
    dbutils.fs.mkdirs(OUTPUT_PATH)
except:
    pass

NUM_RECORDS = 10_000
BATCH_SIZE = 10000

def generate_policy_batch(n):
    rows = []
    for _ in range(n):
        start = fake.date_between(start_date="-3y", end_date="today")
        end = start + timedelta(days=365)

        rows.append({
            "policy_id": str(uuid.uuid4()),
            "customer_name": fake.name(),
            "product": random.choice(["AUTO", "HOME", "HEALTH"]),
            "premium_amount": round(random.uniform(500, 5000), 2),
            "policy_start_date": start,
            "policy_end_date": end
        })
    return pd.DataFrame(rows)

business_date = date.today().strftime("%Y%m%d")

for batch_num, i in enumerate(range(0, NUM_RECORDS, BATCH_SIZE), start=1):
    timestamp_hhmm = datetime.now().strftime("%H%M")
    df = generate_policy_batch(BATCH_SIZE)
    file_path = (
        f"{OUTPUT_PATH}/policies_{business_date}_{timestamp_hhmm}_b{batch_num}.csv"
    )
    df.to_csv(file_path, index=False)

print("Policy CSV generation complete")
