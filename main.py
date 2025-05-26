from fastapi import FastAPI, BackgroundTasks
from NAVscraper import NAVScraper
from BULscraper import BULScraper
from db_utils import upsert_bullz_row
import json
import re
import time
from typing import Dict

app = FastAPI()

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

async def scrape_and_store_data(nav_url: str, bulli_url: str):
    # NAV page
    nav_scraper = NAVScraper(template_path="data.json")
    nav_html = nav_scraper.fetch_html(nav_url)
    nav_content = nav_scraper.extract_content(nav_html)
    nav_json_template = nav_scraper.load_json_template()
    nav_result = nav_scraper.ask_gpt4o(nav_content, nav_json_template)
    cleaned_nav_result = extract_json_from_response(nav_result)
    try:
        nav_result_dict = json.loads(cleaned_nav_result)
    except Exception as e:
        print("Error parsing NAV JSON:", e)
        nav_result_dict = {}
    
    # Bulli page (screenshot + vision)
    bulli_scraper = BULScraper(template_path="data2.json")
    time.sleep(5)
    screenshot_path = await bulli_scraper.take_screenshot(bulli_url)  # Add await here
    bulli_json_template = bulli_scraper.load_json_template()
    bulli_result = bulli_scraper.ask_gpt4o_with_image(screenshot_path, bulli_json_template)
    cleaned_bulli_result = extract_json_from_response(bulli_result)
    try:
        bulli_result_dict = json.loads(cleaned_bulli_result)
    except Exception as e:
        print("Error parsing Bulli JSON:", e)
        bulli_result_dict = {}

    # Changing 'aAa' to 'aaa' due to postgres column name constraints
    if 'aAa' in bulli_result_dict:
        bulli_result_dict['aaa'] = bulli_result_dict.pop('aAa')

    # MERGING DICTIONARIES
    merged_result = {**nav_result_dict, **bulli_result_dict}
    upsert_bullz_row(merged_result)
    return merged_result

@app.get("/")
async def root():
    return {"message": "Welcome to the Bull Scraper API"}

@app.post("/scrape/")
async def scrape_data(background_tasks: BackgroundTasks):
    nav_url = "https://nordic.mloy.fi/NAVBull/BULL/HOLNLDM000671889948/HOL"
    bulli_url = "https://bulli.vit.de/home/details/528000671889948"
    
    # Add the scraping task to background tasks
    background_tasks.add_task(scrape_and_store_data, nav_url, bulli_url)
    
    return {"message": "Scraping task has been started"}

@app.get("/status")
async def get_status():
    # You might want to add some status checking logic here
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
