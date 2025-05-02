from typing import List, Optional

from sqlalchemy.orm import Session

import models
import schemas

# --- Пользователи ---


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(
    db: Session, user_in: schemas.UserCreate, hashed_password: str
) -> models.User:
    db_user = models.User(email=user_in.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Задачи ---


def create_task(db: Session, task_in: schemas.TaskCreate, owner_id: int) -> models.Task:
    db_task = models.Task(
        title=task_in.title,
        description=task_in.description,
        owner_id=owner_id,
        status="pending",
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> List[models.Task]:
    return (
        db.query(models.Task)
        .filter(models.Task.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_task(db: Session, task_id: int, owner_id: int) -> Optional[models.Task]:
    return (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.owner_id == owner_id)
        .first()
    )


def update_task(
    db: Session, task: models.Task, task_in: schemas.TaskUpdate
) -> models.Task:
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
