from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contacts.models import Contact, User
from contacts.database import SessionLocal, get_db
from contacts.utils import get_current_user
from contacts.schemas import ContactCreate, ContactResponse

router = APIRouter()


@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.email == contact.email).first()
    if db_contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    new_contact = Contact(**contact.dict())
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


@router.get("/contacts")
def get_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Contact).filter(Contact.owner_id == current_user.id).all()
