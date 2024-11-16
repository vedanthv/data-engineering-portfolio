from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import random
import logging
from kafka import KafkaProducer, KafkaConsumer
import json
from airflow.providers.postgres.hooks.postgres import PostgresHook
from faker import Faker
import time

# Kafka Configuration
KAFKA_TOPIC = "ipl_livescores_topic_v3"
KAFKA_BROKER = "0.0.0.0:9092"

fake = Faker()

# List of real IPL team names
IPL_TEAMS = [
    "Chennai Super Kings",
    "Mumbai Indians",
    "Royal Challengers Bangalore",
    "Kolkata Knight Riders",
    "Sunrisers Hyderabad",
    "Rajasthan Royals",
    "Punjab Kings",
    "Delhi Capitals",
    "Lucknow Super Giants",
    "Gujarat Titans",
]

# List of some known player names (man of the match candidates)
IPL_PLAYERS = [
    "MS Dhoni", "Virat Kohli", "Rohit Sharma", "AB de Villiers", "Chris Gayle",
    "Lasith Malinga", "David Warner", "Jasprit Bumrah", "Ravindra Jadeja",
    "Hardik Pandya", "KL Rahul", "Rishabh Pant", "Kane Williamson", "Steve Smith",
    "Ben Stokes", "Andre Russell", "Pat Cummins", "Rashid Khan", "Yuvraj Singh",
    "Shane Watson", "Sanju Samson", "Shikhar Dhawan", "Dinesh Karthik", "Bhuvneshwar Kumar",
    "Faf du Plessis", "Suresh Raina", "Moeen Ali", "Mohammed Shami", "Sam Curran",
    "Shaheen Afridi", "Mitchell Starc", "Joe Root", "Tim Southee", "Eoin Morgan",
    "Trent Boult", "Quinton de Kock", "Kieron Pollard", "Glenn Maxwell", "Imran Tahir",
    "Adam Zampa", "Kuldeep Yadav", "Ishan Kishan", "Deepak Chahar", "Shubman Gill",
    "Prithvi Shaw", "Axar Patel", "Navdeep Saini", "Marcus Stoinis", "Nicholas Pooran"
]

IPL_VENUES = [
    "Wankhede Stadium, Mumbai",
    "M. Chinnaswamy Stadium, Bengaluru",
    "Eden Gardens, Kolkata",
    "Arun Jaitley Stadium, Delhi",
    "MA Chidambaram Stadium, Chennai",
    "Narendra Modi Stadium, Ahmedabad",
    "Rajiv Gandhi International Cricket Stadium, Hyderabad",
    "Sawai Mansingh Stadium, Jaipur",
    "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow",
]

# Generate a match record with 25 different columns
def generate_fake_ipl_data():

    venue = random.sample(IPL_VENUES,1)
    team1, team2 = random.sample(IPL_TEAMS, 2)  # Pick two distinct teams
    match_date = fake.date_this_year()  # Match date

    return {
        "match_id": f"{random.randint(1000, 9999)}{int(time.time() * 1000)}",  # Unique match ID
        "league_name": "Indian Premier League",
        "season": random.choice([2020, 2021, 2022, 2023, 2024]),
        "team1": team1,
        "team2": team2,
        "venue": venue,
        "match_date": match_date.strftime("%Y-%m-%d"),  # Convert to string
        "start_time": fake.time(),
        "match_status": random.choice(["Completed", "In Progress", "Scheduled"]),
        "score1": random.randint(120, 240),
        "score2": random.randint(120, 240),
        "wickets1": random.randint(0, 10),
        "wickets2": random.randint(0, 10),
        "runs1": random.randint(100, 200),
        "runs2": random.randint(100, 200),
        "overs1": round(random.uniform(10, 20), 1),
        "overs2": round(random.uniform(10, 20), 1),
        "man_of_the_match": random.choice(IPL_PLAYERS),
        "umpire1": fake.name(),
        "umpire2": fake.name(),
        "match_type": "T20",
        "toss_winner": random.choice([team1, team2]),
        "batting_first": random.choice([team1, team2]),
        "total_runs": random.randint(150, 350),
        "extra_runs": random.randint(5, 25),
        "target_runs": random.randint(150, 350),
        "match_duration": random.randint(120, 240),
        "winning_team": random.choice([team1, team2, "Tie"])
    }
# Publish data to Kafka
def publish_to_kafka(data):
    if not data:
        logging.info("No data to publish to Kafka.")
        return
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        for record in data:
            logging.info(f"Publishing record to Kafka: {record}")
            producer.send(KAFKA_TOPIC, record)
        producer.flush()
        producer.close()
    except Exception as e:
        logging.error(f"Error publishing to Kafka: {e}")

# Consume from Kafka and store in Postgres
def consume_from_kafka():
    MAX_MESSAGES = 100  # Number of messages to consume
    consumed_count = 0  # Counter for consumed messages

    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",  # Adjust as needed (earliest or latest)
            enable_auto_commit=True,       # Commit offsets after consuming
            group_id="ipl_consumer_group"  # Consistent consumer group
        )

        logging.info("Starting to consume messages from Kafka...")
        for message in consumer:
            record = message.value
            logging.info(f"Consumed record: {record}")

            # Process the record (e.g., insert into Postgres)
            insert_into_postgres(record)

            consumed_count += 1
            if consumed_count >= MAX_MESSAGES:
                logging.info(f"Consumed {MAX_MESSAGES} messages. Stopping consumer.")
                break  # Exit the loop after consuming MAX_MESSAGES

        consumer.close()  # Close the consumer properly
        logging.info("Kafka consumer task completed successfully.")

    except Exception as e:
        logging.error(f"Error consuming messages from Kafka: {e}")
        raise

# Insert data into Postgres
def insert_into_postgres(record):
    try:
        postgres_hook = PostgresHook(postgres_conn_id="cricket_postgres_conn")
        insert_query = """
        INSERT INTO ipl_livescores (
            match_id, league_name, season, team1, team2, venue, match_date, start_time, match_status,
            score1, score2, wickets1, wickets2, runs1, runs2, overs1, overs2, man_of_the_match,
            umpire1, umpire2, match_type, toss_winner, batting_first, total_runs, extra_runs,
            target_runs, match_duration, winning_team
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s);
        """
        parameters = (
            record["match_id"],
            record["league_name"],
            record["season"],
            record["team1"],
            record["team2"],
            record["venue"],
            record["match_date"],
            record["start_time"],
            record["match_status"],
            record["score1"],
            record["score2"],
            record["wickets1"],
            record["wickets2"],
            record["runs1"],
            record["runs2"],
            record["overs1"],
            record["overs2"],
            record["man_of_the_match"],
            record["umpire1"],
            record["umpire2"],
            record["match_type"],
            record["toss_winner"],
            record["batting_first"],
            record["total_runs"],
            record["extra_runs"],
            record["target_runs"],
            record["match_duration"],
            record["winning_team"],
        )
        postgres_hook.run(insert_query, parameters=parameters)
        logging.info(f"Inserted record into Postgres: {parameters}")

    except Exception as e:
        logging.error(f"Error inserting into Postgres: {e}")

# Default DAG Arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define DAG
with DAG(
    "ipl_livescores_pipeline",
    default_args=default_args,
    description="Generate dummy IPL live scores and store them in Postgres",
    schedule_interval=timedelta(minutes=1),  # Run every 5 minutes
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Create the "ipl_livescores" table if it doesn't exist
    create_table_task = PostgresOperator(
        task_id="create_ipl_livescores_table",
        postgres_conn_id="cricket_postgres_conn",
        sql="""
        CREATE TABLE IF NOT EXISTS ipl_livescores (
            match_id TEXT ,
            league_name TEXT,
            season INT,
            team1 TEXT,
            team2 TEXT,
            venue TEXT,
            match_date TEXT,
            start_time TEXT,
            match_status TEXT,
            score1 INT,
            score2 INT,
            wickets1 INT,
            wickets2 INT,
            runs1 INT,
            runs2 INT,
            overs1 FLOAT,
            overs2 FLOAT,
            man_of_the_match TEXT,
            umpire1 TEXT,
            umpire2 TEXT,
            match_type TEXT,
            toss_winner TEXT,
            batting_first TEXT,
            total_runs INT,
            extra_runs INT,
            target_runs INT,
            match_duration INT,
            winning_team TEXT
        );
        """,
    )

    # Generate fake IPL match data
    generate_ipl_data_task = PythonOperator(
        task_id="generate_ipl_data",
        python_callable=lambda: publish_to_kafka([generate_fake_ipl_data() for _ in range(100)]),  # Generate 100 records
    )

    # Consume from Kafka and insert into Postgres
    consume_from_kafka_task = PythonOperator(
        task_id="consume_from_kafka",
        python_callable=consume_from_kafka,
    )

    # Set task dependencies
    create_table_task >> generate_ipl_data_task >> consume_from_kafka_task
