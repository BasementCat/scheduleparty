from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.models import (
    User,
    )


def make_commands(app, manager):
    @manager.command
    def user(create=None, show=None, password=None, email=None):
        if create:
            assert password and email, "--password, and --email are required"
            user = User(username=create, password=password, email=email)
            db.session.add(user)
            db.session.commit()
        elif show:
            user = User.query.filter(User.username.like(show) | User.username_slug.like(show)).one()
            print "{}\t{}".format(user.username, user.email)
            for key in user.api_keys:
                print key.key
        else:
            for user in User.query.all():
                print "{}\t{}".format(
                    user.username,
                    user.email
                )
