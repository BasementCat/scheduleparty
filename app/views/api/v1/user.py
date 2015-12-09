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
    JSONResponse,
    )
from app.models import (
    User,
    )


app = Blueprint('v1_user', __name__)


@app.route('/token', methods=['POST'])
def token_new():
    try:
        user = User.query.filter(User.username == request.form['username']).one()
        if request.form['password'] == user.password:
            return "ok"
    except KeyError:
        raise ApiError(400, "Username and password are required")
    except NoResultFound:
        pass

    raise ApiError(400, "Invalid username or password")
