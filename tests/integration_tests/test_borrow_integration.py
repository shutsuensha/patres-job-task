from datetime import datetime, timezone

import pytest
from app.core.security import hash_password
from app.models.book import Book
from app.models.borrowed_book import BorrowedBook
from app.models.librarian import Librarian
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def clear_tables(db: AsyncSession):
    await db.execute(delete(BorrowedBook))
    await db.execute(delete(Librarian))
    await db.execute(delete(User))
    await db.execute(delete(Book))
    await db.commit()

    yield

    await db.execute(delete(BorrowedBook))
    await db.execute(delete(Librarian))
    await db.execute(delete(User))
    await db.execute(delete(Book))
    await db.commit()


async def test_borrow_book_auth(ac: AsyncClient, db: AsyncSession):
    email = "librarian@example.com"
    password = "strongpassword"
    librarian = Librarian(email=email, password=hash_password(password))
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_data = {
        "username": email,
        "password": password,
    }
    login_resp = await ac.post("/librarians/login", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = User(name="Reader", email="reader@example.com")
    book_copies_count = 2
    book = Book(title="Test Book", author="Author", copies_count=book_copies_count)
    db.add_all([user, book])
    await db.commit()
    await db.refresh(user)
    await db.refresh(book)

    borrow_payload = {"book_id": book.id, "reader_id": user.id}

    response = await ac.post("/borrow/", json=borrow_payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["book_id"] == book.id
    assert data["reader_id"] == user.id

    await db.refresh(book)

    result = await db.execute(select(Book).where(Book.id == book.id))
    updated_book = result.scalar_one()
    assert updated_book.copies_count == book_copies_count - 1

    result = await db.execute(
        select(BorrowedBook).where(
            BorrowedBook.book_id == book.id,
            BorrowedBook.reader_id == user.id,
            BorrowedBook.return_date.is_(None),
        )
    )
    borrowed_book = result.scalar_one_or_none()
    assert borrowed_book is not None


async def test_return_borrowed_book_auth(ac: AsyncClient, db: AsyncSession):
    email = "librarian@example.com"
    password = "strongpassword"
    librarian = Librarian(email=email, password=hash_password(password))
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_resp = await ac.post("/librarians/login", data={"username": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = User(name="Reader", email="reader@example.com")
    book_copies_count = 1
    book = Book(title="Test Book", author="Author", copies_count=book_copies_count)
    db.add_all([user, book])
    await db.commit()
    await db.refresh(user)
    await db.refresh(book)

    borrowed = BorrowedBook(
        book_id=book.id, reader_id=user.id, borrow_date=datetime.now(timezone.utc)
    )
    db.add(borrowed)
    await db.commit()
    await db.refresh(borrowed)

    payload = {"book_id": book.id, "reader_id": user.id}

    response = await ac.post("/borrow/return", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"detail": "Book returned successfully"}

    await db.refresh(book)

    result = await db.execute(select(Book).where(Book.id == book.id))
    updated_book = result.scalar_one()
    assert updated_book.copies_count == book_copies_count + 1

    await db.refresh(borrowed)
    result = await db.execute(
        select(BorrowedBook).where(
            BorrowedBook.book_id == book.id, BorrowedBook.reader_id == user.id
        )
    )
    borrowed_record = result.scalar_one()
    assert borrowed_record.return_date is not None


async def test_list_borrowed_books_by_user_auth(ac: AsyncClient, db: AsyncSession):
    email = "librarian@example.com"
    password = "strongpassword"
    librarian = Librarian(email=email, password=hash_password(password))
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_resp = await ac.post("/librarians/login", data={"username": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = User(name="Reader", email="reader@example.com")
    book1 = Book(title="Book One", author="Author 1", copies_count=5)
    book2 = Book(title="Book Two", author="Author 2", copies_count=3)
    db.add_all([user, book1, book2])
    await db.commit()
    await db.refresh(user)
    await db.refresh(book1)
    await db.refresh(book2)

    borrowed1 = BorrowedBook(
        book_id=book1.id, reader_id=user.id, borrow_date=datetime.now(timezone.utc)
    )
    borrowed2 = BorrowedBook(
        book_id=book2.id, reader_id=user.id, borrow_date=datetime.now(timezone.utc)
    )
    db.add_all([borrowed1, borrowed2])
    await db.commit()

    response = await ac.get(f"/borrow/{user.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    titles = {book["title"] for book in data}
    assert book1.title in titles
    assert book2.title in titles
