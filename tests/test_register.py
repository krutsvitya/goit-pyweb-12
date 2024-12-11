import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contacts.database import get_db
from contacts.main import contacts_app  # импорт приложения FastAPI
from contacts.models import Base, User, Contact
from contacts.utils import get_current_user

# Создание тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Используется SQLite для тестирования
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фикстура для тестовой базы данных
@pytest.fixture(scope="module")
def db():
    if os.path.exists("test.db"):  # Удаление старой базы данных перед созданием новой
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)  # Создание таблиц
    db_session = SessionLocal()
    yield db_session
    db_session.close()
    Base.metadata.drop_all(bind=engine)  # Очистка после тестов

# Фикстура для создания тестового пользователя
@pytest.fixture
def test_user(db):
    # Добавление тестового пользователя
    user = User(email="testuser@example.com", hashed_password="hashedpassword123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Фикстура для создания тестового контакта
@pytest.fixture
def test_contact(db, test_user):
    # Добавление тестового контакта
    contact = Contact(
        first_name="John", last_name="Doe", email="john.doe@example.com",
        phone="1234567890", owner_id=test_user.id
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

# Мокинг зависимости для получения текущего пользователя
@pytest.fixture
def override_get_current_user(test_user):
    def mock_get_current_user():
        return test_user  # Возвращаем тестового пользователя
    return mock_get_current_user

# Создание клиента для тестирования
@pytest.fixture
def client(db, override_get_current_user):
    # Переопределение зависимостей
    contacts_app.dependency_overrides[get_db] = lambda: db
    contacts_app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(contacts_app)

# Тест маршрута получения контактов
def test_get_contacts(client, test_contact):
    response = client.get("/contacts")  # Запрос на получение контактов
    assert response.status_code == 200
    assert len(response.json()) == 1  # Проверка, что один контакт в базе
    assert response.json()[0]["email"] == test_contact.email  # Проверка email
    assert response.json()[0]["first_name"] == test_contact.first_name  # Проверка имени
    assert response.json()[0]["last_name"] == test_contact.last_name  # Проверка фамилии
