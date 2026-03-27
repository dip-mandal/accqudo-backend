import re

SECTION_PATTERNS = {
    "education": r"(education|academic background)",
    "experience": r"(experience|academic positions|employment)",
    "publications": r"(publications|journal articles|conference papers)",
}


def split_sections(text):

    sections = {}

    current = "general"

    sections[current] = []

    for line in text.split("\n"):

        for key, pattern in SECTION_PATTERNS.items():

            if re.search(pattern, line.lower()):

                current = key
                sections[current] = []
                break

        sections.setdefault(current, []).append(line)

    for k in sections:

        sections[k] = "\n".join(sections[k])

    return sections