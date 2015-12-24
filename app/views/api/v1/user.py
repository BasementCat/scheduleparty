import arrow

from bottle import (
    Bottle,
    request,
    abort,
    )

from sqlalchemy.orm.exc import NoResultFound

from app.models import (
    ReadSession,
    WriteSession,
    User,
    APIKey,
    )


app = Bottle()


@app.post('/token')
def token_new():
    try:
        with WriteSession(closing=True) as session:
            user = session.query(User).filter(User.username == unicode(request.forms['username'])).one()
            if request.forms['password'] == user.password:
                key = APIKey(
                    user=user
                )
                session.add(key)
                return key.to_json()
    except KeyError:
        abort(400, "Username and password are required")
    except NoResultFound:
        pass

    raise abort(400, "Invalid username or password")


@app.get('/token')
@APIKey.authenticated
def token_list(auth_user):
    with ReadSession(closing=True):
        return [
            key.to_json()
            for key
            in auth_user.api_keys
            if not key.is_expired
        ]
