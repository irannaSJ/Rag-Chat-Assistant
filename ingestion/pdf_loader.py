import os
from pypdf import PdfReader
from processing.cleaner import clean_text


def load_pdf(file_path: str, source_name: str | None = None) -> list[dict]:
    reader = PdfReader(file_path)
    display_name = source_name or os.path.basename(file_path)
    documents = []

    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned_text = clean_text(raw_text)

        if cleaned_text:
            documents.append({
                "text": cleaned_text,
                "metadata": {
                    "source_type": "PDF",
                    "source_name": display_name,
                    "page": page_num,
                },
            })

    return documents