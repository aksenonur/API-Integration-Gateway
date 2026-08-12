import requests
import sqlite3
import csv
import logging
import time
from datetime import datetime
from requests.exceptions import RequestException

logging.basicConfig(
    filename='etl_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

API_URL = "https://jsonplaceholder.typicode.com/posts"
DB_NAME = "enterprise_data.db"

def init_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                processed_at TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

def extract_data_with_retry(url, retries=3, backoff_factor=2):
    for attempt in range(retries):
        try:
            logging.info(f"Attempting to fetch data from {url} (Attempt {attempt + 1}/{retries})")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logging.warning(f"Request failed: {e}. Retrying in {backoff_factor ** attempt} seconds...")
            time.sleep(backoff_factor ** attempt)
    logging.critical("All extraction retries failed. Pipeline aborted.")
    raise ConnectionError("Failed to fetch data from external API after multiple attempts.")

def transform_data(raw_data):
    transformed = []
    current_time = datetime.utcnow().isoformat()
    for item in raw_data:
        if not item.get('title') or not item.get('body'):
            logging.warning(f"Skipping malformed record ID: {item.get('id')}")
            continue
        cleaned_item = {
            'id': item.get('id'),
            'user_id': item.get('userId'),
            'title': item.get('title').strip().title(),
            'body': item.get('body').strip(),
            'processed_at': current_time
        }
        transformed.append(cleaned_item)
    logging.info(f"Successfully transformed {len(transformed)} records out of {len(raw_data)} raw records.")
    return transformed

def load_data_to_db(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        query = '''
            INSERT OR REPLACE INTO posts (id, user_id, title, body, processed_at)
            VALUES (:id, :user_id, :title, :body, :processed_at)
        '''
        cursor.executemany(query, data)
        conn.commit()
        logging.info(f"Successfully loaded {len(data)} records into database '{DB_NAME}'.")
    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Transaction rolled back due to database error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    logging.info("=== ETL Pipeline Execution Started ===")
    try:
        init_database()
        raw_payload = extract_data_with_retry(API_URL)
        clean_payload = transform_data(raw_payload)
        load_data_to_db(clean_payload)
        logging.info("=== ETL Pipeline Execution Completed Successfully ===")
    except Exception as e:
        logging.critical(f"Pipeline crashed with critical error: {e}")
        print(f"Pipeline execution failed. Check 'etl_pipeline.log' for details.")
