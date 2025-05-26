from app.dependencies.auth import form_data
from app.dependencies.db import db
from app.schemas.librarian import LibrarianIn, LibrarianOut, TokenOut
from app.services.librarian_service import authenticate_librarian, register_librarian
from fastapi import APIRouter, status

router = APIRouter(prefix="/librarians", tags=["librarians"])


@router.post("/register", response_model=LibrarianOut, status_code=status.HTTP_201_CREATED)
async def register(data: LibrarianIn, session: db) -> LibrarianOut:
    return await register_librarian(data, session)


@router.post("/login", response_model=TokenOut, status_code=status.HTTP_200_OK)
async def login(form_data: form_data, session: db) -> TokenOut:
    return await authenticate_librarian(form_data.username, form_data.password, session)
