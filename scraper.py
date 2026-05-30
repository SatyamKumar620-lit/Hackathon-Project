# ================================
# 🏆 Hackathon Template Notebook
# Prospect Research Agent
# ================================

# ========= CONFIG =========
# 🔑 Add your API key here
import requests
import re
import json
import google.generativeai as genai

from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from urllib.parse import urljoin, urlparse

import google.generativeai as genai

API_KEY = "YOUR_ACTUAL_GEMINI_KEY"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def fetch_page(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
            allow_redirects=True
        )

        if response.status_code >= 400:
            print(f"Blocked: {url} ({response.status_code})")

        return response.text

    except Exception as e:
        print("Fetch Error:", e)
        return ""

from bs4 import BeautifulSoup
import re

def clean_html(html):

    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "meta",
        "link"
    ]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)

    text = re.sub(r"\s+", " ", text)

    return text[:15000]


def extract_links(base_url, html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = []

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        full_url = urljoin(
            base_url,
            href
        )

        links.append(full_url)

    return list(set(links))


def get_relevant_pages(base_url, links):

    keywords = [
        "about",
        "contact",
        "service",
        "services",
        "solution",
        "solutions",
        "company",
        "who-we-are"
    ]

    selected = []

    for link in links:

        path = urlparse(
            link
        ).path.lower()

        score = 0

        for keyword in keywords:

            score = max(
                score,
                fuzz.partial_ratio(
                    path,
                    keyword
                )
            )

        if score >= 75:
            selected.append(link)

    return selected[:3]


def extract_emails(text):

    emails = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    return list(set(emails))

def extract_phones(text):

    matches = re.findall(
        r'(?:\+\d{1,3}[\s\-]?)?(?:\(?\d{2,5}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,}',
        text
    )

    phones = []

    for m in matches:

        digits = re.sub(r"\D", "", m)

        if len(digits) < 10:
            continue

        # Reject year sequences
        if digits.startswith(("200", "201", "202")):
            continue

        phones.append(m.strip())

    return list(set(phones))


def ask_gemini(content, emails, phones):


    prompt = f"""
You are a strict information extraction engine.

Rules:
1. Use ONLY information found in text.
2. Never invent information.
3. Return valid JSON only.
4. If data is missing return

IMPORTANT:
- Never infer phone numbers.
- Use only phone numbers from Detected Phones.
- If no valid phone exists, return "".
- Never use years, dates, counts, statistics, or revenue figures as phone numbers."".

Website Content:

{content[:12000]}

Detected Emails:
{emails}

Detected Phones:
{phones}

IMPORTANT:
Use ONLY phone numbers from the Detected Phones section.
If none are valid, return "".
Never use years, dates, revenue figures, employee counts, or other numbers as phone numbers.

Return:

{{
  "website_name":"",
  "company_name":"",
  "address":"",
  "mobile_number":"",
  "mail":[],
  "core_service":"",
  "target_customer":"",
  "probable_pain_point":"",
  "outreach_opener":""
}}
"""

    try:

        response = model.generate_content(
            prompt
        )

        text = response.text

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        data = json.loads(text)

        return data

    except Exception as e:

            print("========== GEMINI ERROR ==========")
            print(str(e))
            print("==================================")

    return {
        "website_name": "",
        "company_name": "",
        "address": "",
        "mobile_number": "",
        "mail": emails,
        "core_service": "",
        "target_customer": "",
        "probable_pain_point": "",
        "outreach_opener": ""
    }


# ========= REQUIRED FUNCTION =========

def enrich_company(url: str) -> dict:
    """
    Input: Company URL
    Output: Structured company profile (STRICT FORMAT)
    """

    homepage_html = fetch_page(url)

    if not homepage_html:

        return {
            "website_name": "",
            "company_name": "",
            "address": "",
            "mobile_number": "",
            "mail": [],
            "core_service": "",
            "target_customer": "",
            "probable_pain_point": "",
            "outreach_opener": ""
        }

    text_parts = []

    homepage_text = clean_html(
        homepage_html
    )

    text_parts.append(
        homepage_text
    )

    links = extract_links(
        url,
        homepage_html
    )

    pages = get_relevant_pages(
        url,
        links
    )

    for page in pages:

        html = fetch_page(page)

        if html:

            page_text = clean_html(
                html
            )

            text_parts.append(
                page_text
            )

    combined_text = "\n".join(
        text_parts
    )

    emails = extract_emails(
        combined_text
    )

    phones = extract_phones(
        combined_text
    )

    data = ask_gemini(
        combined_text,
        emails,
        phones
    )

    data["mail"] = emails

    valid_phone = ""

    for p in phones:
        digits = re.sub(r"\D", "", p)

        if len(digits) >= 10:
            valid_phone = p
            break

    data["mobile_number"] = valid_phone

    required_fields = [
        "website_name",
        "company_name",
        "address",
        "mobile_number",
        "mail",
        "core_service",
        "target_customer",
        "probable_pain_point",
        "outreach_opener"
    ]

    for field in required_fields:

        if field not in data:

            if field == "mail":
                data[field] = []
            else:
                data[field] = ""

    return data


