from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contacts.models import Contact
from contacts import schemas
from contacts import crud
from contacts.database import engine, Base, get_db
from datetime import datetime, timedelta

contacts = FastAPI()

Base.metadata.create_all(bind=engine)


@contacts.post("/contacts/", response_model=schemas.ContactResponse)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    return crud.create_contact(db=db, contact=contact)


@contacts.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@contacts.put("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)):
    db_contact = crud.update_contact(db, contact_id=contact_id, contact_data=contact)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@contacts.delete("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.delete_contact(db, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@contacts.get("/contacts/", response_model=list[schemas.ContactResponse])
def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_contacts(db, skip=skip, limit=limit)


@contacts.get("/contacts/search/", response_model=list[schemas.ContactResponse])
def search_contacts(query: str, db: Session = Depends(get_db)):
    return db.query(Contact).filter(
        (Contact.first_name.contains(query)) |
        (Contact.last_name.contains(query)) |
        (Contact.email.contains(query))
    ).all()


@contacts.get("/contacts/upcoming_birthdays/", response_model=list[schemas.ContactResponse])
def upcoming_birthdays(db: Session = Depends(get_db)):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(
        Contact.birthday >= today,
        Contact.birthday <= next_week
    ).all()
