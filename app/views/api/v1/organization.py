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
    User,
    Presenter,
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

                    if 'organization_user_slug' in kwargs:
                        try:
                            organization_user = session.query(OrganizationUser) \
                                .filter(
                                    OrganizationUser.organization == organization,
                                    OrganizationUser.user.has(User.username_slug == kwargs['organization_user_slug'])
                                ) \
                                .one()
                            kwargs['organization_user'] = organization_user
                            del kwargs['organization_user_slug']
                        except NoResultFound:
                            abort(404, {'code': 404, 'message': 'No such organization user: "{}"'.format(kwargs['organization_user_slug']), 'data': {'slug': kwargs['organization_user_slug']}})

                    if 'organization_presenter_slug' in kwargs:
                        try:
                            organization_presenter = session.query(Presenter) \
                                .filter(
                                    Presenter.organization == organization,
                                    (
                                        (Presenter.slug == kwargs['organization_presenter_slug']) |
                                        (Presenter.user.has(User.username_slug == kwargs['organization_presenter_slug']))
                                    )
                                ) \
                                .one()
                            kwargs['organization_presenter'] = organization_presenter
                            del kwargs['organization_presenter_slug']
                        except NoResultFound:
                            abort(404, {'code': 404, 'message': 'No such organization presenter: "{}"'.format(kwargs['organization_presenter_slug']), 'data': {'slug': kwargs['organization_presenter_slug']}})

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


@app.get('/<organization_slug>/users')
@APIKey.authenticated
@organization_slug(role='editor')
def organization_users_get(auth_user, organization):
    return organization.to_json(with_relationships={'users': {'user': None}})['users']


@app.put('/<organization_slug>/users')
@APIKey.authenticated
@organization_slug(writing=True, role='administrator')
def organization_users_create(auth_user, organization):
    with WriteSession() as session:
        with session.no_autoflush:
            org_user = OrganizationUser.from_request(request.json)
            if session.query(OrganizationUser).filter(OrganizationUser.organization == organization, OrganizationUser.user == org_user.user).first():
                abort(400, {'code': 400, 'message': 'That user already exists on this organization', 'data': {'user': org_user.user.to_json()}})
            org_user.organization = organization
            session.add(org_user)
            session.commit()
            return organization.to_json(with_relationships={'users': {'user': None}})['users']


@app.delete('/<organization_slug>/users/<organization_user_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='administrator')
def organization_users_create(auth_user, organization, organization_user):
    with WriteSession() as session:
        with session.no_autoflush:
            session.delete(organization_user)
            session.commit()
            return organization.to_json(with_relationships={'users': {'user': None}})['users']


@app.get('/<organization_slug>/presenters')
@organization_slug()
def organization_presenters_get(organization):
    return organization.to_json(with_relationships={'presenters': {'user': None}})['presenters']


@app.put('/<organization_slug>/presenters')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_presenters_create(auth_user, organization):
    with WriteSession() as session:
        with session.no_autoflush:
            org_presenter = Presenter.from_request(request.json)
            if session.query(Presenter).filter(Presenter.organization == organization, Presenter.slug == org_presenter.slug).first():
                abort(400, {'code': 400, 'message': 'That presenter already exists on this organization', 'data': {'presenter': org_presenter.to_json()}})
            if org_presenter.user and session.query(Presenter).filter(Presenter.organization == organization, Presenter.user == org_presenter.user).first():
                abort(400, {'code': 400, 'message': 'A presenter with that user already exists on this organization', 'data': {'presenter': org_presenter.to_json()}})
            org_presenter.organization = organization
            session.add(org_presenter)
            session.commit()
            return organization.to_json(with_relationships={'presenters': {'user': None}})['presenters']


@app.delete('/<organization_slug>/presenters/<organization_presenter_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_presenters_create(auth_user, organization, organization_presenter):
    with WriteSession() as session:
        with session.no_autoflush:
            session.delete(organization_presenter)
            session.commit()
            return organization.to_json(with_relationships={'presenters': {'user': None}})['presenters']