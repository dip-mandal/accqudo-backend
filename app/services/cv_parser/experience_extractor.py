import re


def extract_experience(text):

    experience = []

    for line in text.split("\n"):

        if any(x in line.lower() for x in ["professor","researcher","scientist","lecturer","assistant professor"]):

            years = re.findall(r"(19|20)\d{2}", line)

            experience.append({
                "title": line.strip(),
                "institution": "",
                "start_year": int(years[0]) if years else 0,
                "end_year": int(years[-1]) if len(years) > 1 else 0,
                "department": ""
            })

    return experience