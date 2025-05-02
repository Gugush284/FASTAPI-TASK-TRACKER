import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:secret@localhost:5432/tasktracker"
)

# Создаем движок подключения к БД
engine = create_engine(DATABASE_URL)

# Создаем класс для декларативного описания моделей
Base = declarative_base()

# Создаем сессию для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Зависимость для работы с БД ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
