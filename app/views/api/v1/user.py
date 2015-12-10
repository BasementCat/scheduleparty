import arrow

from flask import (
    Blueprint,
    url_for,
    redirect,
    request,
    current_app,
    g,
    abort,
    )

from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.lib.apitools import (
    ApiError,
    returns_json,
    )
from app.models import (
    User,
    APIKey,
    )


app = Blueprint('v1_user', __name__)


@app.route('/token', methods=['POST'])
@returns_json
def token_new():
    try:
        user = User.query.filter(User.username == request.form['username']).one()
        if request.form['password'] == user.password:
            key = APIKey(
                user=user
            )
            db.session.add(key)
            db.session.commit()
            return key.key
    except KeyError:
        raise ApiError(400, "Username and password are required")
    except NoResultFound:
        pass

    raise ApiError(400, "Invalid username or password")


@app.route('/token', methods=['GET'])
@APIKey.authenticated
@returns_json
def token_list(auth_user):
    return [
        key.to_json()
        for key
        in auth_user.api_keys
        if not key.is_expired
    ]
