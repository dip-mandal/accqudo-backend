from pydantic import BaseModel
from typing import List, Dict


class PublicationItem(BaseModel):
    title: str
    year: int
    journal: str = ""
    type: str = "Journal"


class ScholarImportRequest(BaseModel):
    scholar_url: str


class ScholarConfirmRequest(BaseModel):

    publications: List[PublicationItem]

    citations: int
    h_index: int
    i10_index: int

    research_interests: List[str] = []

    coauthors: List[Dict] = []

    citations_per_year: Dict[str, int] = {}

    top_papers: List[Dict] = []