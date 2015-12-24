import arrow

from bottle import (
    Bottle,
    request,
    )
from bottleutils.database import Pagination

from sqlalchemy.orm.exc import NoResultFound

from app.models import (
    ReadSession,
    WriteSession,
    User,
    APIKey,
    Organization,
    OrganizationUser,
    )


app = Bottle()


@app.get('/')
@APIKey.authenticated
def organization_list(auth_user):
    with ReadSession(closing=True) as session:
        return Pagination(session.query(Organization)).json_response


@app.put('/')
@APIKey.authenticated
def organization_create(auth_user):
    with WriteSession(closing=True) as session:
        organization = Organization.from_request(request.json)
        org_user = OrganizationUser(
            role='administrator',
            organization=organization,
            user=auth_user
        )
        session.add(organization)
        session.add(org_user)
        session.commit()
        return organization.to_json()
