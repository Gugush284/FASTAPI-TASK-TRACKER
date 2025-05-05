# FASTAPI-TASK-TRACKER

## Как запустить приложение

Для начала работы необходимо установить docker и в корневой директории ввести команду:
```
docker compose up --build
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
