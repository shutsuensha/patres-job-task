from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BorrowRequest(BaseModel):
    book_id: int
    reader_id: int


class BorrowedBookOut(BaseModel):
    id: int
    book_id: int
    reader_id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None

    class Config:
        from_attributes = True
