from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Librarian(Base):
    __tablename__ = "librarians"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
