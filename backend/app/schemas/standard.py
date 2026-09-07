from typing import List, Optional
from pydantic import BaseModel


class StandardClauseResponse(BaseModel):
    id: str
    standard_id: str
    clause_number: str
    title: str
    text: str
    page: Optional[int] = None
    source_document: Optional[str] = None

    model_config = {"from_attributes": True}


class StandardResponse(BaseModel):
    standard_id: str
    title: str
    version: str
    category: str
    scope: str
    source: Optional[str] = None
    publication_date: Optional[str] = None
    active: bool

    model_config = {"from_attributes": True}


class StandardDetailResponse(StandardResponse):
    clauses: List[StandardClauseResponse] = []
