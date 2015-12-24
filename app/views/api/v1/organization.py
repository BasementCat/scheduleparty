import arrow

from bottle import (
    Bottle,
    request,
    abort,
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
        if session.query(Organization).filter(Organization.slug == organization.slug).first():
            abort(400, {'message': "An organization by that name already exists", 'code': 400, 'data': {'name': organization.name, 'slug': organization.slug}})
        org_user = OrganizationUser(
            role='administrator',
            organization=organization,
            user=auth_user
        )
        session.add(organization)
        session.add(org_user)
        session.commit()
        return organization.to_json()


@app.post('/<slug>')
@APIKey.authenticated
def organization_update(auth_user, slug):
    with WriteSession(closing=True) as session:
        try:
            organization = session.query(Organization).filter(Organization.slug == slug).one()
            organization.require_role(auth_user, 'administrator')
            organization.populate_from_request(request.json)
            session.commit()
            return organization.to_json()
        except NoResultFound:
            abort(404, {'code': 404, 'message': 'No such organization: "{}"'.format(slug), 'data': {'slug': slug}})
