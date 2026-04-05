from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# Base user schema with common fields.
# Базовая схема пользователя с общими полями.
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    # User registration payload.
    # Данные для регистрации пользователя.
    password: str = Field(..., min_length=6)
    role: str = Field("viewer", pattern="^(admin|moderator|viewer)$")


class UserOut(UserBase):
    # User representation returned from API.
    # Представление пользователя, возвращаемое API.
    id: int
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    # Fields allowed for user updates.
    # Поля, разрешённые для обновления пользователя.
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|moderator|viewer)$")


class Token(BaseModel):
    # JWT access token response.
    # Ответ с JWT токеном доступа.
    access_token: str
    token_type: str


class TokenData(BaseModel):
    # Data extracted from token payload.
    # Данные, извлечённые из полезной нагрузки токена.
    email: Optional[str] = None


class TaskBase(BaseModel):
    # Common task fields for create/update operations.
    # Общие поля задачи для создания/обновления.
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    time_spent: int = Field(..., ge=0)


class TaskCreate(TaskBase):
    # Task creation payload.
    # Данные для создания задачи.
    pass


class TaskUpdate(BaseModel):
    # Fields allowed for task updates.
    # Поля, разрешённые для обновления задачи.
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")
    time_spent: Optional[int] = Field(None, ge=0)


class TaskOut(TaskBase):
    # Response schema for task objects.
    # Схема ответа для объектов задач.
    id: int
    status: str
    created_at: datetime
    owner_id: int
    project_id: Optional[int] = None

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    # Common project fields.
    # Общие поля проекта.
    name: str


class ProjectCreate(ProjectBase):
    # Payload to create a project with task IDs.
    # Данные для создания проекта с идентификаторами задач.
    task_ids: List[int] = Field(default_factory=list)


class ProjectOut(BaseModel):
    # Response schema for project objects.
    # Схема ответа для объектов проекта.
    id: int
    name: str
    tasks: List[TaskOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


class ProjectAlgOut(BaseModel):
    # Output schema for task selection algorithm.
    # Схема результата для алгоритма выбора задач.
    id: int
    title: str
    description: Optional[str]
    time_spent: int

    class Config:
        orm_mode = True
