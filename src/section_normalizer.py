import re
from src.txt_cleaner import normalize_text as basic_normalize

def preprocess_sections(text):
    sections = ['EDUCATION', 'SKILLS', 'CORE COMPETENCIES', 'AREAS OF EXPERTISE',
                'PROJECTS', 'RELEVANT PROJECTS', 'PORTFOLIO',
                'EXPERIENCE', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE', 'INTERNSHIP']

    for sec in sections:
        text = re.sub(r'(?<![\n])(' + sec + r')', r'\n\1', text, flags=re.IGNORECASE)
        text = re.sub(r'(' + sec + r')(?![\n])', r'\1\n', text, flags=re.IGNORECASE)
    return text


def standardize_sections(text):
    def replace_if_line_alone(text, section_names, replacement):
        # The pattern matches only when section header is on a line by itself possibly with colon or dot, no other text
        pattern = r'^\s*(' + '|'.join(section_names) + r')\s*[:.]?\s*$'
        return re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.MULTILINE)

    text = replace_if_line_alone(text, ['EDUCATION'], '=== EDUCATION ===')
    text = replace_if_line_alone(text, ['SKILLS', 'CORE COMPETENCIES', 'AREAS OF EXPERTISE'], '=== SKILLS ===')
    text = replace_if_line_alone(text, ['PROJECTS', 'RELEVANT PROJECTS', 'PORTFOLIO'], '=== PROJECTS ===')
    text = replace_if_line_alone(text, ['EXPERIENCE', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE'], '=== EXPERIENCE ===')

    # Preserve line breaks
    text = re.sub(r'[ ]{2,}', ' ', text)
    return text.strip()




def normalize_text(text):
    text = basic_normalize(text)  # Unicode normalization, tabs removal, collapsing spaces
    text = preprocess_sections(text)  # Inserts newlines before and after section headers like EDUCATION, SKILLS, etc.
    text = standardize_sections(text)  # Converts those section headers lines to === EDUCATION === etc., preserving line breaks
    return text

