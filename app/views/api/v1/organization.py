import arrow

from bottle import Bottle

from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.lib.apitools import (
    returns_json,
    paginated,
    )
from app.models import (
    User,
    APIKey,
    Organization,
    )


app = Bottle()


@app.get('/')
@APIKey.authenticated
def organization_list(auth_user):
    return paginated(Organization.query)
