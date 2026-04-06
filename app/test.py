import os

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

import database
import models

os.environ["TESTING"] = "1"

from main import app
import auth
import crud


TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield


def override_get_db():
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[database.get_db] = override_get_db

client = TestClient(app)

email = "test@test.ru"
password = "simplepass"


def register_user():
    url = "/register"
    data = {"email": email, "password": password}
    response = client.post(url, json=data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def authorize_user():
    url = "/token"
    data = {"username": email, "password": password}
    response = client.post(url, data=data)
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Got {response.status_code}. Response content: {response.content}"
    payload = response.json()
    return payload["access_token"], payload["token_type"]


def get_auth_headers():
    register_user()
    token, token_type = authorize_user()
    return {"Authorization": f"{token_type} {token}"}


def test_registered_user():
    register_user()


def test_token():
    register_user()
    token, token_type = authorize_user()
    assert token
    assert token_type == "bearer"


def test_delete():
    headers = get_auth_headers()
    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_get_user():
    headers = get_auth_headers()

    url = "/users/me"
    response = client.get(url, headers=headers)
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Expected 200 OK, but got {response.status_code}. Response content: {response.content}"

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(url, headers=headers)
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Expected 401, but got {response.status_code}. Response content: {response.content}"


def create_task(time: int, name: str, headers):
    url = "/task/create"
    data = {"title": name, "description": "Description", "time_spent": time}
    return client.post(url, headers=headers, json=data)


def test_create_task():
    headers = get_auth_headers()

    response = create_task(6, "Test task", headers)
    assert response.status_code == status.HTTP_201_CREATED

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = create_task(6, "Test task", headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def get_tasks(headers):
    url = "/tasks/"
    response = client.get(url, headers=headers)
    if response.status_code == status.HTTP_200_OK:
        return response.json()
    return None


def get_tasks_check(tasks_set: set, headers):
    server_tasks = get_tasks(headers)
    if server_tasks is None:
        return False
    return all(task["title"] in tasks_set for task in server_tasks)


def test_get_tasks():
    headers = get_auth_headers()

    tasks_set = {"Test task 1", "Test task 2"}
    for task_name in tasks_set:
        create_task(6, task_name, headers)

    assert get_tasks_check(tasks_set, headers)

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    assert not get_tasks_check(tasks_set, headers)


def task_delete(task, headers):
    url = f"/tasks/{task['id']}"
    response = client.delete(url, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert task not in get_tasks(headers), f"{task} in {get_tasks(headers)}"


def test_task_deleting():
    headers = get_auth_headers()

    create_task(6, "Delete", headers)

    task = get_tasks(headers)[0]
    task_delete(task, headers)

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_create_project_with_tasks():
    headers = get_auth_headers()

    task_data = {
        "title": "Test Task 1",
        "description": "Test Description 1",
        "time_spent": 6,
    }
    response = client.post("/task/create", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    task1_id = response.json()["id"]

    task_data = {
        "title": "Test Task 2",
        "description": "Test Description 2",
        "time_spent": 6,
    }
    response = client.post("/task/create", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    task2_id = response.json()["id"]

    project_data = {"name": "Test Project", "task_ids": [task1_id, task2_id]}
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    project = response.json()
    assert project["name"] == "Test Project"
    assert len(project["tasks"]) == 2

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_create_project_with_invalid_task_id():
    headers = get_auth_headers()

    task_data = {
        "title": "Test Task 1",
        "description": "Test Description 1",
        "time_spent": 6,
    }
    response = client.post("/task/create", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    task_data = {
        "title": "Test Task 2",
        "description": "Test Description 2",
        "time_spent": 6,
    }
    response = client.post("/task/create", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    server_tasks = get_tasks(headers)
    assert len(server_tasks) == 2

    response = client.delete(f"/tasks/{server_tasks[0]['id']}", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    assert len(get_tasks(headers)) == 1

    project_data = {
        "name": "Invalid Project",
        "task_ids": [server_tasks[0]["id"], server_tasks[1]["id"]],
    }
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        f"Task with id {server_tasks[0]['id']} not found" in response.json()["detail"]
    )

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_select_tasks_greedy():
    headers = get_auth_headers()

    # Создаем задачи с разным временем
    task1_data = {"title": "Task 1", "description": "Desc 1", "time_spent": 10}
    task2_data = {"title": "Task 2", "description": "Desc 2", "time_spent": 20}
    task3_data = {"title": "Task 3", "description": "Desc 3", "time_spent": 30}

    task1_response = client.post("/task/create", json=task1_data, headers=headers)
    task2_response = client.post("/task/create", json=task2_data, headers=headers)
    task3_response = client.post("/task/create", json=task3_data, headers=headers)

    assert task1_response.status_code == status.HTTP_201_CREATED
    assert task2_response.status_code == status.HTTP_201_CREATED
    assert task3_response.status_code == status.HTTP_201_CREATED

    task1_id = task1_response.json()["id"]
    task2_id = task2_response.json()["id"]
    task3_id = task3_response.json()["id"]

    project_data = {"name": "Test Project", "task_ids": [task1_id, task2_id, task3_id]}
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    project_id = response.json()["id"]

    response = client.get(
        f"/projects/{project_id}/select_tasks?time_limit=45", headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    selected_tasks = response.json()
    assert len(selected_tasks) == 2

    # Проверяем порядок задач (должны быть отсортированы по времени)
    assert selected_tasks[0]["time_spent"] == 10
    assert selected_tasks[1]["time_spent"] == 20

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_project_not_found():
    headers = get_auth_headers()

    task1_data = {"title": "Task 1", "description": "Desc 1", "time_spent": 10}
    task1_response = client.post("/task/create", json=task1_data, headers=headers)
    assert task1_response.status_code == status.HTTP_201_CREATED

    task1_id = task1_response.json()["id"]

    project_data = {"name": "Test Project", "task_ids": [task1_id]}
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    project_id = response.json()["id"]

    response = client.delete(f"/projects/{project_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get(
        f"/projects/{project_id}/select_tasks?time_limit=60", headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Project not found" in response.json()["detail"]

    project_data = {"name": "Test Project", "task_ids": [task1_id]}
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

    project_id = response.json()["id"]

    response = client.delete(f"/tasks/{task1_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(
        f"/projects/{project_id}/select_tasks?time_limit=60", headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Project not found" in response.json()["detail"]

    response = client.request("DELETE", "/delete/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def create_user_with_role(db, email: str, password: str, role: str):
    from schemas import UserCreate
    user_in = UserCreate(email=email, password=password, role=role)
    return crud.create_user(db, user_in, auth.get_password_hash(password))


def get_auth_headers_for_user(email: str, password: str):
    # Register if not exists, but since we create via crud, assume exists
    url = "/token"
    data = {"username": email, "password": password}
    response = client.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    return {"Authorization": f"{payload['token_type']} {payload['access_token']}"}


def test_role_based_access():
    # Create admin (first user)
    admin_headers = get_auth_headers()  # This creates admin

    # Create viewer and moderator via crud (since register restricts roles)
    db = TestingSessionLocal()
    create_user_with_role(db, "viewer@test.com", "password", "viewer")
    create_user_with_role(db, "moderator@test.com", "password", "moderator")
    db.close()

    viewer_headers = get_auth_headers_for_user("viewer@test.com", "password")
    moderator_headers = get_auth_headers_for_user("moderator@test.com", "password")

    # Test moderator can update their own task
    task_data = {"title": "Moderator Task", "description": "Desc", "time_spent": 10}
    response = client.post("/task/create", json=task_data, headers=moderator_headers)
    assert response.status_code == status.HTTP_201_CREATED
    task_id = response.json()["id"]

    update_data = {"title": "Updated by Moderator"}
    response = client.patch(f"/tasks/{task_id}", json=update_data, headers=moderator_headers)
    assert response.status_code == status.HTTP_200_OK

    # Test viewer cannot update task (moderator access required)
    response = client.patch(f"/tasks/{task_id}", json={"title": "Updated by Viewer"}, headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test moderator can delete their own task
    response = client.delete(f"/tasks/{task_id}", headers=moderator_headers)
    assert response.status_code == status.HTTP_200_OK

    # Test viewer cannot delete task (moderator access required)
    task_data = {"title": "Viewer Task", "description": "Desc", "time_spent": 10}
    response = client.post("/task/create", json=task_data, headers=viewer_headers)
    assert response.status_code == status.HTTP_201_CREATED
    task_id = response.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test admin can get all users
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) >= 3  # admin, viewer, moderator

    # Test moderator cannot get all users
    response = client.get("/users/", headers=moderator_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test viewer cannot get all users
    response = client.get("/users/", headers=viewer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Clean up
    response = client.request("DELETE", "/delete/me", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.request("DELETE", "/delete/me", headers=viewer_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.request("DELETE", "/delete/me", headers=moderator_headers)
    assert response.status_code == status.HTTP_200_OK
