import os
import psycopg2
from dotenv import load_dotenv
import json
import requests

### Environment Variables ###
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

### Main Database Insertion Function ###
def insert_bull_data(data):
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_DB_HOST"),
        dbname=os.getenv("SUPABASE_DB_NAME"),
        user=os.getenv("SUPABASE_DB_USER"),
        password=os.getenv("SUPABASE_DB_PASSWORD"),
        port=os.getenv("SUPABASE_DB_PORT", 5432)
    )
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO bulls (bull_name, ntm, yield, data_json)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data.get("bull_names", [""])[0],  # first bull name
            data.get("NTM", ""),
            data.get("yield", ""),
            json.dumps(data)  # store the whole data as JSON for reference
        )
    )
    conn.commit()
    cur.close()
    conn.close()

def upsert_bullz_row(data):
    url = f"{SUPABASE_URL}/rest/v1/Bullz"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    # Supabase expects a list of dicts for upsert
    response = requests.post(url, headers=headers, json=[data])
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except Exception:
        print("Response content:", response.content)
    return response

# Example usage:
if __name__ == "__main__":
    data = {
        "name": "Test Bull",
        "ntm": "7",
        # Add any other columns you want to set/update
    }
    upsert_bullz_row(data)


