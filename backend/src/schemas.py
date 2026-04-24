from pydantic import BaseModel
from typing import List

class ArticleSummary(BaseModel):
    title: str
    summary: str

class PressRelease(BaseModel):
    title: str
    general_summary: str
    articles: List[ArticleSummary]
