import sys
import os
from src.file_readers.file_readers_txt import read_txt
from src.file_readers.file_readers_docx import read_docx
from src.file_readers.file_readers_pdf import read_pdf
from src.text_cleaner.section_normalizer import preprocess_sections
from src.text_cleaner.section_normalizer import normalize_text
from src.text_cleaner.remove_personal import remove_personal

def read_any(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.txt':
        return read_txt(file_path)
    if ext == '.docx':
        return read_docx(file_path)
    if ext == '.pdf':
        return read_pdf(file_path)
    print("Unsupported file type:", ext)
    return ""

def main():
    # Default file
    file_path = "sri_resume.txt"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    print(f"Processing file: {file_path}")

    raw = read_any(file_path)
    if not raw.strip():
        print("No text extracted.")
        sys.exit(1)

    print("\n=== BEFORE CLEANING ===\n", raw[:500], "...\n")

    # Remove personal info, normalize text with section preprocessing etc.
    cleaned = normalize_text(preprocess_sections(remove_personal(raw)))

    print("\n=== AFTER CLEANING ===\n", cleaned[:500], "...\n")

    with open("cleaned_sri_resume.txt", "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("\n✅ Saved as cleaned_sri_resume.txt")

if __name__ == "__main__":
    main()
