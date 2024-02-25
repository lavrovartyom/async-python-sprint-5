from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import get_session
from models import User
from util.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
)

from .schemas import UserCreate, UserResponse

router = APIRouter()


@router.post("/auth")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_create: UserCreate, db: AsyncSession = Depends(get_session)
):
    db_user = await db.execute(
        select(User).where(User.username == user_create.username)
    )
    db_user = db_user.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    hashed_password = bcrypt.hash(user_create.password)
    new_user = User(username=user_create.username, password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"username": new_user.username, "id": new_user.id}
