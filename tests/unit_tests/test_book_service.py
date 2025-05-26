import pytest
from app.models.book import Book
from app.schemas.book import BookIn, BookPatch
from app.services.book_service import (
    create_book,
    delete_book,
    get_book_by_id,
    list_books,
    update_book,
)
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def clear_books_table(db: AsyncSession):
    await db.execute(delete(Book))
    await db.commit()

    yield

    await db.execute(delete(Book))
    await db.commit()


async def test_get_book_by_id_success(db: AsyncSession):
    fake_book = Book(title="Test Book", author="Test Author")
    db.add(fake_book)
    await db.commit()
    await db.refresh(fake_book)

    book = await get_book_by_id(db, book_id=fake_book.id)

    assert book.id == fake_book.id
    assert book.title == fake_book.title
    assert book.author == fake_book.author


async def test_get_book_by_id_not_found(db: AsyncSession):
    non_existing_id = 9999

    with pytest.raises(HTTPException) as exc_info:
        await get_book_by_id(db, book_id=non_existing_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book not found"


async def test_list_books(db: AsyncSession):
    book1 = Book(title="Book 1", author="Author 1")
    book2 = Book(title="Book 2", author="Author 2")
    db.add_all([book1, book2])
    await db.commit()

    await db.refresh(book1)
    await db.refresh(book2)

    books = await list_books(db)

    assert len(books) == 2
    titles = [book.title for book in books]
    assert "Book 1" in titles
    assert "Book 2" in titles


async def test_create_book_success(db: AsyncSession):
    book_data = BookIn(title="Clean Code", author="Robert C. Martin", isbn="9780132350884")

    book = await create_book(db, book_data)

    assert book.title == book_data.title
    assert book.author == book_data.author
    assert book.isbn == book_data.isbn


async def test_create_book_duplicate_isbn(db: AsyncSession):
    book_data = BookIn(title="Clean Code", author="Robert C. Martin", isbn="9780132350884")

    await create_book(db, book_data)

    with pytest.raises(HTTPException) as exc_info:
        await create_book(db, book_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Book with this ISBN already exists"


async def test_update_book_success(db: AsyncSession):
    original = Book(title="Old Title", author="Old Author")
    db.add(original)
    await db.commit()
    await db.refresh(original)

    new_data = BookIn(title="New Title", author="New Author")
    updated = await update_book(db, book_id=original.id, book_data=new_data)

    assert updated.id == original.id
    assert updated.title == "New Title"
    assert updated.author == "New Author"


async def test_partial_update_book_success(db: AsyncSession):
    original = Book(title="Old Title", author="Old Author")
    db.add(original)
    await db.commit()
    await db.refresh(original)

    new_data = BookPatch(isbn="123")
    updated = await update_book(db, book_id=original.id, book_data=new_data)

    assert updated.id == original.id
    assert updated.title == original.title
    assert updated.author == original.author
    assert updated.isbn == "123"


async def test_update_book_not_found(db: AsyncSession):
    non_existing_id = 9999
    new_data = BookIn(title="New Title", author="New Author")

    with pytest.raises(HTTPException) as exc_info:
        await update_book(db, book_id=non_existing_id, book_data=new_data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book not found"


async def test_update_book_isbn_conflict(db: AsyncSession):
    book1 = Book(title="Book One", author="Author A", isbn="111")
    db.add(book1)

    book2 = Book(title="Book Two", author="Author B", isbn="222")
    db.add(book2)

    await db.commit()
    await db.refresh(book1)
    await db.refresh(book2)

    new_data = BookIn(title="Updated", author="Updated", isbn="111")

    with pytest.raises(HTTPException) as exc_info:
        await update_book(db, book_id=book2.id, book_data=new_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Book with this ISBN already exists"


async def test_delete_book_success(db: AsyncSession):
    book = Book(title="To Delete", author="Someone", isbn="000")
    db.add(book)
    await db.commit()
    await db.refresh(book)

    await delete_book(db, book_id=book.id)

    with pytest.raises(HTTPException) as exc_info:
        await get_book_by_id(db, book_id=book.id)

    assert exc_info.value.status_code == 404


async def test_delete_book_not_found(db: AsyncSession):
    non_existing_id = 9999

    with pytest.raises(HTTPException) as exc_info:
        await delete_book(db, book_id=non_existing_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Book not found"
