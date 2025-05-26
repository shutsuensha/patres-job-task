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


async def test_read_books_with_auth(ac: AsyncClient, db: AsyncSession):
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

    book1 = Book(title="Book One", author="Author A")
    book2 = Book(title="Book Two", author="Author B")
    db.add_all([book1, book2])
    await db.commit()
    await db.refresh(book1)
    await db.refresh(book2)

    response = await ac.get("/books/", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    titles = [book["title"] for book in data]
    assert "Book One" in titles
    assert "Book Two" in titles


async def test_get_book_by_id_with_auth(ac: AsyncClient, db: AsyncSession):
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

    book = Book(title="Test Book", author="Test Author")
    db.add(book)
    await db.commit()
    await db.refresh(book)

    response = await ac.get(f"/books/{book.id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == book.id
    assert data["title"] == book.title
    assert data["author"] == book.author


@pytest.mark.parametrize(
    "title, author, publication_year, isbn, copies_count, status_code",
    [
        ("title 1", "author 1", 2000, "123124124", 5, 201),
        ("title 2", "author 2", None, None, None, 422),
        ("title 3", None, None, None, 4, 422),
    ],
)
async def test_create_new_book_auth(
    ac: AsyncClient,
    db: AsyncSession,
    title,
    author,
    publication_year,
    isbn,
    copies_count,
    status_code,
):
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

    book_payload = {
        "title": title,
        "author": author,
        "publication_year": publication_year,
        "isbn": isbn,
        "copies_count": copies_count,
    }

    response = await ac.post("/books/", json=book_payload, headers=headers)
    assert response.status_code == status_code

    if response.status_code != 201:
        return

    data = response.json()
    assert data["title"] == book_payload["title"]
    assert data["author"] == book_payload["author"]

    result = await db.execute(select(Book).where(Book.title == book_payload["title"]))
    book = result.scalar_one_or_none()
    assert book is not None
    assert book.author == book_payload["author"]


async def test_update_existing_book_auth(ac: AsyncClient, db: AsyncSession):
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

    book = Book(title="Old Title", author="Old Author")
    db.add(book)
    await db.commit()
    await db.refresh(book)

    update_payload = {"title": "Updated Title", "author": "Updated Author"}

    response = await ac.put(f"/books/{book.id}", json=update_payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == update_payload["title"]
    assert data["author"] == update_payload["author"]

    await db.refresh(book)

    result = await db.execute(select(Book).where(Book.id == book.id))
    updated_book = result.scalar_one_or_none()

    assert updated_book.title == update_payload["title"]
    assert updated_book.author == update_payload["author"]


async def test_partial_update_existing_book_auth(ac: AsyncClient, db: AsyncSession):
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

    book = Book(title="Original Title", author="Original Author")
    db.add(book)
    await db.commit()
    await db.refresh(book)

    patch_payload = {"author": "Updated Author"}

    response = await ac.patch(f"/books/{book.id}", json=patch_payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Original Title"
    assert data["author"] == patch_payload["author"]

    await db.refresh(book)

    result = await db.execute(select(Book).where(Book.id == book.id))
    updated_book = result.scalar_one_or_none()
    assert updated_book is not None
    assert updated_book.title == "Original Title"
    assert updated_book.author == patch_payload["author"]


async def test_delete_existing_book_auth(ac: AsyncClient, db: AsyncSession):
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

    book = Book(title="To Be Deleted", author="Author")
    db.add(book)
    await db.commit()
    await db.refresh(book)

    response = await ac.delete(f"/books/{book.id}", headers=headers)
    assert response.status_code == 204

    result = await db.execute(select(Book).where(Book.id == book.id))
    deleted_book = result.scalar_one_or_none()
    assert deleted_book is None
