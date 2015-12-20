import arrow

from bottle import (
    Bottle,
    request,
    )
from bottleutils.database import Pagination

from sqlalchemy.orm.exc import NoResultFound

from app.models import (
    write_session,
    User,
    APIKey,
    Organization,
    OrganizationUser,
    )


app = Bottle()


@app.get('/')
@APIKey.authenticated
def organization_list(auth_user):
    return Pagination(Organization.query).json_response


@app.put('/')
@APIKey.authenticated
def organization_create(auth_user):
    # import pudb;pudb.set_trace()
    organization = Organization.from_request(request.json)
    org_user = OrganizationUser(
        role='administrator',
        organization=organization,
        user=auth_user
    )
    write_session().add(organization)
    write_session().add(org_user)
    write_session().commit()
    return organization.to_json()
