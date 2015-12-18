import arrow

from bottle import (
    Bottle,
    request,
    )

from sqlalchemy.orm.exc import NoResultFound

from app.lib.apitools import ApiError
from app.models import (
    write_session,
    User,
    APIKey,
    )


app = Bottle()


@app.post('/token')
def token_new():
    try:
        user = User.query.filter(User.username == request.form['username']).one()
        if request.form['password'] == user.password:
            key = APIKey(
                user=user
            )
            write_session().add(key)
            write_session().commit()
            return key.key
    except KeyError:
        raise ApiError(400, "Username and password are required")
    except NoResultFound:
        pass

    raise ApiError(400, "Invalid username or password")


@app.get('/token')
@APIKey.authenticated
def token_list(auth_user):
    return [
        key.to_json()
        for key
        in auth_user.api_keys
        if not key.is_expired
    ]
