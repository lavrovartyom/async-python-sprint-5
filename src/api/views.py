import os
import typing as t
from datetime import datetime, timedelta
from uuid import uuid4

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text

from db import get_session
from models import FileModel, UserModel
from util.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
)

from .schemas import FileUploadRequest, UserCreate, UserResponse

router = APIRouter()


@router.get("/files/download")
async def download_file(
    path: t.Optional[str] = None,
    file_meta_id: t.Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    if not path and not file_meta_id:
        raise HTTPException(
            status_code=400, detail="Path or file_meta_id must be provided"
        )

    file_record = None
    if file_meta_id:
        result = await db.execute(select(FileModel).where(FileModel.id == file_meta_id))
        file_record = result.scalars().first()
    elif path:
        result = await db.execute(select(FileModel).where(FileModel.path == path))
        file_record = result.scalars().first()

    if not file_record or file_record.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    file_path = file_record.path
    try:
        return Response(
            content=open(file_path, "rb").read(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_record.name}"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found on server")


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: FileUploadRequest = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    file_id = str(uuid4())
    file_name = file.filename
    file_path = os.path.join(request.path, file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        async with aiofiles.open(file_path, "wb") as buffer:
            while True:
                content = await file.read(1024 * 1024)
                if not content:
                    break
                await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    file_model = FileModel(
        id=file_id,
        name=file_name,
        created_at=datetime.utcnow(),
        path=file_path,
        size=os.path.getsize(file_path),
        is_downloadable=True,
        owner_id=current_user.id,
    )
    db.add(file_model)
    await db.commit()

    return {
        "id": file_id,
        "name": file_name,
        "created_at": file_model.created_at.isoformat(),
        "path": file_path,
        "size": file_model.size,
        "is_downloadable": file_model.is_downloadable,
    }


@router.get("/files/")
async def get_files(
    db: AsyncSession = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    async with db as session:
        result = await session.execute(
            select(FileModel).where(FileModel.owner_id == current_user.id)
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
        select(UserModel).where(UserModel.username == user_create.username)
    )
    db_user = db_user.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    hashed_password = bcrypt.hash(user_create.password)
    new_user = UserModel(username=user_create.username, password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"username": new_user.username, "id": new_user.id}
