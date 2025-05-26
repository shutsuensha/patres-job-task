import pytest
from app.models.user import User
from app.schemas.user import UserIn, UserPatch
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def clear_books_table(db: AsyncSession):
    await db.execute(delete(User))
    await db.commit()

    yield

    await db.execute(delete(User))
    await db.commit()


async def test_get_user_by_id_success(db: AsyncSession):
    user = User(name="testuser", email="test@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    fetched_user = await get_user_by_id(db, user_id=user.id)

    assert fetched_user.id == user.id
    assert fetched_user.name == user.name
    assert fetched_user.email == user.email


async def test_get_user_by_id_not_found(db: AsyncSession):
    non_existing_id = 9999

    with pytest.raises(HTTPException) as exc_info:
        await get_user_by_id(db, user_id=non_existing_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


async def test_list_users(db: AsyncSession):
    user1 = User(name="user1", email="user1@example.com")
    user2 = User(name="user2", email="user2@example.com")
    db.add_all([user1, user2])
    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)

    users = await list_users(db)

    assert len(users) == 2
    usernames = [user.name for user in users]
    assert "user1" in usernames
    assert "user2" in usernames


async def test_create_user_success(db: AsyncSession):
    user_data = UserIn(name="testuser", email="test@example.com")

    user = await create_user(db, user_data)

    assert user.name == user_data.name
    assert user.email == user_data.email


async def test_create_user_duplicate_email(db: AsyncSession):
    user_data = UserIn(name="testuser", email="test@example.com")

    await create_user(db, user_data)

    with pytest.raises(HTTPException) as exc_info:
        await create_user(db, user_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User with this email already exists"


async def test_update_user_success(db: AsyncSession):
    user = User(name="olduser", email="old@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    update_data = UserIn(name="newuser", email="new@example.com")
    updated = await update_user(db, user_id=user.id, user_data=update_data)

    assert updated.id == user.id
    assert updated.name == "newuser"
    assert updated.email == "new@example.com"


async def test_partial_update_user_success(db: AsyncSession):
    user = User(name="olduser", email="old@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    update_data = UserPatch(name="newuser")
    updated = await update_user(db, user_id=user.id, user_data=update_data)

    assert updated.id == user.id
    assert updated.name == "newuser"
    assert updated.email == "old@example.com"


async def test_update_user_not_found(db: AsyncSession):
    non_existing_id = 9999
    update_data = UserIn(name="newuser", email="new@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await update_user(db, user_id=non_existing_id, user_data=update_data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


async def test_update_user_email_conflict(db: AsyncSession):
    user1 = User(name="user1", email="user1@example.com")
    db.add(user1)

    user2 = User(name="user2", email="user2@example.com")
    db.add(user2)

    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)

    update_data = UserIn(name="user2new", email="user1@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await update_user(db, user_id=user2.id, user_data=update_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User with this email already exists"


async def test_delete_user_success(db: AsyncSession):
    user = User(name="todelete", email="del@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await delete_user(db, user_id=user.id)

    with pytest.raises(HTTPException) as exc_info:
        await get_user_by_id(db, user_id=user.id)

    assert exc_info.value.status_code == 404


async def test_delete_user_not_found(db: AsyncSession):
    non_existing_id = 9999

    with pytest.raises(HTTPException) as exc_info:
        await delete_user(db, user_id=non_existing_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
