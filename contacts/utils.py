"""
Модуль для забезпечення авторизації та безпеки у FastAPI застосунку.

Цей модуль містить функції для створення токенів доступу, верифікації токенів, хешування паролів та отримання поточного користувача.
"""
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Union
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .models import User
from .database import SessionLocal

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """
    Створює токен доступу.

    Аргументи:
        data (dict): Дані, які будуть зашифровані в токені.
        expires_delta (Union[timedelta, None]): Час дії токена. Якщо не вказано, використовується значення за замовчуванням.

    Повертає:
        str: Зашифрований JWT токен.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    """
    Перевіряє дійсність токена доступу.

    Аргументи:
        token (str): Токен, що перевіряється.

    Повертає:
        dict або None: Розшифровані дані з токена, якщо перевірка успішна. None, якщо токен недійсний.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_password(plain_password, hashed_password):
    """
    Перевіряє відповідність пароля його хешу.

    Аргументи:
        plain_password (str): Пароль у відкритому вигляді.
        hashed_password (str): Хеш пароля.

    Повертає:
        bool: True, якщо пароль відповідає хешу, False інакше.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    """
    Генерує хеш для пароля.

    Аргументи:
        password (str): Пароль у відкритому вигляді.

    Повертає:
        str: Хешований пароль.
    """
    return pwd_context.hash(password)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
    """
    Отримує поточного користувача з токена.

    Аргументи:
        token (str): Токен доступу.
        db (Session): Сесія бази даних.

    Повертає:
        User: Об'єкт користувача, отриманий із бази даних.

    Порушення:
        HTTPException: Якщо токен недійсний або користувача не знайдено.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
