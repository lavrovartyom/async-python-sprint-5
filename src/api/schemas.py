from pydantic import BaseModel


class FileUploadRequest(BaseModel):
    path: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    id: int
