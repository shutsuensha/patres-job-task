from typing import Optional

from pydantic import BaseModel, EmailStr


class UserIn(BaseModel):
    name: str
    email: EmailStr


class UserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True
