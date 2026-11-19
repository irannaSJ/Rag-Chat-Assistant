import os
from processing.cleaner import clean_text


def load_notes_file(file_path: str, source_name: str | None = None) -> list[dict]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        raw_text = file.read()

    display_name = source_name or os.path.basename(file_path)
    return load_notes_text(raw_text, source_name=display_name)


def load_notes_text(raw_text: str, source_name: str = "Quick Note") -> list[dict]:
    cleaned_text = clean_text(raw_text)
    if not cleaned_text:
        return []

    return [{
        "text": cleaned_text,
        "metadata": {
            "source_type": "NOTES",
            "source_name": source_name.strip() or "Quick Note",
        },
    }]