import requests
from bs4 import BeautifulSoup
from processing.cleaner import clean_text


def load_website(url: str) -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        tag.decompose()

    # Prefer main/article body if present for cleaner extraction
    main_container = soup.find("main") or soup.find("article") or soup.body or soup
    raw_text = main_container.get_text(separator="\n")
    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        return []

    page_title = soup.title.string.strip() if soup.title and soup.title.string else url

    return [{
        "text": cleaned_text,
        "metadata": {
            "source_type": "WEBSITE",
            "source_name": page_title,
            "url": url,
        },
    }]