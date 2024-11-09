from faker import Faker
from kafka import KafkaProducer
import json
import random
import time

# Configuration
KAFKA_TOPIC = 'financial_data_topic'
KAFKA_BOOTSTRAP_SERVERS = ['localhost:29092','localhost:39092']  # Replace with your Kafka server

# Initialize Faker and Kafka producer
fake = Faker()
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to generate mock financial data
def generate_financial_data():
    return {
        "transaction_id": fake.uuid4(),
        "transaction_date": fake.date_time_this_year().isoformat(),
        "account_id": fake.uuid4(),
        "transaction_type": random.choice(["deposit", "withdrawal", "transfer", "payment"]),
        "amount": round(random.uniform(100, 5000), 2),
        "currency": random.choice(["USD", "EUR", "GBP", "JPY", "CAD"]),
        "location": fake.city(),
        "merchant": fake.company(),
        "category": random.choice(["utilities", "groceries", "travel", "entertainment", "healthcare"])
    }

# Function to send data to Kafka
def send_financial_data_to_kafka():
    while True:
        financial_data = generate_financial_data()
        producer.send(KAFKA_TOPIC, value=financial_data)
        print(f"Sent: {financial_data}")
        time.sleep(1)  # Send a message every second (adjust as needed)

# Run the function
send_financial_data_to_kafka()
