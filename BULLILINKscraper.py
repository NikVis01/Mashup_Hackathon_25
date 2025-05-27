import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv

async def scrape_bull_details_links(start_url, output_csv="bull_details_links.csv"):
    all_links = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(start_url)
        last_height = 0
        same_height_count = 0

        print("Scrolling to load all bulls...")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_height_count += 1
                if same_height_count > 2:
                    break
            else:
                same_height_count = 0
                last_height = new_height

        print("Parsing loaded HTML...")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.find_all("mat-card")  # Adjust this selector!
        print(f"Found {len(cards)} cards.")
        for card in cards:
            # Adjust selectors as needed!
            name_tag = card.find("div", class_="mat-card-title")
            bull_name = name_tag.text.strip() if name_tag else "Unknown"
            details_btn = card.find("button", string="Details")
            details_link = None
            if details_btn and details_btn.has_attr("ng-reflect-router-link"):
                details_link = details_btn["ng-reflect-router-link"]
            all_links.append({"name": bull_name, "url": details_link})

        await browser.close()

    if all_links:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "url"])
            writer.writeheader()
            for link in all_links:
                writer.writerow(link)
        print(f"Extracted {len(all_links)} bull details links to {output_csv}")
    else:
        print("No links found! Check your selectors and page structure.")

# To run:
asyncio.run(scrape_bull_details_links('https://bulli.vit.de/home'))