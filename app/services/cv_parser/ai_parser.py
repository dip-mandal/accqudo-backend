from .section_detector import split_sections
from .education_extractor import extract_education
from .experience_extractor import extract_experience
from .publication_extractor import extract_publications
from .deduplicator import remove_duplicates
from .ai_validator import validate_with_ai


def parse_cv_advanced(text):

    sections = split_sections(text)

    education = extract_education(sections.get("education",""))

    experience = extract_experience(sections.get("experience",""))

    publications = extract_publications(sections.get("publications",""))

    publications = remove_duplicates(publications,"title")

    data = {
        "summary":"",
        "skills":[],
        "education":education,
        "experience":experience,
        "publications":publications
    }

    return validate_with_ai(data)