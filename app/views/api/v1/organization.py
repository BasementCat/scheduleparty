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
    Venue,
    Event,
    Panel,
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

                    if 'organization_venue_slug' in kwargs:
                        try:
                            organization_venue = session.query(Venue) \
                                .filter(
                                    Venue.organization == organization,
                                    Venue.slug == kwargs['organization_venue_slug']
                                ) \
                                .one()
                            kwargs['organization_venue'] = organization_venue
                            del kwargs['organization_venue_slug']
                        except NoResultFound:
                            abort(404, {'code': 404, 'message': 'No such organization venue: "{}"'.format(kwargs['organization_venue_slug']), 'data': {'slug': kwargs['organization_venue_slug']}})

                    if 'organization_event_slug' in kwargs:
                        try:
                            organization_event = session.query(Event) \
                                .filter(
                                    Event.organization == organization,
                                    Event.slug == kwargs['organization_event_slug']
                                ) \
                                .one()
                            kwargs['organization_event'] = organization_event
                            del kwargs['organization_event_slug']
                        except NoResultFound:
                            abort(404, {'code': 404, 'message': 'No such organization event: "{}"'.format(kwargs['organization_event_slug']), 'data': {'slug': kwargs['organization_event_slug']}})

                        if 'event_panel_slug' in kwargs:
                            try:
                                event_panel = session.query(Panel) \
                                    .filter(
                                        Panel.event == organization_event,
                                        Panel.slug == kwargs['event_panel_slug']
                                    ) \
                                    .one()
                                kwargs['event_panel'] = event_panel
                                del kwargs['event_panel_slug']
                            except NoResultFound:
                                abort(404, {'code': 404, 'message': 'No such event panel: "{}"'.format(kwargs['event_panel_slug']), 'data': {'slug': kwargs['event_panel_slug']}})

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


@app.get('/<organization_slug>/venues')
@organization_slug()
def organization_venues_get(organization):
    return organization.to_json(with_relationships={'venues': {'user': None}})['venues']


@app.put('/<organization_slug>/venues')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_venues_create(auth_user, organization):
    with WriteSession() as session:
        with session.no_autoflush:
            org_venue = Venue.from_request(request.json)
            if session.query(Venue).filter(Venue.organization == organization, Venue.slug == org_venue.slug).first():
                abort(400, {'code': 400, 'message': 'That venue already exists on this organization', 'data': {'venue': org_venue.to_json()}})
            org_venue.organization = organization
            session.add(org_venue)
            session.commit()
            return organization.to_json(with_relationships={'venues': {'venue': None}})['venues']


@app.delete('/<organization_slug>/venues/<organization_venue_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_venues_create(auth_user, organization, organization_venue):
    with WriteSession() as session:
        with session.no_autoflush:
            session.delete(organization_venue)
            session.commit()
            return organization.to_json(with_relationships={'venues': {'venue': None}})['venues']


@app.get('/<organization_slug>/events')
@organization_slug()
def organization_events_get(organization):
    return organization.to_json(with_relationships={'events': None})['events']


@app.put('/<organization_slug>/events')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_events_create(auth_user, organization):
    with WriteSession() as session:
        with session.no_autoflush:
            org_event = Event.from_request(request.json)
            if session.query(Event).filter(Event.organization == organization, Event.slug == org_event.slug).first():
                abort(400, {'code': 400, 'message': 'That event already exists on this organization', 'data': {'event': org_event.to_json()}})
            org_event.organization = organization
            session.add(org_event)
            session.commit()
            return organization.to_json(with_relationships={'events': None})['events']


@app.get('/<organization_slug>/events/<organization_event_slug>')
@organization_slug()
def organization_events_create(organization, organization_event):
    return org_event.to_json()


@app.delete('/<organization_slug>/events/<organization_event_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_events_create(auth_user, organization, organization_event):
    with WriteSession() as session:
        with session.no_autoflush:
            session.delete(organization_event)
            session.commit()
            return organization.to_json(with_relationships={'events': None})['events']


@app.put('/<organization_slug>/events/<organization_event_slug>/panels')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_events_create(auth_user, organization, organization_event):
    with WriteSession() as session:
        with session.no_autoflush:
            event_panel = Panel.from_request(request.json, event=organization_event)
            if session.query(Panel).filter(Panel.event == organization_event, Panel.slug == event_panel.slug).first():
                abort(400, {'code': 400, 'message': 'That panel already exists on this event', 'data': {'panel': event_panel.to_json()}})
            session.add(event_panel)
            session.commit()
            return organization_event.to_json(with_relationships={'panels': {'venue': None, 'presenter': {'user': None}}})['panels']


@app.get('/<organization_slug>/events/<organization_event_slug>/panels')
@organization_slug()
def organization_events_create(organization, organization_event):
    return organization_event.to_json(with_relationships={'panels': {'venue': None, 'presenter': {'user': None}}})['panels']


@app.delete('/<organization_slug>/events/<organization_event_slug>/panels/<event_panel_slug>')
@APIKey.authenticated
@organization_slug(writing=True, role='editor')
def organization_events_create(auth_user, organization, organization_event, event_panel):
    with WriteSession() as session:
        with session.no_autoflush:
            session.delete(event_panel)
            session.commit()
            return organization_event.to_json(with_relationships={'panels': {'venue': None, 'presenter': {'user': None}}})['panels']
