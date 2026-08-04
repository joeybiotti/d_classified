import os
from datetime import datetime, timezone

import pandas as pd
import requests
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

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
    url = f'https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1'
    params = {
        'app_id': API_ID,
        'app_key': API_KEY,
        'results_per_page': RESULTS_PER_PAGE,
        'what': what,
        'content-type': 'application/json',
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get('results', [])


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
        print('Error: ADZUNA_APP_ID / ADZUNA_APP_KEY not set in .env')
        return

    loaded_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    all_postings = []

    for term in SEARCH_TERMS:
        print(f'Fetching postings for {term}')
        results = fetch_postings(term)
        print(f'  {len(results)} results')
        all_postings.extend(results)

    df = flatten(all_postings, loaded_at)
    print(f'Total postings this run: {len(df)}')

    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
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
        from snowflake.connector.pandas_tools import write_pandas

        df.columns = df.columns.str.upper()
        _, _, nrows, _ = write_pandas(conn, df, 'POSTINGS')
        print(f'Success. Inserted {nrows} rows this time')

        cursor.execute('SELECT count(*) FROM postings')
        total_rows = cursor.fetchone()[0]
        print(f'posting table now has {total_rows} total rows across all runs.')
    finally:
        conn.close()


if __name__ == '__main__':
    run_ingest()
