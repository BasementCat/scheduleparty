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
    paginated,
    )
from app.models import (
    User,
    APIKey,
    Organization,
    )


app = Blueprint('v1_organization', __name__)


@app.route('/', methods=['GET'])
@APIKey.authenticated
@returns_json
def organization_list(auth_user):
    return paginated(Organization.query)
