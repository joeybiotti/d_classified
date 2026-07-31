import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('ADZUNA_APP_ID')
API_KEY = os.getenv('ADZUNA_APP_KEY')

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'd_classified.duckdb'

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

    loaded_at = datetime.now(timezone.utc)
    all_postings = []

    for term in SEARCH_TERMS:
        print(f'Fetching postings for {term}')
        results = fetch_postings(term)
        print(f'  {len(results)} results')
        all_postings.extend(results)

    df = flatten(all_postings, loaded_at)
    print(f'Total postings this run: {len(df)}')

    with duckdb.connect(str(DB_PATH)) as conn:
        conn.execute('CREATE SCHEMA IF NOT EXISTS raw;')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw.postings AS
            SELECT * FROM df LIMIT 0
        """)
        conn.execute('INSERT INTO raw.postings SELECT * FROM df')

        total_rows = conn.execute('SELECT count(*) FROM raw.postings').fetchone()[0]
        print(f'Success. raw.postings now has {total_rows} total rows across all runs.')


if __name__ == '__main__':
    run_ingest()