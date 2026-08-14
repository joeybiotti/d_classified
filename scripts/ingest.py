import logging
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('d_classified.log'), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

API_ID = os.getenv('ADZUNA_APP_ID')
API_KEY = os.getenv('ADZUNA_APP_KEY')

SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA'),
}

COUNTRY = 'us'
SEARCH_TERMS = ['analytics engineer', 'data engineer', 'sql developer']
RESULTS_PER_PAGE = 50


def fetch_postings(what: str) -> list[dict]:
    all_results = []
    page = 1

    while True:
        url = f'https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}'
        params = {
            'app_id': API_ID,
            'app_key': API_KEY,
            'results_per_page': RESULTS_PER_PAGE,
            'what': what,
            'content-type': 'application/json',
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f'Timed out fetching postings for "{what}" page {page}.')
            break
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed for "{what}" page {page}: {e}')
            break

        try:
            data = response.json()
            results = data.get('results', [])
            all_results.extend(results)

            pagecount = data.get('pagecount', 1)
            if page >= pagecount:
                break
            page += 1
        except ValueError:
            logger.error(f'Could not parse JSON response for "{what}" page {page}')
            break

    return all_results


def flatten(postings: list[dict], loaded_at: datetime) -> pd.DataFrame:
    rows = []
    for p in postings:
        rows.append(
            {
                'posting_id': p.get('id'),
                'title': p.get('title'),
                'company': p.get('company', {}).get('display_name'),
                'location': p.get('location', {}).get('display_name'),
                'salary_min': p.get('salary_min'),
                'salary_max': p.get('salary_max'),
                'description': p.get('description'),
                'created': p.get('created'),
                'category': p.get('category', {}).get('label'),
                'redirect_url': p.get('redirect_url'),
                'loaded_at': loaded_at,
            }
        )
    return pd.DataFrame(rows)


def run_ingest():
    if not API_ID or not API_KEY:
        logger.error('Error: ADZUNA_APP_ID / ADZUNA_APP_KEY not set in .env')
        return

    missing_sf_config = [k for k, v in SNOWFLAKE_CONFIG.items() if not v]
    if missing_sf_config:
        logger.error(f'Missing Snowflake config values: {missing_sf_config}')
        return

    loaded_at = datetime.now(timezone.utc)
    all_postings = []

    for term in SEARCH_TERMS:
        logger.info(f'Fetching postings for {term}')
        results = fetch_postings(term)
        logger.info(f'  {len(results)} results')
        all_postings.extend(results)
        time.sleep(1)

    if not all_postings:
        logger.warning('No postings fetched this run across all search terms. Skipping write.')
        return

    df = flatten(all_postings, loaded_at)
    df.columns = df.columns.str.upper()
    logger.info(f'Total postings this run: {len(df)}')

    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    except snowflake.connector.errors.Error as e:
        logger.error(f'Failed to connect to Snowflake: {e}')
        return

    try:
        cursor = conn.cursor()
        cursor.execute('USE DATABASE D_CLASSIFIED')
        cursor.execute('USE SCHEMA RAW')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                posting_id STRING,
                title STRING,
                company STRING,
                location STRING,
                salary_min FLOAT,
                salary_max FLOAT,
                description STRING,
                created STRING,
                category STRING,
                redirect_url STRING,
                loaded_at TIMESTAMP_NTZ
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postings_staging (
                posting_id STRING,
                title STRING,
                company STRING,
                location STRING,
                salary_min FLOAT,
                salary_max FLOAT,
                description STRING,
                created STRING,
                category STRING,
                redirect_url STRING,
                loaded_at TIMESTAMP_NTZ
            )
        """)

        _, _, nrows, _ = write_pandas(conn, df, 'POSTINGS_STAGING', use_logical_type=True)
        logger.info(f'Success. Inserted {nrows} rows to staging')

        cursor.execute("""
            MERGE INTO postings t
            USING postings_staging s
            ON t.posting_id = s.posting_id
            WHEN NOT MATCHED THEN 
            INSERT (posting_id, title, company, location, salary_min, salary_max, description, created, category, redirect_url, loaded_at)
            VALUES (s.posting_id, s.title, s.company, s.location, s.salary_min, s.salary_max, s.description, s.created, s.category, s.redirect_url, s.loaded_at)
        """)
        logger.info('Merged staging into postings')

        cursor.execute('TRUNCATE TABLE postings_staging')

        cursor.execute('SELECT count(*) FROM postings')
        total_rows = cursor.fetchone()[0]
        logger.info(f'posting table now has {total_rows} total rows across all runs.')
    except snowflake.connector.errors.Error as e:
        logger.error(f'Snowflake write failed: {e}')
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        run_ingest()
    except Exception as e:
        logger.critical(f'Unhandled error: {e}', exc_info=True)
        sys.exit(1)
