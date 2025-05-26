from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    publication_year: Mapped[int | None] = mapped_column(nullable=True)
    isbn: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    copies_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (CheckConstraint("copies_count >= 0", name="copies_count_non_negative"),)
