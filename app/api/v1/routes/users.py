from app.dependencies.auth import librarian_id
from app.dependencies.db import db
from app.schemas.user import UserIn, UserOut, UserPatch
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from fastapi import APIRouter, status

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut], status_code=status.HTTP_200_OK)
async def read_users(session: db, librarian_id: librarian_id) -> list[UserOut]:
    return await list_users(session)


@router.get("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, session: db, librarian_id: librarian_id) -> UserOut:
    return await get_user_by_id(session, user_id)


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_new_user(user: UserIn, session: db, librarian_id: librarian_id) -> UserOut:
    return await create_user(session, user)


@router.put("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_existing_user(
    user_id: int, user: UserIn, session: db, librarian_id: librarian_id
) -> UserOut:
    return await update_user(session, user_id, user)


@router.patch("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def partial_update_existing_user(
    user_id: int, user: UserPatch, session: db, librarian_id: librarian_id
) -> UserOut:
    return await update_user(session, user_id, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(user_id: int, session: db, librarian_id: librarian_id):
    await delete_user(session, user_id)
