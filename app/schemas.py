from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = Field("viewer", pattern="^(admin|moderator|viewer)$")


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|moderator|viewer)$")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class TaskBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    time_spent: int = Field(..., ge=0)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")
    time_spent: Optional[int] = Field(None, ge=0)


class TaskOut(TaskBase):
    id: int
    status: str
    created_at: datetime
    owner_id: int
    project_id: Optional[int] = None

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    task_ids: List[int] = Field(default_factory=list)


class ProjectOut(BaseModel):
    id: int
    name: str
    tasks: List[TaskOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


class ProjectAlgOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    time_spent: int

    class Config:
        orm_mode = True
