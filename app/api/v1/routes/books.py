from app.dependencies.auth import librarian_id
from app.dependencies.db import db
from app.schemas.book import BookIn, BookOut, BookPatch
from app.services.book_service import (
    create_book,
    delete_book,
    get_book_by_id,
    list_books,
    update_book,
)
from fastapi import APIRouter, status

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=list[BookOut], status_code=status.HTTP_200_OK)
async def read_books(session: db, librarian_id: librarian_id) -> list[BookOut]:
    return await list_books(session)


@router.get("/{book_id}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def get_book(book_id: int, session: db, librarian_id: librarian_id) -> BookOut:
    return await get_book_by_id(session, book_id)


@router.post("/", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_new_book(book: BookIn, session: db, librarian_id: librarian_id) -> BookOut:
    return await create_book(session, book)


@router.put("/{book_id}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def update_existing_book(
    book_id: int, book: BookIn, session: db, librarian_id: librarian_id
) -> BookOut:
    return await update_book(session, book_id, book)


@router.patch("/{book_id}", response_model=BookOut, status_code=status.HTTP_200_OK)
async def partial_update_existing_book(
    book_id: int, book: BookPatch, session: db, librarian_id: librarian_id
) -> BookOut:
    return await update_book(session, book_id, book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_book(book_id: int, session: db, librarian_id: librarian_id):
    await delete_book(session, book_id)
