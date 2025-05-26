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


async def test_read_users_auth(ac: AsyncClient, db: AsyncSession):
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

    users = [
        User(name="User One", email="user1@example.com"),
        User(name="User Two", email="user2@example.com"),
    ]
    db.add_all(users)
    await db.commit()

    response = await ac.get("/users/", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    emails = [user["email"] for user in data]
    assert "user1@example.com" in emails
    assert "user2@example.com" in emails


async def test_get_user_by_id_auth(ac: AsyncClient, db: AsyncSession):
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

    user = User(name="Test User", email="testuser@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = await ac.get(f"/users/{user.id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["name"] == user.name


async def test_create_new_user_auth(ac: AsyncClient, db: AsyncSession):
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

    new_user_data = {"name": "New User", "email": "newuser@example.com"}

    response = await ac.post("/users/", json=new_user_data, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == new_user_data["email"]
    assert data["name"] == new_user_data["name"]

    # Проверяем, что пользователь создался в базе
    result = await db.execute(select(User).where(User.id == data["id"]))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == new_user_data["email"]
    assert user.name == new_user_data["name"]


async def test_update_existing_user_auth(ac: AsyncClient, db: AsyncSession):
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

    user = User(name="Old Name", email="olduser@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    update_payload = {"name": "Updated Name", "email": "updateduser@example.com"}

    response = await ac.put(f"/users/{user.id}", json=update_payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["email"] == update_payload["email"]

    await db.refresh(user)

    result = await db.execute(select(User).where(User.id == user.id))
    updated_user = result.scalar_one_or_none()
    assert updated_user is not None
    assert updated_user.name == update_payload["name"]
    assert updated_user.email == update_payload["email"]


async def test_partial_update_existing_user_auth(ac: AsyncClient, db: AsyncSession):
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

    user = User(name="Old Name", email="olduser@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    patch_payload = {"name": "Partially Updated Name"}

    response = await ac.patch(f"/users/{user.id}", json=patch_payload, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == patch_payload["name"]
    assert data["email"] == user.email

    await db.refresh(user)

    result = await db.execute(select(User).where(User.id == user.id))
    updated_user = result.scalar_one_or_none()
    assert updated_user is not None
    assert updated_user.name == patch_payload["name"]
    assert updated_user.email == user.email


async def test_delete_existing_user_auth(ac: AsyncClient, db: AsyncSession):
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

    user = User(name="User To Delete", email="todelete@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response = await ac.delete(f"/users/{user.id}", headers=headers)
    assert response.status_code == 204

    result = await db.execute(select(User).where(User.id == user.id))
    deleted_user = result.scalar_one_or_none()
    assert deleted_user is None
