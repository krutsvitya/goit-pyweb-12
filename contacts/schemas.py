"""
Модулі Pydantic схем для управління контактами.

Цей модуль містить Pydantic моделі, які забезпечують валідацію вхідних та вихідних даних для операцій із контактами.
"""
from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


class ContactBase(BaseModel):
    """
    Базова модель контактів.

    Використовується для загального визначення полів, які спільні для створення, оновлення та відповіді контактів.

    Атрибути:
        first_name (str): Ім'я контакту.
        last_name (str): Прізвище контакту.
        email (EmailStr): Електронна пошта контакту, перевіряється на правильність формату.
        phone (str): Номер телефону контакту.
        birthday (date): Дата народження контакту.
        additional_info (Optional[str]): Додаткова інформація про контакт (необов'язкове поле).
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    """
    Модель для створення нового контакту.

    Наслідує всі атрибути від ContactBase.
    """
    pass


class ContactUpdate(BaseModel):
    """
    Модель для оновлення існуючого контакту.

    Усі поля є необов'язковими, дозволяючи оновлювати лише вибрані атрибути.

   Атрибути:
       first_name (Optional[str]): Ім'я контакту.
       last_name (Optional[str]): Прізвище контакту.
       email (Optional[EmailStr]): Електронна пошта контакту.
       phone (Optional[str]): Номер телефону контакту.
       birthday (Optional[date]): Дата народження контакту.
       additional_info (Optional[str]): Додаткова інформація про контакт.
   """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None


class ContactResponse(ContactBase):
    """
    Модель для відповіді при запитах на інформацію про контакт.

    Наслідує атрибути від ContactBase і додає унікальний ідентифікатор контакту.

    Атрибути:
        id (int): Унікальний ідентифікатор контакту.
    """
    id: int

    class Config:
        """
        Налаштування моделі для коректного перетворення даних із атрибутів SQLAlchemy моделі.
        """
        from_attributes = True
