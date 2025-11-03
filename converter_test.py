import pdfplumber
from docx import Document
import os
import re
import json
import spacy

# =========================================================
# MILESTONE 3: SETUP NLP MODEL
# =========================================================
# Load the small English model ONCE at the start of the script.
try:
    # Set nlp as a global variable
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("FATAL ERROR: spaCy model 'en_core_web_sm' not found.")
    print("Please run: python -m spacy download en_core_web_sm")
    exit()

# =========================================================
# MILESTONE 1.2: DOCUMENT CONVERSION
# =========================================================

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with pdfplumber.open(file_path) as pdf:
            # Join text from all pages
            text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
        return text
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error extracting PDF: {e}"

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = Document(file_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error extracting DOCX: {e}"

# =========================================================
# MILESTONE 1.3: TEXT CLEANING
# =========================================================

def clean_resume_text(raw_text):
    """Performs essential cleaning on raw resume text."""

    if not raw_text:
        return ""

    # 1. Merge hyphenated words across lines (e.g., 'soft-\nware' -> 'software')
    text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', raw_text, flags=re.IGNORECASE)

    # 2. Remove common resume structural markers (e.g., page numbers, if they contain noise)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # 3. Remove non-ASCII characters and weird unicode 
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # 4. Normalize excessive whitespace (multiple spaces, tabs, newlines) to a single space
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. Convert everything to lowercase for simple NLP models
    text = text.lower()
    
    return text

# =========================================================
# MILESTONE 2.1: CONTACT INFO EXTRACTION (RegEx)
# =========================================================

def extract_email(text):
    """Uses regex to find email addresses."""
    email = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    return email[0] if email else None

def extract_phone_number(text):
    """Uses regex to find phone numbers, standardizing various formats."""
    phone = re.findall(r'(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\(\d{3}\)\s*\d{3}[-\s]?\d{4}|\d{10,15})', text)
    cleaned_phone = [re.sub(r'\D', '', p) for p in phone]
    return next((p for p in cleaned_phone if len(p) >= 10 and len(p) <= 15), None)

def extract_urls(text):
    """Uses regex to find common professional URLs (LinkedIn, GitHub)."""
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    relevant_urls = [u for u in urls if 'linkedin' in u.lower() or 'github' in u.lower()]
    return relevant_urls

# =========================================================
# MILESTONE 2.2 & 2.3: SKILLS AND NAME EXTRACTION
# =========================================================

def extract_name(raw_text):
    """Extracts name by taking the first line before any structured data (MVP approach)."""
    lines = raw_text.strip().split('\n')
    name_candidate = lines[0].strip()
    name = re.sub(r'[|:,-]', '', name_candidate).strip()
    
    if len(name.split()) > 5 or len(name) < 4:
        names_found = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?', raw_text)
        return names_found[0].title() if names_found else "N/A (Failed Fallback)"
    
    return name.title()

def extract_skills(cleaned_text):
    """Extracts skills using a keyword-matching approach."""
    try:
        with open('skills.txt', 'r') as f:
            skill_list = [line.strip().lower() for line in f]
    except FileNotFoundError:
        return ["WARNING: skills.txt missing. Cannot extract skills."]
    
    found_skills = set()
    for skill in skill_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', cleaned_text):
            found_skills.add(skill)
    
    return list(found_skills)

# =========================================================
# MILESTONE 3.2: NLP ENTITY EXTRACTION
# =========================================================

def extract_nlp_entities(cleaned_text):
    """Uses a spaCy pre-trained model to extract entities like education and experience."""
    global nlp # Access the globally loaded spaCy model
    doc = nlp(cleaned_text)
    
    # Extract entities that are often relevant to education/experience (Organizations, Dates, Locations)
    education_and_experience_entities = []
    
    for ent in doc.ents:
        # We look for organizations (schools/companies), dates (start/end), and proper nouns near keywords
        if ent.label_ in ('ORG', 'DATE') or 'education' in ent.text.lower() or 'experience' in ent.text.lower():
             # Simple filtering to get meaningful names, not single letters
            if len(ent.text.strip().split()) > 1 or ent.label_ == 'DATE':
                education_and_experience_entities.append(f"{ent.text.strip()} ({ent.label_})")
    
    # We clean the list using a set and only take the unique, top 5 results
    return list(set(education_and_experience_entities))[:5]


# =========================================================
# MAIN EXECUTION AND TEST BLOCK (MILESTONE 3 FINAL)
# =========================================================

if __name__ == "__main__":
    TEST_DIR = "test_files"
    pdf_path = os.path.join(TEST_DIR, "sample_resume.pdf")

    print("--- Starting FINAL Parser Pipeline Test (PDF) ---")
    
    # STEP 1: CONVERT (M1.2)
    raw_text = extract_text_from_pdf(pdf_path)
    if "Error" in raw_text:
        print(f"FATAL ERROR: Conversion failed. {raw_text}")
        exit()

    # STEP 2: CLEAN (M1.3)
    cleaned_text = clean_resume_text(raw_text)
    print(f"1. Converted & Cleaned. Length: {len(cleaned_text)} chars.")
    print(f"   Snippet: {cleaned_text[:150]}...")
    
    # STEP 3: EXTRACT ALL DATA (M2 & M3)
    
    nlp_results = extract_nlp_entities(cleaned_text)
    
    structured_data = {
        # M2.3 Name
        "name": extract_name(raw_text), 
        # M2.1 Contact Info
        "email": extract_email(cleaned_text),
        "phone": extract_phone_number(cleaned_text),
        "urls": extract_urls(cleaned_text),
        # M2.2 Skills
        "skills": extract_skills(cleaned_text), 
        # M3.2 NLP Results
        "nlp_education_experience": nlp_results,
        "cleaned_text_snippet": cleaned_text[:500] 
    }
    
    print("\n--- Extracted Structured Data (JSON Output) ---")
    
    # Final check for completeness
    if structured_data['nlp_education_experience'] and len(structured_data['skills']) > 0:
        print("🎉 MVP COMPLETE: All rule-based and advanced NLP extraction successful.")
    else:
        print("⚠️ WARNING: Advanced NLP results may be empty. Check sample resume formatting.")

    # Print the structured result
    print(json.dumps(structured_data, indent=4))
    
    print("\n--- Project Fully Operational ---")