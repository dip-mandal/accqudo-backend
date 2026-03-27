import re


def extract_publications(text):

    pubs = []

    for line in text.split("\n"):

        year = re.search(r"(19|20)\d{2}", line)

        if year and len(line) > 25:

            pubs.append({
                "title": line.strip(),
                "year": int(year.group()),
                "type": "Journal",
                "journal": ""
            })

    return pubs