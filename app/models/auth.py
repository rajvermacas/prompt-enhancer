from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    created_at: datetime


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Session(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
