import os
import openai
import json
from playwright.async_api import async_playwright
import asyncio
import os

class BULScraper:
    def __init__(self, openai_api_key=None, template_path="data2.json"):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key
        self.path = template_path

    async def take_screenshot(self, url):  # Make this method async
        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            # Set a large viewport height to help capture long pages
            page = await browser.new_page(viewport={"width": 1920, "height": 3000})
            await page.goto(url)
            await asyncio.sleep(5)  # Wait for JS to render
            # Scroll to the bottom to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)  # Wait for any lazy-loaded content
            # Optionally, scroll back to top for completeness
            await page.evaluate("window.scrollTo(0, 0)")
            # Take the full page screenshot
            screenshot_path = "screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            await browser.close()
            return screenshot_path

    def ask_gpt4o_with_image(self, image_path, json_template):
        prompt = f"""
You are an information extraction assistant. Extract the following fields from the attached screenshot of a bull's profile page. Respond ONLY with a valid JSON object in this format (fill in the values, leave as null if not found):
Be as specific as possible and try to fill all specified fields as well as you can. Never return percentage signs or other symbols.
{json.dumps(json_template, indent=2)}
"""
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
        # OpenAI Vision API expects base64-encoded image URLs
        import base64
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content

    def load_json_template(self):
        with open(self.path, "r") as f:
            return json.load(f)

if __name__ == "__main__":
    import asyncio
    url = "https://bulli.vit.de/home/details/528000671889948"
    scraper = BULScraper()
    screenshot_path = asyncio.run(scraper.take_screenshot(url))
    json_template = scraper.load_json_template()
    result = scraper.ask_gpt4o_with_image(screenshot_path, json_template)
    print(result)
