from fastapi import FastAPI, BackgroundTasks
from NAVscraper import NAVScraper
from BULscraperOCR import BULScraperOCR
from db_utils import upsert_bullz_row
from pydantic import BaseModel, HttpUrl
import json
import re
import time
from typing import Dict
import traceback
import datetime
import asyncio

import psycopg2  # Ensure psycopg2 is installed for database operations
from psycopg2 import errorcodes, DatabaseError

app = FastAPI(
    title="Bull Scraper API",
    description="An API for scraping bull information from NAV and Bulli websites",
    version="1.0.0"
)

class ScrapeRequest(BaseModel):
    nav_url: HttpUrl = "https://nordic.mloy.fi/NAVBull/BULL/HOLNLDM000671889948/HOL"
    bulli_url: HttpUrl = "https://bulli.vit.de/home/details/528000671889948"

    class Config:
        json_schema_extra = {
            "example": {
                "nav_url": "https://nordic.mloy.fi/NAVBull/BULL/HOLNLDM000671889948/HOL",
                "bulli_url": "https://bulli.vit.de/home/details/528000671889948"
            }
        }

# List of all expected columns (union of both templates)
def get_expected_columns():
    with open("data.json") as f1, open("data2.json") as f2:
        nav_cols = set(json.load(f1).keys())
        bulli_cols = set(json.load(f2).keys())
    return sorted(nav_cols | bulli_cols)

def extract_json_from_response(response):
    # Remove markdown code block if present
    match = re.search(r'```(?:json)?\\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Trying also with just triple backticks (no newline)
    match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()

def create_update_comment(merged_result, expected_cols):
    found_cols = set(merged_result.keys())
    missing_cols = [col for col in expected_cols if col not in found_cols]
    update_comment = ""
    if missing_cols:
        update_comment += "The following columns are missing in the merged result: " + ", ".join(missing_cols) + ". "
    else:
        update_comment += "All expected columns are present in the merged result. "
    null_cols = [col for col in expected_cols if merged_result.get(col) is None]
    if null_cols:
        update_comment += f"Columns {', '.join(null_cols)} contain null values."
    else:
        update_comment += "No columns contain null values."
    return update_comment

### NEED STRUCTURED OUTPUT AND TYPE CHECKING FROM GPT ###

# For NAV scraper
NAV_FIELD_TYPES = {
    "name": str,
    "yield": float,

}

# For BUL scraper
BUL_FIELD_TYPES = {
    "aAa": str,
    "cappa_casain": str,
    "beta_casain": str,
    "fat_percentage": float,
    "protein_percentage": float
    
}

async def scrape_and_store_data(nav_url: str, bulli_url: str):
    print(f"[LOG] Starting scrape_and_store_data for NAV: {nav_url}, Bulli: {bulli_url}")
    # NAV page
    nav_scraper = NAVScraper(template_path="data.json")
    print("[LOG] Fetching NAV HTML...")
    nav_html = nav_scraper.fetch_html(nav_url)
    print("[LOG] Extracting NAV content...")
    nav_content = nav_scraper.extract_content(nav_html)
    print("[LOG] Loading NAV JSON template...")
    nav_json_template = nav_scraper.load_json_template()
    print("[LOG] Asking GPT-4o for NAV data...")
    nav_result = nav_scraper.ask_gpt4o(nav_content, nav_json_template)
    cleaned_nav_result = extract_json_from_response(nav_result)
    print("[DEBUG] Cleaned NAV result:", cleaned_nav_result)
    try:
        print("[LOG] Parsing NAV JSON result...")
        nav_result_dict = json.loads(cleaned_nav_result)
    except Exception as e:
        print("Error parsing NAV JSON:", e)
        traceback.print_exc()
        nav_result_dict = {}
    
    # Bulli page (screenshot + vision)
    bulli_scraper = BULScraperOCR(template_path="data2.json")
    print("[LOG] Sleeping 5 seconds before Bulli scrape...")
    time.sleep(5)
    print("[LOG] Taking Bulli screenshot...")
    screenshot_path = await bulli_scraper.take_screenshot(bulli_url)  # Add await here
    print(f"[LOG] Screenshot saved to {screenshot_path}")
    bulli_json_template = bulli_scraper.load_json_template()
    print("[LOG] Asking GPT-4o with Bulli image...")
    bulli_result = bulli_scraper.ask_gpt4o_with_image(screenshot_path, bulli_json_template)
    print("[DEBUG] Raw Bulli result from OpenAI:", bulli_result)
    cleaned_bulli_result = extract_json_from_response(bulli_result)
    print("[DEBUG] Cleaned Bulli result:", cleaned_bulli_result)
    try:
        print("[LOG] Parsing Bulli JSON result...")
        bulli_result_dict = json.loads(cleaned_bulli_result)
    except Exception as e:
        print("Error parsing Bulli JSON:", e)
        traceback.print_exc()
        bulli_result_dict = {}

    # Changing 'aAa' to 'aaa' due to postgres column name constraints
    if 'aAa' in bulli_result_dict:
        bulli_result_dict['aaa'] = bulli_result_dict.pop('aAa')

    # Changing 'aAa' to 'aaa' due to postgres column name constraints
    if 'BCS_gM' in bulli_result_dict:
        bulli_result_dict['body_condition'] = bulli_result_dict.pop('BCS_gM')

    # MERGING DICTIONARIES
    print("[LOG] Merging NAV and Bulli results...")
    merged_result = {**nav_result_dict, **bulli_result_dict}

    print("[DEBUG] Merged result:", merged_result)

    # Create and append update_comment
    print("[LOG] Creating update_comment...")
    try:
        merged_result["update_comment"] = create_update_comment(merged_result, get_expected_columns())
        print("[LOG] Upserting merged result to Supabase...")
        upsert_bullz_row(merged_result)
        print("[LOG] Upsert complete. Returning merged result.")

    except psycopg2.Error as e:
        print("TypeError detected when upserting:", e)
        error_msg = "Unsuccessful upsert: TypeError"
        error_dict = {"update_message": error_msg}
        upsert_bullz_row(error_dict)
        print("[LOG] Error upserting error message:", e)
    return merged_result

@app.get("/")
async def root():
    return {"message": "Welcome to the Bull Scraper API"}

@app.post("/scrape/", 
    response_model=Dict[str, str],
    summary="Scrape bull information",
    description="""
    Scrapes bull information from both NAV and Bulli websites.
    The scraping process runs in the background and stores the results in the database.
    
    - NAV website provides general bull information and traits
    - Bulli website provides additional details and images
    """)
async def scrape_data(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    # Add the scraping task to background tasks with a delay to allow batching
    # Sleep for 2 seconds to allow other requests to come in before processing starts
    async def delayed_scrape():
        await asyncio.sleep(2)
        await scrape_and_store_data(str(request.nav_url), str(request.bulli_url))
    
    background_tasks.add_task(delayed_scrape)
    
    return {
        "message": "Scraping task has been started",
        "nav_url": str(request.nav_url),
        "bulli_url": str(request.bulli_url)
    }

@app.get("/status")
async def get_status():
    # You might want to add some status checking logic here
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    
    workers = multiprocessing.cpu_count() - 1
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=workers,
        limit_concurrency=100,  # Increase concurrent connection limit
        backlog=100  # Increase connection queue size
    )
