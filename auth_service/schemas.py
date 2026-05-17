from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    participant = "participant"
    admin = "admin"


class UserCreate(BaseModel):
    """Register ke liye — role field optional hai (backend force karta hai sahi role)."""
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"