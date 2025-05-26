from pydantic import BaseModel, EmailStr


class LibrarianIn(BaseModel):
    email: EmailStr
    password: str


class LibrarianOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
