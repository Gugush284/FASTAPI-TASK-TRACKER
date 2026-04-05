import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import crud
import database

# Secret and algorithm for JWT token generation.
# Секрет и алгоритм для генерации JWT токенов.
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing context using bcrypt.
# Контекст хэширования паролей на основе bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 scheme for bearer token authentication.
# Схема OAuth2 для аутентификации по Bearer токену.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify plain password against hashed password.
    # Проверяет простой пароль с хэшированным паролем.
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Hash plain password for storage.
    # Хэширует пароль для хранения.
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str):
    # Authenticate a user by email and password.
    # Аутентифицирует пользователя по email и паролю.
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Create a JWT token with expiration.
    # Создаёт JWT токен с временем жизни.
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)
):
    # Get the current authenticated user from the token.
    # Получает текущего аутентифицированного пользователя из токена.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    # Keep token role consistency if role changed.
    # Поддержка согласованности роли в токене, если роль изменилась.
    if role and user.role.value != role:
        # Could refresh token, but for simplicity, just use user.role.
        pass
    return user


async def require_admin(current_user = Depends(get_current_user)):
    # Require admin access for route.
    # Требует роль admin для доступа к маршруту.
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_moderator(current_user = Depends(get_current_user)):
    # Require moderator or admin access for route.
    # Требует роль moderator или admin для доступа к маршруту.
    if current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator access required")
    return current_user
