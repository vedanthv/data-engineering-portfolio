import os
import time
import clickhouse_connect
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
CLICKHOUSE_DB = "default"
POSTGRES_DB = "cricket"
POSTGRES_USER = "debezium"
POSTGRES_PASSWORD = "dbz"

print(CLICKHOUSE_HOST)
print(POSTGRES_HOST)

TABLE = "fixtures_with_team_names_mv"

def fetch_clickhouse_data():
    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=8123,
            username="new_admin_user",
            password="blah"
        )
        result = client.query(f"SELECT * FROM {TABLE}")
        print(f"Fetched {len(result.result_rows)} rows from ClickHouse")
        return result.result_rows, result.column_names
    except Exception as e:
        print(f"Error connecting to ClickHouse: {e}")
        return [], []

def upsert_postgres(data, columns):
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=5432
        )
        cur = conn.cursor()
        cols = ','.join(columns)
        placeholders = ','.join([f"%s"] * len(columns))
        updates = ','.join([f"{col}=EXCLUDED.{col}" for col in columns if col != 'id'])

        upsert_query = f"""
        INSERT INTO {TABLE} ({cols}) VALUES %s
        ON CONFLICT (id) DO UPDATE SET {updates};
        """

        execute_values(cur, upsert_query, data)
        conn.commit()
        print(f"Upserted {len(data)} rows to Postgres.")
    except Exception as e:
        print(f"Error upserting to Postgres: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    while True:
        data, columns = fetch_clickhouse_data()
        if data:
            upsert_postgres(data, columns)
        else:
            print("No data fetched from ClickHouse.")
        time.sleep(600)
