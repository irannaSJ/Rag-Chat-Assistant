import re 
def clean_text(text : str) -> str:
    if not text:
        return ""
    
    text = re.sub(r"\s+"," ",text)
    text = re.sub(r"\n+", "\n",text)

    return text.strip()