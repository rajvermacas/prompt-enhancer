from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    USER = "USER"
    APPROVER = "APPROVER"


class User(BaseModel):
    id: str
    email: str
    created_at: datetime
    role: UserRole = UserRole.USER


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
