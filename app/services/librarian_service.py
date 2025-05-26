from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token, hash_password, verify_password
from app.models.librarian import Librarian
from app.schemas.librarian import LibrarianIn, TokenOut


async def register_librarian(data: LibrarianIn, session: AsyncSession) -> Librarian:
    result = await session.execute(select(Librarian).where(Librarian.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    new_librarian = Librarian(email=data.email, password=hash_password(data.password))
    session.add(new_librarian)

    await session.commit()
    await session.refresh(new_librarian)

    return new_librarian


async def authenticate_librarian(email: str, password: str, session: AsyncSession) -> TokenOut:
    result = await session.execute(select(Librarian).where(Librarian.email == email))
    librarian = result.scalar_one_or_none()

    if not librarian or not verify_password(password, librarian.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"user_id": librarian.id})
    return TokenOut(access_token=token)
