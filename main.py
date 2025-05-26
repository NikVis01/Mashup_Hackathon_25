from NAVscraper import NAVScraper
from BULscraper import BULScraper
from db_utils import upsert_bullz_row
import json
import re
import time

def extract_json_from_response(response):
    # Remove markdown code block if present
    match = re.search(r'```(?:json)?\\n(.*?)```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try also with just triple backticks (no newline)
    match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()

if __name__ == "__main__":
    
    # NAV page
    nav_url = "https://nordic.mloy.fi/NAVBull/BULL/HOLNLDM000671889948/HOL"
    nav_scraper = NAVScraper(template_path="data.json")
    nav_html = nav_scraper.fetch_html(nav_url)
    nav_content = nav_scraper.extract_content(nav_html)
    nav_json_template = nav_scraper.load_json_template()
    nav_result = nav_scraper.ask_gpt4o(nav_content, nav_json_template)
    cleaned_nav_result = extract_json_from_response(nav_result)
    try:
        nav_result_dict = json.loads(cleaned_nav_result)
        print("NAV Result Dictionary:", nav_result_dict)
        upsert_bullz_row(nav_result_dict)
    except Exception as e:
        print("Error parsing NAV JSON:", e)
    
    
    # Bulli page (screenshot + vision)
    bulli_url = "https://bulli.vit.de/home/details/528000671889948"
    bulli_scraper = BULScraper(template_path="data2.json")
    time.sleep(5)
    screenshot_path = bulli_scraper.take_screenshot(bulli_url)
    bulli_json_template = bulli_scraper.load_json_template()
    bulli_result = bulli_scraper.ask_gpt4o_with_image(screenshot_path, bulli_json_template)

    # If the LLM returns markdown, clean it
    cleaned_bulli_result = extract_json_from_response(bulli_result)

    try:
        bulli_result_dict = json.loads(cleaned_bulli_result)
        print("Bulli Result Dictionary:", bulli_result_dict)
        upsert_bullz_row(bulli_result_dict)
    except Exception as e:
        print("Error parsing Bulli JSON:", e)

    