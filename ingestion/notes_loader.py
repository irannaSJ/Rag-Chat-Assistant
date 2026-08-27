from processing.cleaner import clean_text
def load_notes(file_path:str):
    with open(file_path, "r" , encoding = "utf-8") as file:
        raw_text = file.read()

    cleaned_text = clean_text(raw_text)

    return [{
        "text":cleaned_text,
        "metadata":{
            "source_type":"NOTES",
            "source_name":file_path
        }
    }]
