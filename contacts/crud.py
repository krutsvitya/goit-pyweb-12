"""
Модуль для операцій із контактами в базі даних.

Цей модуль містить функції для створення, оновлення, видалення та отримання контактів із бази даних.
"""

from sqlalchemy.orm import Session
from contacts import models
from contacts import schemas


def get_contact(db: Session, contact_id: int):
    """
    Отримує контакт із бази даних за його ідентифікатором.

    Аргументи:
        db (Session): Сесія бази даних.
        contact_id (int): Ідентифікатор контакту.

    Повертає:
        Contact: Об'єкт контакту або None, якщо контакт не знайдено.
    """
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


def get_contacts(db: Session, skip: int = 0, limit: int = 10):
    """
    Отримує список контактів із бази даних.

    Аргументи:
        db (Session): Сесія бази даних.
        skip (int): Кількість пропущених записів (за замовчуванням 0).
        limit (int): Максимальна кількість записів, що повертаються (за замовчуванням 10).

    Повертає:
        list: Список контактів.
    """
    return db.query(models.Contact).offset(skip).limit(limit).all()


def create_contact(db: Session, contact: schemas.ContactCreate):
    """
    Створює новий контакт у базі даних.

    Аргументи:
        db (Session): Сесія бази даних.
        contact (ContactCreate): Дані нового контакту.

    Повертає:
        Contact: Об'єкт створеного контакту.
    """
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, contact_id: int, contact_data: schemas.ContactUpdate):
    """
    Оновлює дані контакту в базі даних.

    Аргументи:
        db (Session): Сесія бази даних.
        contact_id (int): Ідентифікатор контакту, що оновлюється.
        contact_data (ContactUpdate): Нові дані для контакту.

    Повертає:
        Contact: Оновлений об'єкт контакту або None, якщо контакт не знайдено.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        for key, value in contact_data.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int):
    """
    Видаляє контакт із бази даних.

    Аргументи:
        db (Session): Сесія бази даних.
        contact_id (int): Ідентифікатор контакту, що видаляється.

    Повертає:
        Contact: Видалений об'єкт контакту або None, якщо контакт не знайдено.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact
