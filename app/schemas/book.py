from typing import Optional

from pydantic import BaseModel, Field


class BookIn(BaseModel):
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    copies_count: int = Field(default=1, ge=0)


class BookPatch(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    copies_count: Optional[int] = Field(default=None, ge=0)


class BookOut(BaseModel):
    id: int
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    copies_count: int = Field(default=1, ge=0)

    class Config:
        from_attributes = True
