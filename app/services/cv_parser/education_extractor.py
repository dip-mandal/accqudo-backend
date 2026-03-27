import re


def extract_education(text):

    education = []

    for line in text.split("\n"):

        if any(x in line.lower() for x in ["phd","ph.d","msc","m.sc","bsc","b.tech","m.tech","bachelor","master"]):

            year = re.findall(r"(19|20)\d{2}", line)

            education.append({
                "degree": line.strip(),
                "institution": "",
                "graduation_year": int(year[0]) if year else 0,
                "thesis_title": ""
            })

    return education