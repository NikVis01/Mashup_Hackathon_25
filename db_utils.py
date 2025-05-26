import os
import psycopg2
from dotenv import load_dotenv
import json
import requests

### Environment Variables ###
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

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


