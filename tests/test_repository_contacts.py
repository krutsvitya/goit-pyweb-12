import unittest
from unittest.mock import MagicMock

import pydantic
from sqlalchemy.orm import Session
from contacts.models import Contact
from contacts.schemas import ContactCreate, ContactUpdate, ContactBase
from contacts.crud import (
    create_contact,
    get_contact,
    get_contacts,
    delete_contact,
    update_contact,
)
from pydantic import BaseModel
class TestContacts(unittest.TestCase):
    def setUp(self):
        # Мокаем сессию базы данных
        self.session = MagicMock(spec=Session)

        self.contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            phone="1234567890",
            birthday="1990-01-01"
        )

        self.contact_update = ContactUpdate(
            first_name="Jane",
            last_name="Doe",
            email="janedoe@example.com",
            phone="0987654321",
            birthday="1990-01-02"
        )
        self.contact = Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            phone="1234567890",
            birthday="1990-01-01"
        )


    async def test_create_contact(self):
        # Мокаем поведение методов SQLAlchemy

        body = Contact(self.contact_data)
        result = await create_contact(self.session, self.contact_data)
        self.assertEqual(result.email, body.email)



    def test_get_contact_found(self):
        self.session.query().filter().first.return_value = self.contact
        result = get_contact(contact_id=1, db=self.session)
        self.assertEqual(result, self.contact)

    def test_get_contact_not_found(self):
        # Мокаем возвращаемое значение запроса
        self.session.query().filter().first.return_value = None
        result = get_contact(contact_id=1, db=self.session)
        self.assertIsNone(result)

    def test_get_contacts(self):
        contacts = [self.contact, Contact(id=2, first_name="Jane", last_name="Doe")]
        self.session.query().offset().limit().all.return_value = contacts
        result = get_contacts(skip=0, limit=10, db=self.session)
        self.assertEqual(result, contacts)

    def test_delete_contact_found(self):
        self.session.query().filter().first.return_value = self.contact
        result = delete_contact(contact_id=1, db=self.session)
        self.assertEqual(result, self.contact)

    def test_delete_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = delete_contact(contact_id=1, db=self.session)
        self.assertIsNone(result)

    def test_update_contact_found(self):
        # Мокаем получение контакта и обновление
        self.session.query().filter().first.return_value = self.contact
        result = update_contact(contact_id=1, contact_data=self.contact_update, db=self.session)
        self.assertEqual(result.first_name, self.contact_update.first_name)
        self.assertEqual(result.email, self.contact_update.email)

    def test_update_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = update_contact(contact_id=1, contact_data=self.contact_update, db=self.session)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
