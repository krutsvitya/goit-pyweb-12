import sqlalchemy
from sqlalchemy import Column, Integer, String, Date, Boolean
from .database import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from passlib.context import CryptContext


class Contact(Base):
    """
    Модель для збереження контактів.

    Атрибути:
        id (int): Унікальний ідентифікатор контакту.
        first_name (str): Ім'я контакту.
        last_name (str): Прізвище контакту.
        email (str): Унікальний email контакту.
        phone (str): Унікальний номер телефону контакту.
        birthday (Date): Дата народження контакту.
        additional_info (str, optional): Додаткова інформація про контакт.
        owner_id (int): Ідентифікатор власника контакту (зовнішній ключ).
        owner (User): Відношення до моделі користувача, який є власником контакту.

    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    birthday = Column(Date)
    additional_info = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="contacts")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    Модель для збереження інформації про користувачів.

    Атрибути:
        id (int): Унікальний ідентифікатор користувача.
        email (str): Унікальний email користувача.
        hashed_password (str): Хешований пароль користувача.
        contacts (List[Contact]): Список контактів, пов'язаних із користувачем.

    Методи:
        verify_password(password: str) -> bool:
            Перевіряє, чи відповідає переданий пароль хешу збереженого пароля.
            Параметри:
                password (str): Пароль для перевірки.
            Повертає:
                bool: Результат перевірки (True або False).

        set_password(password: str):
            Встановлює новий хешований пароль для користувача.
            Параметри:
                password (str): Новий пароль для хешування.

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    contacts = relationship("Contact", back_populates="owner")

    def verify_password(self, password: str):
        """
        Перевіряє, чи відповідає переданий пароль збереженому хешу пароля.

        Параметри:
            password (str): Пароль для перевірки.

        Повертає:
            bool: True, якщо пароль правильний, інакше False.

        """
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str):
        """
        Встановлює новий хешований пароль для користувача.

        Параметри:
            password (str): Пароль, який потрібно хешувати.

        """
        self.hashed_password = pwd_context.hash(password)
