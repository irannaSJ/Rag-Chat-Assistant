import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Normalize Windows/Mac line endings to Unix newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple spaces/tabs on the same line without destroying newlines
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse 3 or more consecutive newlines into a clean paragraph break
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip trailing spaces on each line
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()