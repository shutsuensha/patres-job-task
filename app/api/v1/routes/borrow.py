from app.dependencies.auth import librarian_id
from app.dependencies.db import db
from app.schemas.book import BookOut
from app.schemas.borrow import BorrowedBookOut, BorrowRequest
from app.services.borrow_service import borrow_book, get_active_borrowed_books, return_book
from fastapi import APIRouter, status

router = APIRouter(prefix="/borrow", tags=["borrow"])


@router.post("/", response_model=BorrowedBookOut, status_code=status.HTTP_201_CREATED)
async def borrow_book_endpoint(
    data: BorrowRequest, session: db, librarian_id: librarian_id
) -> BorrowedBookOut:
    return await borrow_book(session, data)


@router.post("/return", status_code=status.HTTP_200_OK)
async def return_borrowed_book(data: BorrowRequest, session: db, librarian_id: librarian_id):
    await return_book(session, data)
    return {"detail": "Book returned successfully"}


@router.get("/{user_id}", response_model=list[BookOut], status_code=status.HTTP_200_OK)
async def list_borrowed_books_by_user(
    user_id: int,
    session: db,
    librarian_id: librarian_id,
) -> list[BookOut]:
    return await get_active_borrowed_books(session, user_id)
