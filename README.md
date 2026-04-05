# FASTAPI-TASK-TRACKER

## Как запустить приложение

Для начала работы необходимо установить docker и в корневой директории ввести команду:
```
docker compose up --build
```

## Как использовать клиент

В репозитории есть простой Python клиент для взаимодействия с API. Для его работы требуется установленный `requests`:

### Документация API через Swagger

После запуска приложения документация Swagger доступна по адресу:

```bash
http://localhost:8000/docs
```

Также корневой URL перенаправляет на Swagger UI:

```bash
http://localhost:8000/
```

JSON спецификация OpenAPI сохраняется в папке `swagger_volume` и доступна внутри контейнера по пути `/app/swagger/openapi.json`.

Документация описывает:
- доступные операции;
- форматы входных и выходных данных;
- возможные коды ошибок.


### Swagger / OpenAPI

После запуска приложения документация Swagger доступна по адресу:

```bash
http://localhost:8000/docs
```

JSON спецификация OpenAPI доступна по адресу:

```bash
http://localhost:8000/openapi.json
```


```bash
pip install requests
```

### Быстрый демо всех операций:

Запустите полный демо-режим, который выполнит все операции последовательно:

```bash
python3 client.py --demo
```

Этот режим:
1. Зарегистрирует пользователя
2. Выполнит вход
3. Получит информацию о пользователе
4. Создаст несколько задач
5. Получит список задач
6. Создаст проект с задачами
7. Выполнит выбор задач по жадному алгоритму

### Индивидуальные команды:

Регистрация пользователя:
```bash
python3 client.py register
```

Вход в систему:
```bash
python3 client.py login
```

Просмотр текущего пользователя:
```bash
python3 client.py user
```

Создание задачи:
```bash
python3 client.py create-task "Моя задача" --description "Описание" --time 30
```

Просмотр всех задач:
```bash
python3 client.py tasks
```

Создание проекта с задачами:
```bash
python3 client.py create-project "Мой проект" 1 2 3
```

Выбор задач для выполнения (жадный алгоритм):
```bash
python3 client.py select-tasks 1 60
```

Полный список команд:
```bash
python3 client.py --help
```

## Структура приложения

Приложение состоит из двух взаимодействующих контейнеров: база данных postgres и сервер на FastAPI.

### Структура базы данных:

База данных содержит в себе три таблицы: user, task, project.

Таблица user содержит в себе поля:
- id. Уникальный идентификатор пользователя
- email. Электронная почта пользователя
- hashed_password. Хэшированный пароль
- created_at. Дата и время создания пользователя
- tasks. Список задач пользователя (Task). Связь один-ко-многим
- projects. Список проектов пользователя (Project). Связь один-ко-многим

Таблица task содержит в себе поля:
- id. Уникальный идентификатор
- title. Название задачи
- description. Описание задачи
- status. Статус задачи.
- created_at. Дата и время создания задачи
- time_spent. Время, затраченное на задачу (в минутах)
- owner_id. Внешний ключ на пользователя (users.id). Cвязь многие-к-одному
- project_id. Внешний ключ на проект (projects.id). Может быть пустым, связь многие-к-одному

Таблица project содержит в себе поля:
- id. Уникальный идентификатор проекта
- name. Название проекта
- owner_id. Ссылка на пользователя-владельца проекта (users.id)
- owner. Cвязь с таблицей users (каждый проект принадлежит одному пользователю)
- tasks. Cвязь с таблицей tasks (один проект может содержать множество задач)

### Структура сервера:

Сервер написан на Python с использование FastAPI. Структура сервера:
- auth. Функции аунтефикации пользователя
- crud. CRUD операции с базой данных
- database. Подключение к базе данных
- main. Главный файл программы, который содержит endpoints
- models. Модели SQLAlchemy для работы с базой данных
- schemas. Схемы для обработки endpoints
- test. Тест клиент

### Как работь с сервером

Регистрация:
```
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

Получения токена:
```
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

Удаление пользователя:
```
curl -X DELETE "http://localhost:8000/delete/me" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

Просмотр текущего пользователя:
```
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer <your_access_token>"
```

Создание задачи:
```
curl -X POST "http://localhost:8000/task/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
        "title": "Новая задача",
        "description": "Описание задачи",
        "time_spent": 0
      }'
```

Получение списка задач текущего пользователя:
```
curl -X GET "http://localhost:8000/tasks/" \
  -H "Authorization: Bearer <your_access_token>"
```

Удаление задачи:
```
curl -X DELETE "http://localhost:8000/tasks/123" \
  -H "Authorization: Bearer <your_access_token>"
```

Создание нового проекта с задачами:
```
curl -X POST "http://localhost:8000/projects/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
        "name": "Новый проект",
        "task_ids": [1, 2, 3]
      }'
```

Удаление проекта:
```
curl -X DELETE "http://localhost:8000/projects/123" \
  -H "Authorization: Bearer <your_access_token>"
```

Выбор задач для выполнения:
```
curl -X GET "http://localhost:8000/projects/<project id>/select_tasks?time_limit=<project time>" \
  -H "Authorization: Bearer <your_access_token>"
```
