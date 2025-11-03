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
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("FATAL ERROR: spaCy model 'en_core_web_sm' not found.")
    print("Please run: python -m spacy download en_core_web_sm")
    # Set nlp to None so other functions don't crash, but fail gracefully
    nlp = None 

# =========================================================
# CORE FUNCTIONS (M1.2)
# =========================================================

def extract_text_from_pdf(file_path):
    # (Implementation remains the same)
    try:
        with pdfplumber.open(file_path) as pdf:
            text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
        return text
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error extracting PDF: {e}"

def extract_text_from_docx(file_path):
    # (Implementation remains the same)
    try:
        doc = Document(file_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error extracting DOCX: {e}"

# =========================================================
# CLEANING AND EXTRACTION FUNCTIONS (M1.3, M2, M3)
# =========================================================

def clean_resume_text(raw_text):
    # (Implementation remains the same)
    if not raw_text: return ""
    text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', raw_text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def extract_email(text):
    # (Implementation remains the same)
    email = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    return email[0] if email else None

def extract_phone_number(text):
    # (Implementation remains the same)
    phone = re.findall(r'(\d{3}[-\s]?\d{3}[-\s]?\d{4}|\(\d{3}\)\s*\d{3}[-\s]?\d{4}|\d{10,15})', text)
    cleaned_phone = [re.sub(r'\D', '', p) for p in phone]
    return next((p for p in cleaned_phone if len(p) >= 10 and len(p) <= 15), None)

def extract_urls(text):
    # (Implementation remains the same)
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    relevant_urls = [u for u in urls if 'linkedin' in u.lower() or 'github' in u.lower()]
    return relevant_urls

def extract_name(raw_text):
    # (Implementation remains the same)
    lines = raw_text.strip().split('\n')
    name_candidate = lines[0].strip()
    name = re.sub(r'[|:,-]', '', name_candidate).strip()
    if len(name.split()) > 5 or len(name) < 4:
        names_found = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?', raw_text)
        return names_found[0].title() if names_found else "N/A (Failed Fallback)"
    return name.title()

def extract_skills(cleaned_text):
    # (Implementation remains the same)
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

def extract_nlp_entities(cleaned_text):
    # (Implementation remains the same)
    global nlp
    if nlp is None:
        return {"error": "NLP model not loaded. Check setup."}

    doc = nlp(cleaned_text)
    education_and_experience_entities = []
    
    for ent in doc.ents:
        if ent.label_ in ('ORG', 'DATE') or 'education' in ent.text.lower() or 'experience' in ent.text.lower():
            if len(ent.text.strip().split()) > 1 or ent.label_ == 'DATE':
                education_and_experience_entities.append(f"{ent.text.strip()} ({ent.label_})")
    
    return list(set(education_and_experience_entities))[:5]

# =========================================================
# FINAL API FUNCTION
# =========================================================

def parse_resume(file_path):
    """
    Main function to process a resume file and return structured JSON data.
    """
    
    # 1. CONVERT
    if file_path.lower().endswith('.pdf'):
        raw_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        raw_text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file type. Must be PDF or DOCX."}

    if "Error" in raw_text:
        return {"error": raw_text}
        
    # 2. CLEAN
    cleaned_text = clean_resume_text(raw_text)
    
    # 3. EXTRACT
    structured_data = {
        "name": extract_name(raw_text), 
        "email": extract_email(cleaned_text),
        "phone": extract_phone_number(cleaned_text),
        "urls": extract_urls(cleaned_text),
        "skills": extract_skills(cleaned_text), 
        "nlp_entities": extract_nlp_entities(cleaned_text),
        "raw_text_length": len(raw_text)
    }
    
    return structured_data

# =========================================================
# API TEST BLOCK
# =========================================================

if __name__ == '__main__':
    TEST_DIR = "test_files"
    # Testing the core PDF functionality
    pdf_path = os.path.join(TEST_DIR, "sample_resume.pdf")
    
    print(f"Testing final API structure with: {pdf_path}")
    result = parse_resume(pdf_path)
    
    print("\n--- FINAL PARSER API OUTPUT ---")
    print(json.dumps(result, indent=4))
    print("\nAPI Test Complete. This function is now ready to be imported and used.")