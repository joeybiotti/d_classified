import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': 'STG_MARTS',
}

OUTPUT_DIR = Path(__file__).parent.parent / 'assets'
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_category_data() -> pd.DataFrame:
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    try:
        query = 'SELECT * FROM  agg_postings_by_category'
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def plot_postings_by_category(df: pd.DataFrame):
    _, ax = plt.subplots(figsize=(10, 6))

    df_sorted = df.sort_values('POSTING_COUNT', ascending=True)
    ax.barh(df_sorted['CATEGORY'], df_sorted['POSTING_COUNT'], color='#2E86AB')

    ax.set_xlabel('Number of Postins')
    ax.set_title('Job Postings by Category', fontsize=14, fontweight='bold')
    ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'postings_by_category.png'
    plt.savefig(output_path, dpi=150)
    print(f'Saved chart to {output_path}')


if __name__ == '__main__':
    df = fetch_category_data()
    plot_postings_by_category(df)
