from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError

from app.core.security import encode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/librarians/login")


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        data = encode_token(token)
        user_id = data.get("user_id")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user_id


librarian_id = Annotated[int, Depends(get_current_user_id)]
form_data = Annotated[OAuth2PasswordRequestForm, Depends()]
