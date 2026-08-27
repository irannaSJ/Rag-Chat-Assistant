from PyPDF2 import PdfReader
from processing.cleaner import clean_text

def load_pdf(file_path : str):
    reader = PdfReader(file_path)
    documents = []

    for page_num,page in enumerate(reader.pages, start = 1):
        raw_text = page.extract_text()
        cleaned_text = clean_text(raw_text)

        if cleaned_text:
            documents.append({
                "text":cleaned_text,
                "metadata":{
                    "source_type":"PDF",
                    "source_name":file_path,
                    "page":page_num
                }
            })

    return documents