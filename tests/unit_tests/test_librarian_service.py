import pytest
from app.core.security import hash_password, verify_password
from app.models.librarian import Librarian
from app.schemas.librarian import LibrarianIn, TokenOut
from app.services.librarian_service import authenticate_librarian, register_librarian
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def clear_books_table(db: AsyncSession):
    await db.execute(delete(Librarian))
    await db.commit()

    yield

    await db.execute(delete(Librarian))
    await db.commit()


async def test_register_librarian_success(db: AsyncSession):
    data = LibrarianIn(email="lib@example.com", password="securepass")

    librarian = await register_librarian(data, db)

    assert librarian.email == data.email
    assert librarian.password != data.password
    assert verify_password(data.password, librarian.password)


async def test_register_librarian_duplicate_email(db):
    data = LibrarianIn(email="lib@example.com", password="securepass")

    await register_librarian(data, db)

    with pytest.raises(HTTPException) as exc_info:
        await register_librarian(data, db)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Email already registered"


async def test_authenticate_librarian_success(db: AsyncSession):
    password = "correctpassword"
    hashed = hash_password(password)
    librarian = Librarian(email="lib@example.com", password=hashed)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    token_out = await authenticate_librarian(email=librarian.email, password=password, session=db)

    assert isinstance(token_out, TokenOut)
    assert token_out.access_token is not None


async def test_authenticate_librarian_invalid_email(db: AsyncSession):
    password = "correctpassword"
    hashed = hash_password(password)
    librarian = Librarian(email="lib@example.com", password=hashed)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    email = "nonexistent@example.com"
    password = "any_pacorrectpasswordssword"

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_librarian(email=email, password=password, session=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials"


async def test_authenticate_librarian_invalid_password(db: AsyncSession):
    password = "correctpassword"
    hashed = hash_password(password)
    librarian = Librarian(email="lib@example.com", password=hashed)
    db.add(librarian)
    await db.commit()
    await db.refresh(librarian)

    email = "lib@example.com"
    password = "any_pacorrectpasswordssword"

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_librarian(email=email, password=password, session=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials"
