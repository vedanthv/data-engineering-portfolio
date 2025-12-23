from faker import Faker
import random, uuid
import pandas as pd
from datetime import datetime,date

fake = Faker()

OUTPUT_PATH = "/Volumes/insurance/bronze/insurance_vol/raw/claims"

try:
    dbutils.fs.mkdirs(OUTPUT_PATH)
except:
    pass

NUM_RECORDS = 10_000
BATCH_SIZE = 10000

def generate_claim_batch(n):
    rows = []
    for _ in range(n):
        rows.append({
            "claim_id": str(uuid.uuid4()),
            "policy_id": str(uuid.uuid4()),
            "claim_amount": round(random.uniform(1000, 20000), 2),
            "claim_status": random.choice(["REPORTED", "OPEN", "SETTLED", "CLOSED"]),
            "loss_date": fake.date_between(start_date="-2y", end_date="today")
        })
    return pd.DataFrame(rows)

business_date = date.today().strftime("%Y%m%d")

for batch_num, i in enumerate(range(0, NUM_RECORDS, BATCH_SIZE), start=1):
    timestamp_hhmm = datetime.now().strftime("%H%M")
    df = generate_claim_batch(BATCH_SIZE)
    file_path = (
        f"{OUTPUT_PATH}/policies_{business_date}_{timestamp_hhmm}_b{batch_num}.csv"
    )
    df.to_csv(file_path, index=False)


print("Claims CSV generation complete")
