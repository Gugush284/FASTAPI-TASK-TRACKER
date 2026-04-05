from typing import List, Optional

from sqlalchemy.orm import Session

import models
import schemas


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    # Find a user by their email address.
    # Находит пользователя по электронной почте.
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    # Find a user by their database ID.
    # Находит пользователя по идентификатору в базе данных.
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_in: schemas.UserCreate, hashed_password: str) -> models.User:
    # Create a new user and save it to the database.
    # Создаёт нового пользователя и сохраняет его в базу данных.
    db_user = models.User(email=user_in.email, hashed_password=hashed_password, role=user_in.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_users(db: Session) -> List[models.User]:
    # Return all users for admin management.
    # Возвращает всех пользователей для управления админом.
    return db.query(models.User).all()


def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate) -> models.User:
    # Update user fields from the incoming schema.
    # Обновляет поля пользователя из входящей схемы.
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user_by_id(db: Session, user_id: int) -> bool:
    # Delete a user by ID if they exist.
    # Удаляет пользователя по идентификатору, если он существует.
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def create_task(db: Session, task_in: schemas.TaskCreate, owner_id: int) -> models.Task:
    # Create a new task record and link it to the owner.
    # Создаёт новую задачу и привязывает её к владельцу.
    db_task = models.Task(
        title=task_in.title,
        description=task_in.description,
        owner_id=owner_id,
        status="pending",
        time_spent=task_in.time_spent,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, current_user: models.User, skip: int = 0, limit: int = 100) -> List[models.Task]:
    # Return tasks based on user role and pagination.
    # Возвращает задачи в зависимости от роли пользователя и пагинации.
    if current_user.role.value in ['admin', 'moderator']:
        return db.query(models.Task).offset(skip).limit(limit).all()
    return db.query(models.Task).filter(models.Task.owner_id == current_user.id).offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int, current_user) -> Optional[models.Task]:
    # Retrieve a task if the current user has access.
    # Получает задачу, если текущий пользователь имеет доступ.
    if isinstance(current_user, int):
        current_user = get_user_by_id(db, current_user)
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    if current_user.role.value in ['admin', 'moderator'] or task.owner_id == current_user.id:
        return task
    return None


def update_task(db: Session, task: models.Task, task_in: schemas.TaskUpdate) -> models.Task:
    # Apply updates to a task and refresh the object.
    # Применяет изменения к задаче и обновляет объект.
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    # Delete the specified task from the database.
    # Удаляет указанную задачу из базе данных.
    db.delete(task)
    db.commit()


def get_projects(db: Session, current_user: models.User) -> List[models.Project]:
    # Return projects available to the current user.
    # Возвращает проекты, доступные текущему пользователю.
    if current_user.role.value in ['admin', 'moderator']:
        return db.query(models.Project).all()
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()


def get_project(db: Session, project_id: int, current_user) -> Optional[models.Project]:
    # Retrieve a project only if the current user has access.
    # Получает проект только если текущий пользователь имеет доступ.
    if isinstance(current_user, int):
        current_user = get_user_by_id(db, current_user)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return None
    if current_user.role.value in ['admin', 'moderator'] or project.owner_id == current_user.id:
        return project
    return None


def get_project_by_name(db: Session, name: str, owner_id: int) -> Optional[models.Project]:
    # Find a project by name for the given owner.
    # Находит проект по имени для заданного владельца.
    return (
        db.query(models.Project)
        .filter(models.Project.name == name, models.Project.owner_id == owner_id)
        .first()
    )


def create_project(db: Session, project_in: schemas.ProjectCreate, owner_id: int) -> models.Project:
    # Create a new project record in the database.
    # Создаёт новую запись проекта в базе данных.
    db_project = models.Project(name=project_in.name, owner_id=owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project: models.Project) -> None:
    # Remove a project from the database.
    # Удаляет проект из базы данных.
    db.delete(project)
    db.commit()
