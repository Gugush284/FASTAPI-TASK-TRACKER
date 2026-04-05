import json
import os
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import auth
import crud
import database
import models
import schemas

# Create FastAPI application with OpenAPI and Swagger settings.
# Создаём приложение FastAPI с настройками OpenAPI и Swagger.
app = FastAPI(
    title="Task Tracker API",
    description="API для трекера задач с JWT-аутентификацией и ролевой моделью доступа. Swagger UI доступен на /docs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Path where the generated OpenAPI JSON is stored.
# Путь, куда сохраняется сгенерированная OpenAPI JSON схема.
SWAGGER_VOLUME_PATH = Path(os.getenv("SWAGGER_VOLUME_PATH", "./swagger"))


@app.on_event("startup")
def on_startup():
    # Create database tables if they do not exist and save OpenAPI schema to volume.
    # Создаём таблицы базы данных, если их нет, и сохраняем схему OpenAPI в volume.
    if os.getenv("TESTING") != "1":
        models.Base.metadata.create_all(bind=database.engine)

    SWAGGER_VOLUME_PATH.mkdir(parents=True, exist_ok=True)
    openapi_schema = app.openapi()
    with open(SWAGGER_VOLUME_PATH / "openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)


@app.get("/", include_in_schema=False)
def root_redirect():
    # Redirect root URL to Swagger documentation.
    # Перенаправляет корневой URL на Swagger документацию.
    return RedirectResponse(url="/docs")


@app.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Email already registered"},
        status.HTTP_403_FORBIDDEN: {"description": "Only admin can set roles"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def register(user_in: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Register a new user. The first user becomes admin.
    # Регистрирует нового пользователя. Первый пользователь становится администратором.
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user_count = db.query(models.User).count()
    if user_count == 0:
        user_in.role = "admin"
    elif user_in.role != "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can set roles")
    return crud.create_user(db, user_in, auth.get_password_hash(user_in.password))


@app.post(
    "/token",
    response_model=schemas.Token,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Incorrect email or password"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Authenticate the user and return JWT token.
    # Аутентифицирует пользователя и возвращает JWT токен.
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@app.delete(
    "/delete/me",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
    },
)
@app.delete(
    "/users/me",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
    },
)
def delete_current_user(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # Delete current authenticated user.
    # Удаляет текущего аутентифицированного пользователя.
    db.delete(current_user)
    db.commit()
    return None


@app.get(
    "/users/me",
    response_model=schemas.UserOut,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
    },
)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    # Return data for current authenticated user.
    # Возвращает данные текущего аутентифицированного пользователя.
    return current_user


@app.get(
    "/users/",
    response_model=List[schemas.UserOut],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin role required"},
    },
)
def read_all_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_admin)):
    # Return all users, admin-only operation.
    # Возвращает всех пользователей, доступно только администратору.
    return crud.get_all_users(db)


@app.post(
    "/users/",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Email already registered"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin role required"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_admin)):
    # Create a new user by admin.
    # Создаёт нового пользователя администратор.
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(db, user_in, auth.get_password_hash(user_in.password))


@app.patch(
    "/users/{user_id}",
    response_model=schemas.UserOut,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin role required"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def update_user(user_id: int, user_in: schemas.UserUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_admin)):
    # Update an existing user record.
    # Обновляет существующую запись пользователя.
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.update_user(db, user, user_in)


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Admin role required"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
    },
)
def delete_user(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_admin)):
    # Delete a user by ID.
    # Удаляет пользователя по идентификатору.
    if not crud.delete_user_by_id(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None


@app.post(
    "/task/create",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
@app.post(
    "/tasks/",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def create_task(task_in: schemas.TaskCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Create a task for the authenticated user.
    # Создаёт задачу для аутентифицированного пользователя.
    return crud.create_task(db, task_in, current_user.id)


@app.get(
    "/tasks/",
    response_model=List[schemas.TaskOut],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def read_tasks(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Return tasks for the current user or all tasks for moderators/admins.
    # Возвращает задачи текущему пользователю или все задачи для модераторов/админов.
    return crud.get_tasks(db, current_user, skip=skip, limit=limit)


@app.patch(
    "/tasks/{task_id}",
    response_model=schemas.TaskOut,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Moderator or admin role required"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def update_task(task_id: int, task_in: schemas.TaskUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_moderator)):
    # Update a task if the user has permission.
    # Обновляет задачу, если пользователь имеет разрешение.
    task = crud.get_task(db, task_id, current_user)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return crud.update_task(db, task, task_in)


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Moderator or admin role required"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
    },
)
def delete_task(task_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_moderator)):
    # Delete a task if the user has permission.
    # Удаляет задачу, если пользователь имеет разрешение.
    task = crud.get_task(db, task_id, current_user)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    crud.delete_task(db, task)
    return None


@app.post(
    "/projects/",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Project already exists"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def create_project(project_in: schemas.ProjectCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Create a project and attach existing tasks to it.
    # Создаёт проект и прикрепляет к нему существующие задачи.
    if crud.get_project_by_name(db, project_in.name, current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project already exists")

    project = crud.create_project(db, project_in, current_user.id)
    for task_id in project_in.task_ids:
        task = crud.get_task(db, task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with id {task_id} not found")
        task.project_id = project.id
        db.commit()
    db.refresh(project)
    return project


@app.get(
    "/projects/",
    response_model=List[schemas.ProjectOut],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
    },
)
def read_projects(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Return projects visible to the current user.
    # Возвращает проекты, доступные текущему пользователю.
    return crud.get_projects(db, current_user)


@app.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_403_FORBIDDEN: {"description": "Moderator or admin role required"},
        status.HTTP_404_NOT_FOUND: {"description": "Project not found"},
    },
)
def delete_project(project_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.require_moderator)):
    # Delete a project if the user has access.
    # Удаляет проект, если пользователь имеет доступ.
    project = crud.get_project(db, project_id, current_user)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    db.query(models.Task).filter(models.Task.project_id == project_id).update({"project_id": None})
    crud.delete_project(db, project)
    return None


@app.get(
    "/projects/{project_id}/select_tasks",
    response_model=List[schemas.ProjectAlgOut],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Authentication required"},
        status.HTTP_404_NOT_FOUND: {"description": "Project not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation Error"},
    },
)
def select_tasks_greedy(project_id: int, time_limit: int = Query(..., gt=0, description="Максимальное доступное время в минутах"), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Select tasks for a project within a time budget using a greedy algorithm.
    # Выбирает задачи для проекта в рамках заданного времени жадным алгоритмом.
    project = crud.get_project(db, project_id, current_user)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    if not tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

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
