from fastapi import APIRouter

from .routes import books, borrow, librarians, users

api_router = APIRouter()
api_router.include_router(librarians.router)
api_router.include_router(users.router)
api_router.include_router(books.router)
api_router.include_router(borrow.router)
