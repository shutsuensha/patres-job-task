from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.schemas.book import BookIn


async def get_book_by_id(session: AsyncSession, book_id: int) -> Book:
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


async def list_books(session: AsyncSession) -> list[Book]:
    result = await session.execute(select(Book))
    return result.scalars().all()


async def create_book(session: AsyncSession, book_data: BookIn) -> Book:
    if book_data.isbn:
        result = await session.execute(select(Book).where(Book.isbn == book_data.isbn))
        existing_book = result.scalar_one_or_none()
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book with this ISBN already exists",
            )

    new_book = Book(**book_data.model_dump())
    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)
    return new_book


async def update_book(session: AsyncSession, book_id: int, book_data: BookIn) -> Book:
    book = await get_book_by_id(session, book_id)

    if book_data.isbn:
        result = await session.execute(select(Book).where(Book.isbn == book_data.isbn))
        existing_book = result.scalar_one_or_none()
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book with this ISBN already exists",
            )

    for field, value in book_data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


async def delete_book(session: AsyncSession, book_id: int) -> None:
    book = await get_book_by_id(session, book_id)
    await session.delete(book)
    await session.commit()
