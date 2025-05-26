import pytest
from app.core.security import hash_password
from app.models.book import Book
from app.models.borrowed_book import BorrowedBook
from app.models.librarian import Librarian
from app.models.user import User
from fastapi import status
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


async def test_register_success(ac: AsyncClient, db: AsyncSession):
    payload = {"email": "test@example.com", "password": "securepassword"}

    response = await ac.post("/librarians/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "password" not in data

    result = await db.execute(select(Librarian).where(Librarian.email == payload["email"]))
    librarian = result.scalar_one_or_none()
    assert librarian is not None


async def test_register_email_conflict(ac: AsyncClient, db: AsyncSession):
    existing_email = "test@example.com"
    librarian = Librarian(email=existing_email, password=hash_password("somepassword"))
    db.add(librarian)
    await db.commit()

    payload = {"email": existing_email, "password": "securepassword"}
    response = await ac.post("/librarians/register", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"] == "Email already registered"


async def test_login_success(ac: AsyncClient, db: AsyncSession):
    email = "test_login@example.com"
    raw_password = "securepassword"
    hashed = hash_password(raw_password)
    librarian = Librarian(email=email, password=hashed)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_data = {"username": email, "password": raw_password}

    response = await ac.post("/librarians/login", data=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_login_fail_wrong_password(ac: AsyncClient, db: AsyncSession):
    email = "testuser2@example.com"
    hashed_password = hash_password("correctpassword")
    librarian = Librarian(email=email, password=hashed_password)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_data = {
        "username": email,
        "password": "wrongpassword",
    }

    response = await ac.post("/librarians/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_fail_user_not_found(ac: AsyncClient, db: AsyncSession):
    email = "testuser2@example.com"
    hashed_password = hash_password("correctpassword")
    librarian = Librarian(email=email, password=hashed_password)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    login_data = {
        "username": "notfound@example.com",
        "password": "correctpassword",
    }

    response = await ac.post("/librarians/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
