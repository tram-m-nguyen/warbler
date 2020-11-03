"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from flask import session
from models import db, connect_db, Message, User, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)

        # self.testuser2 = User.signup(username="testuser2",
        #                             email="test2@test.com",
        #                             password="testuser2",
        #                             image_url=None)

        # self.testuser3 = User.signup(username="testuser3",
        #                             email="test3@test.com",
        #                             password="testuser3",
        #                             image_url=None)
        db.session.add(testuser)
        db.session.commit()
        db.session.add(testuser1)
        db.session.commit()

        # session[CURR_USER_KEY] = self.testuser.id
        # testuser follower: testuser1, testuser3
        # testuser1 followers: testuser2, testuser
        # self.testuser.followers.append(self.testuser1)
        # self.testuser1.followers.append(self.testuser2)
        # self.testuser1.followers.append(self.testuser)
        # self.testuser.followers.append(self.testuser3)
        self.testuser_id = testuser.id
        self.testuser1_id = testuser.id
        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()


    def test_show_following(self):
        """Can they see who they're following"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.testuser_id
            print('follower', change_session[CURR_USER_KEY])

            # go to testuserid_1 to see who they're following
            resp = client.get(f"/users/{self.testuser1_id}/following")
            html = resp.get_data(as_text=True)

            follow = Follows(user_being_followed_id=self.testuser_id, 
                            user_following_id=self.testuser1_id)

            # testuser_id1 is following testuser_id
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<a href="/users/{self.testuser_id}"', html)

            
    def test_show_follower(self):
        """Can they see who their  followers are"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.testuser_id
            print('follower', change_session[CURR_USER_KEY])

            # go to testuserid_1 to see who they're following
            resp = client.get(f"/users/{self.testuser_id}/followers")
            html = resp.get_data(as_text=True)

            follow = Follows(user_being_followed_id=self.testuser_id, 
                            user_following_id=self.testuser1_id)

            # testuser_id1 is following testuser_id
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<a href="/users/{self.testuser1_id}"', html)











    # def test_add_message(self):
    #     """Can use add a message?"""

    #     # Since we need to change the session to mimic logging in,
    #     # we need to use the changing-session trick:

    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         # Now, that session setting is saved, so we can have
    #         # the rest of ours test

    #         resp = c.post("/messages/new", data={"text": "Hello"})

    #         # Make sure it redirects
    #         self.assertEqual(resp.status_code, 302)

    #         msg = Message.query.one()
    #         self.assertEqual(msg.text, "Hello")
