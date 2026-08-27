import requests
from bs4 import BeautifulSoup
from processing.cleaner import clean_text

def load_website(url:str):
    response = requests.get(url, timeout = 10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    #rm script
    for tag in soup(["script","style","nav","footer","header"]):
        tag.decompose()

    raw_text = soup.get_text(separator = " ")
    cleaned_text = clean_text(raw_text)

    return [{
        "text":cleaned_text,
        "metadata":{
            "source_type":"WEBSITE",
            "source_name":url
        }
    }]
