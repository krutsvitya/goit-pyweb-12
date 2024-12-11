"""
Роутер для реєстрації, автентифікації, підтвердження електронної пошти та завантаження аватарів.

Цей модуль містить API маршрути для реєстрації користувачів, підтвердження їх електронної пошти, автентифікації через токени та завантаження аватарів користувачів.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from contacts.models import User
from contacts.utils import create_access_token, verify_password, hash_password
from contacts.database import SessionLocal, get_db
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
from fastapi import File, UploadFile
from dotenv import load_dotenv
import os

# Ініціалізація роутера
router = APIRouter()

# Завантаження конфігурацій з файлу .env
load_dotenv()

# Налаштування поштового сервера
conf = ConnectionConfig(
    MAIL_USERNAME="your_email@example.com",
    MAIL_PASSWORD="your_password",
    MAIL_FROM="your_email@example.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Your App",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

# Налаштування Cloudinary для завантаження аватарів
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_URL"),
    api_secret=os.getenv("SECRET_KEY")
)

# Схема для електронної пошти
class EmailSchema(BaseModel):
    email: str

# Маршрут для відправки листа для підтвердження електронної пошти
@router.post("/send-verification-email")
async def send_verification_email(background_tasks: BackgroundTasks, email: EmailSchema):
    """
    Відправляє листа для підтвердження електронної пошти користувача.

    Аргументи:
        background_tasks (BackgroundTasks): Завдання для фонової обробки.
        email (EmailSchema): Електронна пошта користувача.

    Повертає:
        dict: Повідомлення про успішну відправку листа.
    """
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

# Маршрут для підтвердження електронної пошти користувача
@router.get("/verify-email/{user_id}")
async def verify_email(user_id: int):
    """
    Підтверджує електронну пошту користувача за його ідентифікатором.

    Аргументи:
        user_id (int): Ідентифікатор користувача для підтвердження.

    Повертає:
        dict: Повідомлення про успішне підтвердження електронної пошти.
    """
    user = await User.email.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await user.save()
    return {"message": "Email verified successfully"}

class RegisterRequest(BaseModel):
    email: str
    password: str

# Маршрут для реєстрації нового користувача
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
        Реєструє нового користувача.

        Аргументи:
            request (RegisterRequest): Дані для реєстрації.
            db (Session): Сесія бази даних.

        Повертає:
            dict: Дані зареєстрованого користувача (email, id).
        """
    print(request.dict())  # Виведе вміст запиту
    db_user = db.query(User).filter(request.email == User.email).first()
    if db_user:
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(email=request.email, hashed_password=hash_password(request.password))

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"email": user.email, "id": user.id}


# Маршрут для отримання токена доступу
@router.post("/token", status_code=status.HTTP_201_CREATED)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Отримує токен доступу для користувача.

    Аргументи:
        form_data (OAuth2PasswordRequestForm): Дані форми для автентифікації (username, password).
        db (Session): Сесія бази даних.

    Повертає:
        dict: Токен доступу та тип токена.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

# Маршрут для завантаження аватара користувача
@router.post("/upload-avatar")
async def upload_avatar(user_id: int, file: UploadFile = File(...)):
    """
    Завантажує новий аватар для користувача.

    Аргументи:
        user_id (int): Ідентифікатор користувача.
        file (UploadFile): Аватар у вигляді файлу.

    Повертає:
        dict: Повідомлення про успішне оновлення аватара та URL нового аватара.
    """
    user = await User.objects.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    upload_result = cloudinary.uploader.upload(file.file)
    user.avatar_url = upload_result['url']
    await user.save()
    return {"message": "Avatar updated successfully", "avatar_url": user.avatar_url}
