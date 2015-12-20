import arrow

from bottle import Bottle
from bottleutils.database import Pagination

from sqlalchemy.orm.exc import NoResultFound

from app.models import (
    User,
    APIKey,
    Organization,
    )


app = Bottle()


@app.get('/')
@APIKey.authenticated
def organization_list(auth_user):
    return Pagination(Organization.query).json_response
