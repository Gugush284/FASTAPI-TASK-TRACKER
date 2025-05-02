from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# --- Пользователь ---


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# --- Токены ---


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- Задачи ---


class TaskBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    time_spent: int


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")


class TaskOut(TaskBase):
    id: int
    status: str
    created_at: datetime
    owner_id: int

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    task_ids: List[int] = []


class ProjectOut(BaseModel):
    id: int
    name: str
    tasks: List[TaskOut] = []

    class Config:
        orm_mode = True


class ProjectAlgOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    time_spent: int

    class Config:
        orm_mode = True
