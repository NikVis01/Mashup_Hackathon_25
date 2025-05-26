import os
import requests
from bs4 import BeautifulSoup
import openai
import json

class NAVScraper:
    def __init__(self, openai_api_key=None, template_path="data.json"):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key
        self.path = template_path

    def fetch_html(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def extract_trait_value(self, soup, trait_name):
        for span in soup.find_all("span", class_="toggle collapsed"):
            text = span.get_text(strip=True).replace('"', '').lower()
            if trait_name.lower() == text:
                next_span = span.find_next_sibling("span")
                if next_span:
                    return next_span.get_text(strip=True)
        return ""

    def extract_content(self, html):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else ""
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]
        links = [a['href'] for a in soup.find_all('a', href=True)]
        body_text = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        dropdowns = [
            span.get_text(" ", strip=True)
            for span in soup.find_all("span", class_="toggle collapsed")
        ]
        bull_names = [span.get_text(strip=True) for span in soup.find_all("span", class_="name")]
        traits = [
            ul.get_text(" ", strip=True)
            for ul in soup.find_all("ul", class_="traits level1")
        ]
        ntm_value = ""
        for span in soup.find_all("span"):
            if span.get_text(strip=True) == "NTM":
                next_span = span.find_next_sibling("span")
                if next_span:
                    ntm_value = next_span.get_text(strip=True)
                break
        yield_value = self.extract_trait_value(soup, "Yield")
        return {
            "title": title,
            "headings": headings,
            "links": links,
            "body_text": body_text[:3000],
            "dropdowns": dropdowns,
            "traits": traits,
            "bull_names": bull_names,
            "ntm": ntm_value,
            "yield": yield_value
        }

    def ask_gpt4o(self, content, json_template):
        prompt = f"""
You are an information extraction assistant. You are given a page that corresponds to a specific bull's traits.
The bull's name is found in a <span class="name"> element.
The traits and their descriptions are located within dropdowns, specifically in <span class="toggle collapsed"> elements and their associated content.
Additionally, some traits (like "NTM") are not in dropdowns but are displayed directly in the page (e.g., in a table cell).

For example, if the dropdown contains:
<span class="toggle collapsed" data-tooltip="..."><b>Describes:</b> ... <b>Includes:</b> ...</span>
then extract the trait name, description, and any included values.

Extract the following information from the provided content and respond ONLY in the following JSON format (fill in the values):

JSON format:
{json.dumps(json_template, indent=2)}

Content:
Bull Name(s): {content['bull_names']}
Dropdowns (each contains a trait and its description): {content['dropdowns']}
Traits (raw HTML text from trait containers): {content['traits']}
NTM (or other non-dropdown trait): {content['ntm']}
Yield: {content['yield']}
"""
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content

    def load_json_template(self):
        with open(self.path, "r") as f:
            return json.load(f)

if __name__ == "__main__":
    url = "https://nordic.mloy.fi/NAVBull/BULL/HOLNLDM000671889948/HOL"
    scraper = NAVScraper()
    html = scraper.fetch_html(url)
    content = scraper.extract_content(html)
    json_template = scraper.load_json_template()
    result = scraper.ask_gpt4o(content, json_template)
    # print(result)
