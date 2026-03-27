from pydantic import BaseModel
from typing import List


class BulkInsertData(BaseModel):

    education: List[dict] = []

    experience: List[dict] = []

    publications: List[dict] = []

    summary: str = ""