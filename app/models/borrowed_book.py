from datetime import datetime, timezone

from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BorrowedBook(Base):
    __tablename__ = "borrowed_books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    reader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    borrow_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    return_date: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
