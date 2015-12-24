from sqlalchemy.orm.exc import NoResultFound

from app.lib.commands import option
from app.models import (
    ReadSession,
    WriteSession,
    User,
    )

@option('--create')
@option('--show')
@option('--password')
@option('--email')
def user(create=None, show=None, password=None, email=None):
    if create:
        assert password and email, "--password, and --email are required"
        user = User(username=create, password=password, email=email)
        with WriteSession(closing=True) as session:
            session.add(user)
    elif show:
        with ReadSession(closing=True) as session:
            user = session.query(User).filter(User.username.like(show) | User.username_slug.like(show)).one()
            print "{}\t{}".format(user.username, user.email)
            for key in user.api_keys:
                print key.key
    else:
        with ReadSession(closing=True) as session:
            for user in session.query(User).all():
                print "{}\t{}".format(
                    user.username,
                    user.email
                )
