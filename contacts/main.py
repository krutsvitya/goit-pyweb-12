from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from contacts.models import Contact
from contacts import schemas
from contacts import crud
from contacts.database import engine, Base, get_db
from datetime import datetime, timedelta
from contacts.routers import auth, contacts_router
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware

contacts_app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
contacts_app.state.limiter = limiter
contacts_app.add_middleware(SlowAPIMiddleware)

Base.metadata.create_all(bind=engine)

contacts_app.include_router(auth.router)
contacts_app.include_router(contacts_router.router)

@contacts_app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Обробляє помилку ліміту запитів (Rate Limit Exceeded).

    Аргументи:
        request (Request): Запит, що викликав помилку.
        exc (RateLimitExceeded): Об'єкт помилки ліміту запитів.

    Повертає:
        JSONResponse: Відповідь із статус кодом 429 та повідомленням про перевищення ліміту.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"}
    )

origins = [
    "http://localhost",
    "http://localhost:8000",
]

contacts_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contacts_app.post("/contacts/", response_model=schemas.ContactResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_contact(
    request: Request,
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db)
):
    """
    Створює новий контакт.

    Аргументи:
        request (Request): Запит від клієнта.
        contact (schemas.ContactCreate): Дані нового контакту.
        db (Session): Сесія бази даних для доступу до таблиці контактів.

    Повертає:
        schemas.ContactResponse: Створений контакт.
    """
    return crud.create_contact(db=db, contact=contact)

@contacts_app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Повертає контакт за його ID.

    Аргументи:
        contact_id (int): Ідентифікатор контакту.
        db (Session): Сесія бази даних.

    Повертає:
        schemas.ContactResponse: Контакт з відповідним ID.
    """
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@contacts_app.put("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)):
    """
    Оновлює контакт за його ID.

    Аргументи:
        contact_id (int): Ідентифікатор контакту.
        contact (schemas.ContactUpdate): Дані для оновлення контакту.
        db (Session): Сесія бази даних.

    Повертає:
        schemas.ContactResponse: Оновлений контакт.
    """
    db_contact = crud.update_contact(db, contact_id=contact_id, contact_data=contact)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@contacts_app.delete("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Видаляє контакт за його ID.

    Аргументи:
        contact_id (int): Ідентифікатор контакту.
        db (Session): Сесія бази даних.

    Повертає:
        schemas.ContactResponse: Видалений контакт.
    """
    db_contact = crud.delete_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@contacts_app.get("/contacts/", response_model=list[schemas.ContactResponse])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Повертає список контактів з пагінацією.

    Аргументи:
        skip (int): Кількість пропущених елементів.
        limit (int): Максимальна кількість елементів.
        db (Session): Сесія бази даних.

    Повертає:
        list[schemas.ContactResponse]: Список контактів.
    """
    return crud.get_contacts(db, skip=skip, limit=limit)

@contacts_app.get("/contacts/search/", response_model=list[schemas.ContactResponse])
def search_contacts(query: str, db: Session = Depends(get_db)):
    """
    Пошук контактів за запитом (ім'я, прізвище або email).

    Аргументи:
        query (str): Пошуковий запит.
        db (Session): Сесія бази даних.

    Повертає:
        list[schemas.ContactResponse]: Список знайдених контактів.
    """
    return db.query(Contact).filter(
        (Contact.first_name.contains(query)) |
        (Contact.last_name.contains(query)) |
        (Contact.email.contains(query))
    ).all()

@contacts_app.get("/contacts/upcoming_birthdays/", response_model=list[schemas.ContactResponse])
def upcoming_birthdays(db: Session = Depends(get_db)):
    """
    Повертає контакти з найближчими днями народження (в межах наступного тижня).

    Аргументи:
        db (Session): Сесія бази даних.

    Повертає:
        list[schemas.ContactResponse]: Список контактів з днями народження в межах наступного тижня.
    """
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(
        Contact.birthday >= today,
        Contact.birthday <= next_week
    ).all()
