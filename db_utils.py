import os
import psycopg2
from dotenv import load_dotenv
import json
import requests

### Environment Variables ###
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

### Main upsert function for Bullz table ###
def upsert_bullz_row(data):
    url = f"{SUPABASE_URL}/rest/v1/bulls"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # First try to update existing record
    update_url = f"{url}?name=eq.{data['name']}"
    response = requests.patch(update_url, headers=headers, json=data)
    
    # If no rows were updated (response is empty), then insert
    if not response.content.strip():
        response = requests.post(url, headers=headers, json=data)
    
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