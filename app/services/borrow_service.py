from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.borrowed_book import BorrowedBook
from app.models.user import User
from app.schemas.borrow import BorrowRequest


async def borrow_book(session: AsyncSession, data: BorrowRequest) -> BorrowedBook:
    async with session.begin():
        book_result = await session.execute(
            select(Book).where(Book.id == data.book_id).with_for_update()
        )
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        user_result = await session.execute(select(User).where(User.id == data.reader_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if book.copies_count < 1:
            raise HTTPException(status_code=400, detail="No available copies")

        active_borrows = await session.execute(
            select(func.count())
            .select_from(BorrowedBook)
            .where(
                BorrowedBook.reader_id == data.reader_id,
                BorrowedBook.return_date.is_(None),
            )
        )
        count = active_borrows.scalar()

        if count >= 3:
            raise HTTPException(status_code=400, detail="Reader has already borrowed 3 books")

        borrowed = BorrowedBook(book_id=data.book_id, reader_id=data.reader_id)

        session.add(borrowed)

        book.copies_count -= 1
        session.add(book)

    await session.refresh(borrowed)
    return borrowed


async def return_book(session: AsyncSession, data: BorrowRequest) -> None:
    async with session.begin():
        book_result = await session.execute(select(Book).where(Book.id == data.book_id))
        book = book_result.scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        user_result = await session.execute(select(User).where(User.id == data.reader_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = await session.execute(
            select(BorrowedBook).where(
                BorrowedBook.book_id == data.book_id,
                BorrowedBook.reader_id == data.reader_id,
                BorrowedBook.return_date.is_(None),
            )
        )
        borrowed = result.scalar_one_or_none()
        if not borrowed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book was not borrowed by this reader or already returned",
            )

        book.copies_count += 1
        borrowed.return_date = datetime.now(timezone.utc)


async def get_active_borrowed_books(session: AsyncSession, reader_id: int) -> list[Book]:
    result = await session.execute(
        select(Book)
        .join(BorrowedBook, Book.id == BorrowedBook.book_id)
        .where(BorrowedBook.reader_id == reader_id, BorrowedBook.return_date.is_(None))
    )
    return result.scalars().all()
