from typing import List, Optional, Union

from sqlalchemy.orm import Session

import models
import schemas


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_in: schemas.UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(email=user_in.email, hashed_password=hashed_password, role=user_in.role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def get_all_users(db: Session) -> List[models.User]:
    return db.query(models.User).all()


def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate) -> models.User:
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(user, field, value)
        
    db.commit()
    db.refresh(user)
    
    return user


def delete_user_by_id(db: Session, user_id: int) -> bool:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user:
        db.delete(user)
        db.commit()
        return True
    
    return False


def create_task(db: Session, task_in: schemas.TaskCreate, owner_id: int) -> models.Task:
    
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
    if current_user.role.value in ['admin', 'moderator']:
        return db.query(models.Task).offset(skip).limit(limit).all()
    
    return db.query(models.Task).filter(models.Task.owner_id == current_user.id).offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int, current_user: Union[models.User, int]) -> Optional[models.Task]:
    if isinstance(current_user, int):
        current_user = get_user_by_id(db, current_user)
        
        if current_user is None:
            return None
        
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    
    if current_user.role.value in ['admin', 'moderator'] or task.owner_id == current_user.id:
        return task
    
    return None


def update_task(db: Session, task: models.Task, task_in: schemas.TaskUpdate) -> models.Task:
    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)
        
    db.commit()
    db.refresh(task)
    
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()


def get_projects(db: Session, current_user: models.User) -> List[models.Project]:
    if current_user.role.value in ['admin', 'moderator']:
        return db.query(models.Project).all()
    
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()


def get_project(db: Session, project_id: int, current_user: Union[models.User, int]) -> Optional[models.Project]:
    if isinstance(current_user, int):
        current_user = get_user_by_id(db, current_user)
        
        if current_user is None:
            return None
        
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return None
    
    if current_user.role.value in ['admin', 'moderator'] or project.owner_id == current_user.id:
        return project
    
    return None


def get_project_by_name(db: Session, name: str, owner_id: int) -> Optional[models.Project]:
    return (
        db.query(models.Project)
        .filter(models.Project.name == name, models.Project.owner_id == owner_id)
        .first()
    )


def create_project(db: Session, project_in: schemas.ProjectCreate, owner_id: int) -> models.Project:
    db_project = models.Project(name=project_in.name, owner_id=owner_id)
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


def delete_project(db: Session, project: models.Project) -> None:
    db.delete(project)
    db.commit()
    

def update_project(db: Session, project: models.Project, project_in: schemas.ProjectUpdate) -> models.Project:
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.task_ids is not None:
        db.query(models.Task).filter(models.Task.project_id == project.id).update({"project_id": None})
        for task_id in project_in.task_ids:
            task = db.query(models.Task).filter(models.Task.id == task_id).first()
            if task:
                task.project_id = project.id
    db.commit()
    db.refresh(project)
    return project
