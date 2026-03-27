def parse_scholar_data(profile):

    publications = []
    top_papers = []

    for pub in profile["publications"]:

        bib = pub.get("bib", {})

        item = {
            "title": bib.get("title"),
            "year": int(bib.get("pub_year", 0)) if bib.get("pub_year") else 0,
            "journal": bib.get("venue", ""),
            "type": "Journal"
        }

        publications.append(item)

        citations = pub.get("num_citations", 0)

        if citations > 50:
            top_papers.append({
                "title": bib.get("title"),
                "citations": citations
            })

    coauthors = []

    for author in profile.get("coauthors", []):

        coauthors.append({
            "name": author.get("name")
        })

    interests = profile.get("interests", [])

    metrics = {
        "citations": profile.get("citedby", 0),
        "h_index": profile.get("hindex", 0),
        "i10_index": profile.get("i10index", 0),
        "citations_per_year": profile.get("cites_per_year", {})
    }

    return publications, top_papers, coauthors, interests, metrics