from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship

from database import Base


class RoleEnum(str, PyEnum):
    # Define user roles that control authorization.
    # Определяем роли пользователей для контроля доступа.
    admin = "admin"
    moderator = "moderator"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    # User entity fields and relationships.
    # Поля и связи сущности пользователя.
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    # Task entity fields including ownership and project link.
    # Поля задачи, включая связь с владельцем и проектом.
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # статус задачи: pending, in_progress, done
    created_at = Column(DateTime, default=datetime.utcnow)
    time_spent = Column(Integer, default=0, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    owner = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")


class Project(Base):
    __tablename__ = "projects"

    # Project entity with owner and task list.
    # Сущность проекта с владельцем и списком задач.
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")

    tasks = relationship("Task", back_populates="project")
