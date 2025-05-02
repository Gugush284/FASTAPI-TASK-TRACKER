import os
from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import auth
import crud
import database
import models
import schemas

# Создаем таблицы в БД (если их еще нет)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Task Tracker API")

# --- Эндпоинты ---


# Регистрация нового пользователя
@app.post(
    "/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED
)
def register(user_in: schemas.UserCreate, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_in.password)
    new_user = models.User(email=user_in.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Вход и получение токена
@app.post("/token", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.delete("/delete/me", status_code=status.HTTP_200_OK)
def delete_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Удаляем пользователя
    db.delete(user)
    db.commit()
    return None


# Получение информации о текущем пользователе
@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --- CRUD для задач ---


# Создание задачи
@app.post(
    "/task/create", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED
)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = models.Task(
        title=task_in.title,
        description=task_in.description,
        owner_id=current_user.id,
        status="pending",
        created_at=datetime.utcnow(),
        time_spent=task_in.time_spent,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Получение списка задач текущего пользователя
@app.get("/tasks/", response_model=List[schemas.TaskOut])
def read_tasks(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    tasks = db.query(models.Task).filter(models.Task.owner_id == current_user.id).all()
    return tasks


# Удаление задачи (только владелец)
@app.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.owner_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_id = task.project_id

    db.delete(task)
    db.commit()

    if project_id:
        if (
            db.query(models.Task).filter(models.Task.project_id == project_id).count()
            == 0
        ):
            project = (
                db.query(models.Project).filter(models.Project.id == project_id).first()
            )
            if project:
                db.delete(project)
                db.commit()

    return None


@app.post(
    "/projects/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED
)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        # 1. Create the project
        db_project = models.Project(name=project_in.name, owner_id=current_user.id)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        # 2. Associate tasks within a transaction
        for task_id in project_in.task_ids:
            task = db.query(models.Task).filter(models.Task.id == task_id).first()
            if task:
                task.project_id = db_project.id
                db.commit()  # Commit within the loop to avoid losing individual task assignments
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found",
                )
        db.refresh(db_project)  # Refresh to get updated task associations
        return db_project

    except HTTPException as e:
        db.rollback()
        db.delete(db_project)
        db.commit()
        raise e

    except Exception as e:
        db.rollback()
        if "db_project" in locals():
            db.delete(db_project)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(database.get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Обнуляем project_id у связанных задач
    db.query(models.Task).filter(models.Task.project_id == project_id).update(
        {"project_id": None}
    )
    db.delete(project)
    db.commit()
    return None


@app.get(
    "/projects/{project_id}/select_tasks", response_model=List[schemas.ProjectAlgOut]
)
def select_tasks_greedy(
    project_id: int,
    time_limit: int = Query(
        ..., gt=0, description="Максимальное доступное время в минутах"
    ),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Проверяем, что проект принадлежит текущему пользователю
    project = (
        db.query(models.Project)
        .filter(
            models.Project.id == project_id, models.Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Получаем все задачи проекта
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()

    # Сортируем задачи по времени выполнения
    tasks_sorted = sorted(tasks, key=lambda t: t.time_spent)

    selected_tasks = []
    total_time = 0

    for task in tasks_sorted:
        if total_time + task.time_spent <= time_limit:
            selected_tasks.append(task)
            total_time += task.time_spent
        else:
            break

    return selected_tasks
