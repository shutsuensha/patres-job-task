from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

db = Annotated[AsyncSession, Depends(get_db)]
