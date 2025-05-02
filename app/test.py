import json

from fastapi import status
from fastapi.testclient import TestClient

from main import app  # Замените на путь к вашему экземпляру FastAPI

client = TestClient(app)

# Данные для тестов
email = "test@test.ru"
password = "simplepass"
token = None
token_type = None


def test_registered_user():
    url = "/register"
    data = {"email": email, "password": password}
    response = client.post(url, json=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_token():
    global token, token_type
    url = "/token"
    data = {"username": email, "password": password}
    response = client.post(url, data=data)

    token = response.json()["access_token"]
    token_type = response.json()["token_type"]

    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Got {response.status_code}. Response content: {response.content}"


def test_delete():
    test_token()
    url = "/delete/me"
    headers = {"Authorization": f"{token_type} {token}"}
    data = {"username": email, "password": password}
    response = client.request("DELETE", url, data=data)
    assert response.status_code == status.HTTP_200_OK


def test_get_user():
    test_registered_user()
    test_token()

    url = "/users/me"
    headers = {"Authorization": f"{token_type} {token}"}

    response = client.get(url, headers=headers)
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Expected 200 OK, but got {response.status_code}. Response content: {response.content}"

    test_delete()

    response = client.get(url, headers=headers)
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Expected 401, but got {response.status_code}. Response content: {response.content}"


def create_task(time: int, name: str):
    url = "/task/create"
    headers = {"Authorization": f"{token_type} {token}"}
    data = {"title": name, "description": "Description", "time_spent": time}

    return client.post(url, headers=headers, json=data)


def test_create_task():
    test_registered_user()
    test_token()

    response = create_task(6, "Test task")
    assert response.status_code == status.HTTP_201_CREATED

    test_delete()

    response = create_task(6, "Test task")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def get_tasks():
    url = "/tasks/"
    headers = {"Authorization": f"{token_type} {token}"}

    response = client.get(url, headers=headers)
    if response.status_code == status.HTTP_200_OK:
        return response.json()

    return None


def get_tasks_check(tasks_set: set):
    flag = True

    server_tasks = get_tasks()

    if server_tasks is not None:
        for s in server_tasks:
            if s["title"] not in tasks_set:
                flag = False
                break
    else:
        flag = False

    return flag


def test_get_tasks():
    test_registered_user()
    test_token()

    tasks_set = set()
    tasks_set.add("Test task 1")
    tasks_set.add("Test task 2")

    for task in tasks_set:
        create_task(6, task)

    assert get_tasks_check(tasks_set)

    test_delete()

    assert not get_tasks_check(tasks_set)


def task_delete(task):
    url = f"/tasks/{task['id']}"
    headers = {"Authorization": f"{token_type} {token}"}

    response = client.delete(url, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert task not in get_tasks(), f"{task} in {get_tasks()}"


def test_task_deleting():
    test_registered_user()
    test_token()

    create_task(6, "Delete")

    task = get_tasks()[0]
    print(task)

    task_delete(task)

    test_delete()


def test_create_project_with_tasks():  # use the fixture
    # Create some test tasks
    test_registered_user()
    test_token()

    headers = {"Authorization": f"{token_type} {token}"}

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
    print("Response status:", response.status_code)
    print("Response body:", response.text)
    assert response.status_code == status.HTTP_201_CREATED

    project = response.json()
    assert project["name"] == "Test Project"
    assert len(project["tasks"]) == 2

    test_delete()


def test_create_project_with_invalid_task_id():
    test_registered_user()
    test_token()

    headers = {"Authorization": f"{token_type} {token}"}

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

    server_tasks = get_tasks()
    assert len(server_tasks) == 2

    headers = {"Authorization": f"{token_type} {token}"}
    response = client.delete(f"/tasks/{server_tasks[0]['id']}", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    assert len(get_tasks()) == 1

    project_data = {
        "name": "Invalid Project",
        "task_ids": [server_tasks[0]["id"], server_tasks[1]["id"]],
    }  # Invalid task ID
    response = client.post("/projects/", json=project_data, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert (
        f"Task with id {server_tasks[0]['id']} not found" in response.json()["detail"]
    )

    test_delete()


def test_select_tasks_greedy():
    test_registered_user()
    test_token()
    headers = {"Authorization": f"{token_type} {token}"}

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

    test_delete()


def test_project_not_found():
    test_registered_user()
    test_token()
    headers = {"Authorization": f"{token_type} {token}"}

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

    test_delete()
