import re

def standardize_sections(text):
    # Ensure text is clean of excess spaces before searching
    text = re.sub(r'\s{2,}', ' ', text).strip()
    
    # --------------------------------------------------------
    # 1. FIX SKILLS: Avoid replacing 'my skills', 'your skills', 'gaining skills'
    # Pattern: Look for SKILLS/COMPETENCIES that are NOT preceded by a possessive or verb
    text = re.sub(
        r'(?<!my\s)(?<!gaining\s)(?<!having\s)(?<!our\s)' # Negative lookbehind to exclude common prefixes
        r'\b(SKILLS|CORE COMPETENCIES|AREAS OF EXPERTISE)\s*[:]?\b', 
        ' === SKILLS === ', # Note the added spaces for clean separation (Fixes the last issue too)
        text, 
        flags=re.IGNORECASE
    )
    
    # --------------------------------------------------------
    # 2. FIX PROJECTS: Avoid replacing 'built real-world projects'
    # Pattern: Look for PROJECTS that are NOT preceded by a verb or adjective
    text = re.sub(
        r'(?<!built\s)(?<!real-world\s)(?<!my\s)(?<!latest\s)' # Exclude common sentence structures
        r'\b(PROJECTS|RELEVANT PROJECTS|PORTFOLIO)\s*[:]?\b', 
        ' === PROJECTS === ', # Note the added spaces
        text, 
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # 3. FIX EXPERIENCE: Avoid replacing 'gaining practical experience'
    # Pattern: Look for EXPERIENCE that is NOT preceded by a verb or adjective
    text = re.sub(
        r'(?<!gaining\s)(?<!practical\s)(?<!work\s)(?<!professional\s)' # Exclude common sentence structures
        r'\b(EXPERIENCE|WORK HISTORY|PROFESSIONAL EXPERIENCE)\s*[:]?\b', 
        ' === EXPERIENCE === ', # Note the added spaces
        text, 
        flags=re.IGNORECASE
    )
    
    # --------------------------------------------------------
    # 4. Final Cleanup: Ensure only single spaces remain after all replacements
    text = re.sub(r'\s{2,}', ' ', text).strip() 
    
    return text