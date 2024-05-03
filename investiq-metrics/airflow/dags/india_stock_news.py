from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import time
from io import StringIO

def extract_headlines():
    # Configure Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")  # Disable sandbox mode
    chrome_options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage
    chrome_options.add_argument('--remote-debugging-pipe')

    ticker_list = ["INFY","SBIN","JIOFIN"]

    for ticker in ticker_list:
        driver = webdriver.Chrome()
        driver.get(f"https://finance.yahoo.com/quote/{ticker}.NS/news")
        time.sleep(5)  # Allow time for the page to load
        num_scrolls = 50  # Number of times to scroll
        for _ in range(num_scrolls):
                last_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Adjust sleep time as needed
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
            
        # Extract headlines
        headlines = driver.find_elements(By.XPATH, "//h3")
        extracted_headlines = []
        for headline in headlines:
            if ticker in headline.text:
                extracted_headlines.append(headline.text)
        driver.quit()
            
        # Create DataFrame
        df = pd.DataFrame({'ticker': [{ticker}] * len(extracted_headlines), 'title': extracted_headlines})

        abc =StringIO()
            
        # Export DataFrame to CSV
        df.to_csv(abc, header=True)
        abc.seek(0)
        s3_client.put_object(Bucket='india-stock-news-nse', Body=abc.getvalue() ,Key=f'{ticker}-news-01052024.csv') #key is the csv file name that will be created

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG('yahoo_finance_headlines_extraction', default_args=default_args, schedule_interval='@daily')

extract_task = PythonOperator(
    task_id='extract_headlines_task',
    python_callable=extract_headlines,
    dag=dag,
)

extract_task
