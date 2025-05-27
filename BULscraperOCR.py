import os
import openai
import json
from playwright.async_api import async_playwright
import asyncio
from paddleocr import PaddleOCR
import urllib.request
import tarfile
import requests
import re


OCR_KEY=os.environ.get("OCR_KEY")

class BULScraperOCR:
    def __init__(self, openai_api_key=None, template_path="data2.json"):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key
        #self.ocr_key = os.environ.get('OCR_API_KEY')
        self.ocr_key = 'K88521408988957'
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

    def extract_text_with_ocr(self, image_path):
        payload = {
            'isOverlayRequired': False,
            'apikey': self.ocr_key,
            'language': "eng",
        }
        with open(image_path, 'rb') as f:
            r = requests.post(
                'https://api.ocr.space/parse/image',
                files={image_path: f},
                data=payload,
            )
        output = r.content.decode()
        print("Raw OCR API output:", output)
        try:
            result = json.loads(output)
            # Check for expected structure
            if (
                "ParsedResults" in result and
                isinstance(result["ParsedResults"], list) and
                len(result["ParsedResults"]) > 0 and
                "ParsedText" in result["ParsedResults"][0]
            ):
                text = result["ParsedResults"][0]["ParsedText"]
                print("Extracted OCR text:", text)
                return text
            else:
                print("OCR API did not return expected structure.")
                return ""
        except Exception as e:
            print("Error parsing OCR API response:", e)
            return ""

    def ask_gpt4o_with_image(self, image_path, json_template):
        # First, extract text using OCR
        ocr_text = self.extract_text_with_ocr(image_path)
        print(f"OCR Extracted Text:\n{ocr_text}\n")
        prompt = f"""
You are an information extraction assistant. I will provide you with:
1. OCR-extracted text from the image
2. The actual image

Extract the following fields from both the OCR text and the image of a bull's profile page, weighing the OCR higher. 
The OCR text may contain some errors, so use the image to verify and correct any mistakes.
Respond ONLY with a valid JSON object in this format (fill in the values, leave as null if not found):

OCR Extracted Text:
{ocr_text}

JSON Template:
{json.dumps(json_template, indent=2)}

Be as specific as possible and try to fill all specified fields as well as you can. 
Never return percentage signs or other symbols.
If there's a conflict between OCR text and what you see in the image, trust the image.
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
        result_json = response.choices[0].message.content
        result_dict = json.loads(result_json)

        # Now result_dict["chest_width"] is just the number as a string
        return json.dumps(result_dict)

    def load_json_template(self):
        with open(self.path, "r") as f:
            return json.load(f)

if __name__ == "__main__":
    import asyncio
    url = "https://bulli.vit.de/home/details/528000671889948"
    scraper = BULScraperOCR()
    screenshot_path = asyncio.run(scraper.take_screenshot(url))
    json_template = scraper.load_json_template()
    result = scraper.ask_gpt4o_with_image(screenshot_path, json_template)
    print(result)