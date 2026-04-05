import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection URL, read from environment or use default.
# URL подключения к базе данных берётся из окружения или по умолчанию.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:secret@localhost:5432/tasktracker"
)

# Create SQLAlchemy engine for database communication.
# Создаём SQLAlchemy движок для связи с базой данных.
engine = create_engine(DATABASE_URL)

# Base class for declarative models.
# Базовый класс для декларативных моделей SQLAlchemy.
Base = declarative_base()

# Session factory configured for application use.
# Фабрика сессий для работы с базой данных в приложении.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # Provide a database session to endpoint dependencies.
    # Предоставляет сессию базы данных зависимостям endpoint.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
