FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic python-jose[cryptography] passlib bcrypt==4.0.1 pydantic[email] python-multipart httpx pytest

COPY . .

CMD ["pytest", "./test.py"]