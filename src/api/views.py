from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from db import get_session

router = APIRouter()


class UrlCreate(BaseModel):
    url: HttpUrl


class UrlResponse(BaseModel):
    short_id: str


@router.get(path="/")
async def ping_database(db: AsyncSession = Depends(get_session)):
    return JSONResponse("Привет мир!!!")
