from datetime import datetime, timezone

import pytest
from app.models.book import Book
from app.models.borrowed_book import BorrowedBook
from app.models.user import User
from app.schemas.borrow import BorrowRequest
from app.services.borrow_service import borrow_book, get_active_borrowed_books, return_book
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def clear_tables(db: AsyncSession):
    await db.execute(delete(BorrowedBook))
    await db.execute(delete(User))
    await db.execute(delete(Book))
    await db.commit()

    yield

    await db.execute(delete(BorrowedBook))
    await db.execute(delete(User))
    await db.execute(delete(Book))
    await db.commit()


async def test_borrow_book_success(db: AsyncSession):
    async with db.begin():
        user = User(name="John", email="john@example.com")
        book = Book(title="Test Book", author="Author", copies_count=2)
        db.add_all([user, book])

    data = BorrowRequest(book_id=book.id, reader_id=user.id)
    borrowed = await borrow_book(db, data)

    assert borrowed.book_id == book.id
    assert borrowed.reader_id == user.id

    updated_book = (await db.execute(select(Book).where(Book.id == book.id))).scalar_one()
    assert updated_book.copies_count == 1


async def test_borrow_book_book_not_found(db: AsyncSession):
    async with db.begin():
        user = User(name="John", email="john@example.com")
        db.add(user)

    data = BorrowRequest(book_id=999, reader_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await borrow_book(db, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book not found"


async def test_borrow_book_user_not_found(db: AsyncSession):
    async with db.begin():
        book = Book(title="Test Book", author="Author", copies_count=1)
        db.add(book)

    data = BorrowRequest(book_id=book.id, reader_id=999)

    with pytest.raises(HTTPException) as exc_info:
        await borrow_book(db, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


async def test_borrow_book_no_copies(db: AsyncSession):
    async with db.begin():
        user = User(name="John", email="john@example.com")
        book = Book(title="Test Book", author="Author", copies_count=0)
        db.add_all([user, book])

    data = BorrowRequest(book_id=book.id, reader_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await borrow_book(db, data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No available copies"


async def test_borrow_book_max_borrows(db: AsyncSession):
    user = User(name="John", email="john@example.com")
    book = Book(title="Test Book", author="Author", copies_count=5)
    db.add_all([user, book])
    await db.commit()
    await db.refresh(user)
    await db.refresh(book)

    borrows = [
        BorrowedBook(book_id=book.id, reader_id=user.id),
        BorrowedBook(book_id=book.id, reader_id=user.id),
        BorrowedBook(book_id=book.id, reader_id=user.id),
    ]
    db.add_all(borrows)
    await db.commit()

    data = BorrowRequest(book_id=book.id, reader_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await borrow_book(db, data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Reader has already borrowed 3 books"


async def test_return_book_success(db: AsyncSession):
    async with db.begin():
        user = User(name="John", email="john@example.com")
        book = Book(title="Book 1", author="Author", copies_count=1)
        db.add_all([user, book])

    async with db.begin():
        borrowed = BorrowedBook(book_id=book.id, reader_id=user.id)
        db.add(borrowed)

    data = BorrowRequest(book_id=book.id, reader_id=user.id)
    await return_book(db, data)

    updated_book = (await db.execute(select(Book).where(Book.id == book.id))).scalar_one()
    assert updated_book.copies_count == 2

    updated_borrowed = (
        await db.execute(select(BorrowedBook).where(BorrowedBook.id == borrowed.id))
    ).scalar_one()

    assert updated_borrowed.return_date is not None


async def test_return_book_not_found_book(db: AsyncSession):
    async with db.begin():
        user = User(name="John", email="john@example.com")
        db.add(user)

    data = BorrowRequest(book_id=999, reader_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await return_book(db, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book not found"


async def test_return_book_not_found_user(db: AsyncSession):
    async with db.begin():
        book = Book(title="Book 1", author="Author", copies_count=1)
        db.add(book)

    data = BorrowRequest(book_id=book.id, reader_id=999)

    with pytest.raises(HTTPException) as exc_info:
        await return_book(db, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


async def test_return_book_not_borrowed_or_already_returned(db: AsyncSession):
    user = User(name="John", email="john@example.com")
    book = Book(title="Book 1", author="Author", copies_count=1)
    db.add_all([user, book])
    await db.commit()
    await db.refresh(user)
    await db.refresh(book)

    borrowed = BorrowedBook(
        book_id=book.id, reader_id=user.id, return_date=datetime.now(timezone.utc)
    )
    db.add(borrowed)
    await db.commit()

    data = BorrowRequest(book_id=book.id, reader_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await return_book(db, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book was not borrowed by this reader or already returned"


async def test_get_active_borrowed_books(db: AsyncSession):
    user = User(name="John", email="john@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    book1 = Book(title="Active Borrowed Book", author="Author1", copies_count=1)
    book2 = Book(title="Returned Book", author="Author2", copies_count=1)
    db.add_all([book1, book2])
    await db.commit()
    await db.refresh(book1)
    await db.refresh(book2)

    borrowed_active = BorrowedBook(book_id=book1.id, reader_id=user.id, return_date=None)
    borrowed_returned = BorrowedBook(
        book_id=book2.id, reader_id=user.id, return_date=datetime.now(timezone.utc)
    )
    db.add_all([borrowed_active, borrowed_returned])
    await db.commit()

    active_books = await get_active_borrowed_books(db, user.id)

    # Проверяем, что возвращается только активная книга
    assert len(active_books) == 1
    assert active_books[0].id == book1.id
    assert active_books[0].title == "Active Borrowed Book"
