"""
fetch_data.py
Downloads all tables from the Neon PostgreSQL database and saves them as CSVs
in analysis_script/data/.

Usage:
    python analysis_script/fetch_data.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("ERROR: DATABASE_URL not found in .env")

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TABLES = [
    "sessions",
    "session_mode_events",
    "messages",
    "hallucinated_facts",
    "hallucination_guesses",
    "claims",
    "predictions",
    "prediction_scores",
    "interaction_events",
]


def fetch_all():
    print(f"Connecting to Neon...")
    conn = psycopg2.connect(DATABASE_URL)

    for table in TABLES:
        try:
            df = pd.read_sql(f"SELECT * FROM {table} ORDER BY 1", conn)
            out = DATA_DIR / f"{table}.csv"
            df.to_csv(out, index=False)
            print(f"  {table:<30} {len(df):>5} rows  →  {out.name}")
        except Exception as e:
            print(f"  {table:<30} ERROR: {e}")

    conn.close()
    print("\nDone. CSVs saved to analysis_script/data/")


if __name__ == "__main__":
    fetch_all()
