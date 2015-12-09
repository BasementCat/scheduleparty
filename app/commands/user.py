from app import db
from app.models import (
    User,
    )


def make_commands(app, manager):
    @manager.command
    def user(create=False, username=None, password=None, email=None):
        if create:
            assert username and password and email, "--username, --password, and --email are required"
            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
        else:
            for user in User.query.all():
                print "{}\t{}".format(
                    user.username,
                    user.email
                )
