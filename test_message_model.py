"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from flask_bcrypt import Bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

app.config['TESTING'] = True

db.drop_all()
db.create_all()

bcrypt = Bcrypt()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # Hashed password for user
        hashed_password = bcrypt.generate_password_hash('HASHED_PASSWORD').decode('UTF-8')

        user = User(
            email="test@test.com",
            username="testuser",
            password=hashed_password,
            location="SF"
        )

        # Hashed password for user
        hashed_password1 = bcrypt.generate_password_hash('HASHED_PASSWORD1').decode('UTF-8')

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1",
            location="NY"
        )
        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD1",
            location="NY"
        )
        db.session.add_all([user, user1, user2])
        db.session.commit()

        self.user = user
        self.user1 = user1
        self.user2 = user2
        self.client = app.test_client()

        message = Message(text='Our first message', user_id=self.user.id)
        message1 = Message(text='123', user_id=self.user1.id)

        db.session.add_all([message, message1])
        db.session.commit()

        self.message = message
        self.message1 = message1



    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_message_model(self):
        '''Does the basic model work?'''

        self.assertEqual(self.message.text, 'Our first message')
        self.assertNotEqual(self.message1.text, "SF")
        self.assertIsInstance(Message(text='abc', user_id=self.user1),
                                Message)

        # Testing the User/Message relationship
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.message.user_id, self.user.id)
        self.assertEqual(self.message.user, self.user)

