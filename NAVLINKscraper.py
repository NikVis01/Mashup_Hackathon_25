import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv

async def scrape_all_bull_links_playwright(start_url, output_csv="bull_links.csv"):
    all_links = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(start_url)
        page_num = 1

        while True:
            print(f"Scraping page {page_num}...")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            for row in soup.find_all("tr"):
                name_cell = row.find("td", class_="name-cell")
                if name_cell:
                    a_tag = name_cell.find("a")
                    if a_tag and a_tag.get("href"):
                        bull_link = a_tag["href"]
                        bull_name = a_tag.text.strip()
                        # Make absolute if needed
                        bull_link = page.url.split('?')[0] + bull_link if bull_link.startswith('/') else bull_link
                        all_links.append({"name": bull_name, "url": bull_link})

            # Find the next page button by its onclick attribute and text '>'
            next_button = await page.query_selector('a[onclick*="NB.BullSearch"] >> text=>')
            if next_button:
                await next_button.click()
                await page.wait_for_timeout(1500)  # Wait for page to load
                page_num += 1
            else:
                break

        await browser.close()

    # Write to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url"])
        writer.writeheader()
        for link in all_links:
            writer.writerow(link)
    print(f"Extracted {len(all_links)} bull links to {output_csv}")

# To run:
asyncio.run(scrape_all_bull_links_playwright("https://nordic.mloy.fi/NAVBull/?breed=HOL&country=AllCountries&-progenyTest=WithDFS&orderBy=NTM&desc&pageSize=50&top=50"))