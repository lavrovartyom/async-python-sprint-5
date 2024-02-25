from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import get_session
from models import UserModel

# Секретный ключ для создания JWT токена
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Для хеширования и проверки паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


async def authenticate_user(db: AsyncSession, username: str, password: str):
    async with db as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalars().first()
        if user and pwd_context.verify(password, user.password):
            return user
    return None


async def get_current_user(
    db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    async with db as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
        return user
