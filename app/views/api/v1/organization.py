import functools

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


def organization_slug(writing=False, role=None):
    def _organization_slug_outer(callback):
        @functools.wraps(callback)
        def _organization_slug_inner(*args, **kwargs):
            sessionmaker = WriteSession if writing else ReadSession
            with sessionmaker(closing=True) as session:
                if 'organization_slug' in kwargs:
                    try:
                        organization = session.query(Organization).filter(Organization.slug == kwargs['organization_slug']).one()
                        if role is not None:
                            organization.require_role(kwargs['auth_user'], role)
                        kwargs['organization'] = organization
                        del kwargs['organization_slug']
                    except NoResultFound:
                        abort(404, {'code': 404, 'message': 'No such organization: "{}"'.format(kwargs['organization_slug']), 'data': {'slug': kwargs['organization_slug']}})

                return callback(*args, **kwargs)
        return _organization_slug_inner
    return _organization_slug_outer


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


@app.get('/<organization_slug>')
@organization_slug()
def organization_get(organization):
    return organization.to_json()


@app.post('/<organization_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='administrator')
def organization_update(auth_user, organization):
    with WriteSession() as session:
        organization.populate_from_request(request.json)
        session.commit()
        return organization.to_json()
