from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text

from db import get_session
from models import File, User
from util.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
)

from .schemas import UserCreate, UserResponse

router = APIRouter()


@router.get("/files/")
async def get_files(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    async with db as session:
        result = await session.execute(
            select(File).where(File.owner_id == current_user.id)
        )
        files = result.scalars().all()
        return {
            "account_id": current_user.id,
            "files": [
                {
                    "id": file.id,
                    "name": file.name,
                    "created_at": file.created_at.isoformat(),
                    "path": file.path,
                    "size": file.size,
                    "is_downloadable": file.is_downloadable,
                }
                for file in files
            ],
        }


@router.get("/ping")
async def ping(db: AsyncSession = Depends(get_session)):
    start_time = datetime.now()
    try:
        await db.execute(text("SELECT 1"))
        end_time = datetime.now()
        db_response_time = (end_time - start_time).total_seconds()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"db": db_response_time}


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
