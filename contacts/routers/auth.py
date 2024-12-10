from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from contacts.models import User
from contacts.utils import create_access_token, verify_password, hash_password
from contacts.database import SessionLocal, get_db
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
from fastapi import File, UploadFile
from dotenv import load_dotenv
import os

router = APIRouter()

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME="your_email@example.com",
    MAIL_PASSWORD="your_password",
    MAIL_FROM="your_email@example.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Your App",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS=True
)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_URL"),
    api_secret=os.getenv("SECRET_KEY")
)


class EmailSchema(BaseModel):
    email: str

@router.post("/send-verification-email")
async def send_verification_email(background_tasks: BackgroundTasks, email: EmailSchema):
    user = await User.objects.get_or_none(email=email.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    verification_link = f"http://localhost:8000/verify-email/{user.id}"

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email.email],
        body=f"Click the link to verify your email: {verification_link}",
        subtype="plain"
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": "Verification email sent"}

@router.get("/verify-email/{user_id}")
async def verify_email(user_id: int):
    user = await User.objects.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await user.save()
    return {"message": "Email verified successfully"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(email: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"email": user.email, "id": user.id}


@router.post("/token", status_code=status.HTTP_201_CREATED)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/upload-avatar")
async def upload_avatar(user_id: int, file: UploadFile = File(...)):
    user = await User.objects.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    upload_result = cloudinary.uploader.upload(file.file)
    await user.save()
    return {"message": "Avatar updated successfully", "avatar_url": user.avatar_url}