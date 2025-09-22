import unicodedata
import re

def normalize_text(text):
    # Normalize Unicode (accents → ASCII)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remove tabs and carriage returns
    text = re.sub(r'[\t\r]+', ' ', text)
    # Collapse multiple spaces/newlines to one space
    text = re.sub(r'\s+', ' ', text).strip()
    return text
