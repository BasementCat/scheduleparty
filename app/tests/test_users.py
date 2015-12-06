from app.tests import TestBase
from app import db
from app.models import (
    User,
    # UserRelationship,
    )

class TestUsers(TestBase):
    def test_new_user(self):
        u = User(username='foo bar.')
        u.set_password('qwerty')

        self.assertTrue(u.username_slug == 'foo-bar')
        self.assertTrue(u.check_password('qwerty'))

    def test_user_friends(self):
        a = User()
        b = User()
        c = User()
        rel = UserRelationship(source_user=a, target_user=b, relationship=u'FRIEND')

        db.session.add_all([a, b, c, rel])
        db.session.commit()
        a_id = a.id
        b_id = b.id
        c_id = c.id
        del a, b, c, rel

        a = User.query.get(a_id)
        b = User.query.get(b_id)
        c = User.query.get(c_id)

        self.assertTrue(len(list(a.friends)) == 1)
        self.assertTrue(list(a.friends)[0].id == b.id)
