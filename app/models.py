import inspect
import functools
import os
import uuid
import copy
from collections import OrderedDict

import bottle
import arrow
from slugify import slugify
import bcrypt
from bottleutils.database import SQLAlchemyJsonMixin
import jsonschema
# from dateutil.tz import tzfile
# from pytz import tzinfo
from datetime import tzinfo

import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload

import sqlalchemy_utils as sau

import app


Base = sa.ext.declarative.declarative_base()

read_engine = sa.create_engine(app.config.get('Database/Read') or app.config.get('Database/RW'), echo=app.config.get('Database/echo', False))
write_engine = sa.create_engine(app.config.get('Database/Write') or app.config.get('Database/RW'), echo=app.config.get('Database/echo', False))

Session = sa.orm.scoped_session(sa.orm.sessionmaker(bind=read_engine))


class SessionContext(object):
    def __init__(self, bind=None, closing=False):
        self.session = None
        self.bind = bind
        self.old_bind = None
        self.closing = closing

    def __enter__(self):
        if self.session is None:
            self.session = Session()
        if self.bind:
            self.old_bind = self.session.bind
            self.session.bind = self.bind
        return self.session

    def _commit_or_rollback(self, type, value, traceback):
        if type or value or traceback:
            self.session.rollback()
        else:
            self.session.commit()

    def _replace_bind(self, type, value, traceback):
        if self.old_bind:
            self.session.bind = self.old_bind
            self.bind = None

        if self.closing:
            self.session.close()
            self.session = None

    def __exit__(self, *args):
        self._commit_or_rollback(*args)
        self._replace_bind(*args)


class ReadSession(SessionContext):
    def __exit__(self, *args):
        self._replace_bind(*args)


class WriteSession(SessionContext):
    def __init__(self, *args, **kwargs):
        kwargs['bind'] = write_engine
        super(WriteSession, self).__init__(*args, **kwargs)


class ModelMeta(sa.ext.declarative.DeclarativeMeta):
    pass
    # @property
    # def read_session(cls):
    #     return read_session()

    # @property
    # def write_session(cls):
    #     return write_session()

    # @property
    # def query(cls):
    #     return cls.read_session.query(cls)


class Model(SQLAlchemyJsonMixin, Base):
    __metaclass__ = ModelMeta
    __abstract__ = True

    @classmethod
    def get_json_schema(self):
        schema = {'type': 'object', 'properties': {}, 'required': []}
        for cls in reversed(inspect.getmro(self)):
            if hasattr(cls, 'json_schema'):
                schema['properties'].update(cls.json_schema)
        schema['required'] = [k for k, v in schema['properties'].items() if not v.get('optional')]
        if not schema['required']:
            del schema['required']
        return schema

    @classmethod
    def validate_request(self, json_object, skip_invalid=True):
        if json_object is None:
            bottle.abort(400, "No JSON object could be parsed from the request")
        schema = self.get_json_schema()
        real_json_object = copy.deepcopy(json_object)
        invalid_keys = set(real_json_object.keys()) - set(schema['properties'].keys())
        if skip_invalid:
            real_json_object = {k: v for k, v in real_json_object.items() if k not in invalid_keys}
        else:
            for k in invalid_keys:
                if k in real_json_object:
                    bottle.abort(400, "Invalid key: " + k)
        try:
            jsonschema.validate(real_json_object, schema)
            return real_json_object
        except jsonschema.exceptions.ValidationError as e:
            raise bottle.HTTPError(status=400, body={'error': {'code': 400, 'message': e.message, 'data': {'validator': e.validator, 'value': e.validator_value}}})

    @classmethod
    def from_request(self, json_object, skip_invalid=True, **kwargs):
        out = self(**kwargs)
        for k, v in self.validate_request(json_object, skip_invalid=skip_invalid).items():
            setattr(out, k, v)
        return out

    def populate_from_request(self, json_object, skip_invalid=True):
        for k, v in self.validate_request(json_object, skip_invalid=skip_invalid).items():
            setattr(self, k, v)

    def to_json(self, *args, **kwargs):
        def _filter(item):
            if isinstance(item, list):
                return [_filter(v) for v in item]
            elif isinstance(item, dict):
                return {k: _filter(v) for k, v in item.items()}
            else:
                if isinstance(item, tzinfo):
                    # return item.tzname()
                    return str(item)
                return item
        return _filter(super(Model, self).to_json(*args, **kwargs))


class TimestampMixin(object):
    created_at = sa.Column(sau.ArrowType(), index=True, default=arrow.utcnow)
    updated_at = sa.Column(sau.ArrowType(), index=True, default=arrow.utcnow, onupdate=arrow.utcnow)


class NameDescMixin(object):
    name = sa.Column(sa.UnicodeText(), nullable=False)
    slug = sa.Column(sa.Unicode(255), nullable=False, unique=True)
    description = sa.Column(sa.UnicodeText())

    json_schema = {
        'name': {
            'type': 'string',
            'optional': False,
        },
        'description': {
            'type': 'string',
            'optional': True,
        },
    }

    @classmethod
    def slugify_name(self, name):
        return slugify(name, max_length=255, word_boundary=True, save_order=True)

    def __setattr__(self, key, value):
        super(NameDescMixin, self).__setattr__(key, value)
        if key == 'name':
            self.slug = self.slugify_name(value)


# permission_to_role = sa.Table('permission_to_role', Model.metadata,
#     sa.Column('parent_role_id', sa.BigInteger(), sa.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     sa.Column('child_permission_id', sa.BigInteger(), sa.ForeignKey('permission.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


# role_to_role = sa.Table('role_to_role', Model.metadata,
#     sa.Column('parent_role_id', sa.BigInteger(), sa.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     sa.Column('child_role_id', sa.BigInteger(), sa.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


# role_to_user = sa.Table('role_to_user', Model.metadata,
#     sa.Column('parent_user_id', sa.BigInteger(), sa.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     sa.Column('child_role_id', sa.BigInteger(), sa.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


class User(TimestampMixin, Model):
    __tablename__ = 'user'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    username = sa.Column(sa.Unicode(255), nullable=False, index=True, unique=True)
    username_slug = sa.Column(sa.Unicode(255), nullable=False, index=True, unique=True, default=u'')
    email = sa.Column(sa.Unicode(255), nullable=False, index=True)
    password = sa.Column(sau.PasswordType(schemes=['bcrypt']), nullable=False)
    timezone = sa.Column(sau.TimezoneType(backend='pytz'), default=lambda: app.config.get('Timezones/Default/User', app.config.get('Timezones/Default/App', 'UTC')))
    # email_verification_code = sa.Column(sa.String(64), index=True)
    # email_verification_expiration = sa.Column(sau.ArrowType(), index=True)
    # email_reset_code = sa.Column(sa.String(64), index=True)
    # email_reset_expiration = sa.Column(sau.ArrowType(), index=True)
    # panels = sa.orm.relationship('Panel', secondary='Presenter')

    @classmethod
    def slugify_username(self, username):
        return slugify(username, max_length=255, word_boundary=True, save_order=True)

    def __setattr__(self, key, value):
        super(User, self).__setattr__(key, value)
        if key == 'username':
            self.username_slug = self.slugify_username(value)

    def to_json(self, *args, **kwargs):
        out = super(User, self).to_json(*args, **kwargs)
        del out['password']
        del out['email']
        return out

    # @classmethod
    # def make_verification_code(self, groups=3, grouplen=2):
    #     return '-'.join([''.join(['{:02X}'.format(c) for c in map(ord, os.urandom(grouplen))]) for _ in range(groups)])

    # def start_verification(self):
    #     self.email_verification_code = self.make_verification_code()
    #     self.email_verification_expiration = arrow.utcnow() + parse_duration(current_app.config.get('EMAIL_VERIFICATION_TIMEOUT'))

    # @property
    # def email_verification_url(self):
    #     if self.email_verification_code:
    #         return url_for('user.verify_email', code=self.email_verification_code)
    #     return None


class APIKey(TimestampMixin, Model):
    __tablename__ = 'api_key'
    key = sa.Column(sa.String(36), primary_key=True, autoincrement=False)
    user_id = sa.Column(sa.BigInteger(), sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    user = sa.orm.relationship('User', backref=sa.orm.backref('api_keys'))
    expires_at = sa.Column(sau.ArrowType(), index=True)
    used_at = sa.Column(sau.ArrowType(), index=True)

    def __init__(self, *args, **kwargs):
        self.key = str(uuid.uuid4())
        super(APIKey, self).__init__(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return self.expires_at > arrow.utcnow()

    @classmethod
    def authenticated(self, callback):
        @functools.wraps(callback)
        def _authenticated_impl(*args, **kwargs):
            with ReadSession() as session:
                error = None
                try:
                    auth_method, given_key = bottle.request.headers['Authorization'].split(' ', 1)
                    assert auth_method == 'X-API-Key', "Invalid authorization method: " + auth_method
                    assert given_key, "No key provided in authorization header"
                    key = session.query(self).options(joinedload('user')).filter(self.key == given_key).one()
                    if not key.is_expired:
                        kwargs['auth_user'] = key.user
                        return callback(*args, **kwargs)
                    # Key is expired
                    error = "Your authentication key is expired"
                except KeyError as e:
                    # No authorization header
                    error = "No authentication was provided"
                except AssertionError as e:
                    # Something's wrong with the key
                    error = "Malformed authorization header: '" + bottle.request.headers['Authorization'] + "'"
                except NoResultFound as e:
                    # Can't find the key
                    error = "Invalid credentials"

                raise bottle.HTTPError(status=401, body=str(error), **{'WWW-Authenticate': 'X-API-Key'})
        return _authenticated_impl


class Organization(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'organization'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    website = sa.Column(sa.UnicodeText())

    json_schema = {
        'website': {
            'type': 'string',
            'optional': True,
        },
    }

    def require_role(self, user, role):
        try:
            with ReadSession() as session:
                org_user = session.query(OrganizationUser).filter(OrganizationUser.organization == self, OrganizationUser.user == user).one()
                user_role = OrganizationUser.available_roles.index(org_user.role)
                expected_role = OrganizationUser.available_roles.index(role)
                assert user_role <= expected_role
        except (NoResultFound, AssertionError):
            bottle.abort(403, "Permission denied")


class OrganizationUser(TimestampMixin, Model):
    available_roles = ['administrator', 'editor']
    __tablename__ = 'organization_user'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    role = sa.Column(sa.Enum(*available_roles), nullable=False, default='editor')
    organization_id = sa.Column(sa.BigInteger(), sa.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = sa.orm.relationship('Organization', backref=sa.orm.backref('users'))
    user_id = sa.Column(sa.BigInteger(), sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    user = sa.orm.relationship('User', backref=sa.orm.backref('organizations'))
    timezone = sa.Column(sau.TimezoneType(backend='pytz'), default=lambda: app.config.get('Timezones/Default/Organization', app.config.get('Timezones/Default/App', 'UTC')))

    json_schema = {
        'username': {
            'type': 'string',
            'optional': False,
        },
        'role': {
            'enum': available_roles,
            'optional': False,
        }
    }

    @property
    def username(self):
        if self.user:
            return self.user.username
        return None

    @username.setter
    def username(self, value):
        with ReadSession() as session:
            with session.no_autoflush:
                try:
                    self.user = session.query(User).filter(User.username_slug == User.slugify_username(value)).one()
                except NoResultFound:
                    bottle.abort(404, {'code': 404, 'message': 'No such user: "{}"'.format(value), 'data': {'slug': value}})


class Presenter(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'presenter'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    organization_id = sa.Column(sa.BigInteger(), sa.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = sa.orm.relationship('Organization', backref=sa.orm.backref('presenters'))
    user_id = sa.Column(sa.BigInteger(), sa.ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    user = sa.orm.relationship('User', backref=sa.orm.backref('presenters'))

    json_schema = {
        'username': {
            'type': 'string',
            'optional': True,
        },
    }

    @property
    def username(self):
        if self.user:
            return self.user.username
        return None

    @username.setter
    def username(self, value):
        with ReadSession() as session:
            with session.no_autoflush:
                try:
                    self.user = session.query(User).filter(User.username_slug == User.slugify_username(value)).one()
                except NoResultFound:
                    bottle.abort(404, {'code': 404, 'message': 'No such user: "{}"'.format(value), 'data': {'slug': value}})


class Venue(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'venue'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    organization_id = sa.Column(sa.BigInteger(), sa.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = sa.orm.relationship('Organization', backref=sa.orm.backref('venues'))


class Event(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'event'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    organization_id = sa.Column(sa.BigInteger(), sa.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = sa.orm.relationship('Organization', backref=sa.orm.backref('events'))
    inherit_description = sa.Column(sa.Boolean(), nullable=False, default=False)
    website = sa.Column(sa.UnicodeText())
    inherit_website = sa.Column(sa.Boolean(), nullable=False, default=True)
    starts_at = sa.Column(sau.ArrowType(), index=True)
    ends_at = sa.Column(sau.ArrowType(), index=True)
    all_day = sa.Column(sa.Boolean(), nullable=False, default=True)
    published_at = sa.Column(sau.ArrowType(), index=True)
    timezone = sa.Column(sau.TimezoneType(backend='pytz'), default=lambda: app.config.get('Timezones/Default/Event', app.config.get('Timezones/Default/App', 'UTC')))

    json_schema = {
        'inherit_description': {
            'type': 'boolean',
            'optional': True,
            'default': False,
        },
        'website': {
            'type': 'string',
            'optional': True,
        },
        'inherit_website': {
            'type': 'boolean',
            'optional': True,
            'default': True,
        },
        'starts_at': {
            'type': 'string',
            'optional': True,
        },
        'ends_at': {
            'type': 'string',
            'optional': True,
        },
        'all_day': {
            'type': 'boolean',
            'optional': True,
            'default': True,
        },
        'published': {
            'type': 'boolean',
            'optional': True,
        }
    }

    @property
    def published(self):
        return True if self.published_at else False

    @published.setter
    def published(self, value):
        if value:
            self.published_at = arrow.utcnow()
        else:
            self.published_at = None

    def to_json(self, *args, **kwargs):
        out = super(Event, self).to_json(*args, **kwargs)
        if self.inherit_description:
            out['description'] = self.organization.description
        if self.inherit_website:
            out['website'] = self.organization.website
        return out


class Panel(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'panel'
    id = sa.Column(sa.BigInteger(), primary_key=True)
    event_id = sa.Column(sa.BigInteger(), sa.ForeignKey('event.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    event = sa.orm.relationship('Event', backref=sa.orm.backref('panels'))
    venue_id = sa.Column(sa.BigInteger(), sa.ForeignKey('venue.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    venue = sa.orm.relationship('Venue', backref=sa.orm.backref('panels'))
    presenter_id = sa.Column(sa.BigInteger(), sa.ForeignKey('presenter.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    presenter = sa.orm.relationship('Presenter', backref=sa.orm.backref('panels'))
    starts_at = sa.Column(sau.ArrowType(), index=True)
    ends_at = sa.Column(sau.ArrowType(), index=True)
    tentative = sa.Column(sa.Boolean(), nullable=False, default=False)
    published_at = sa.Column(sau.ArrowType(), index=True)
    cancelled = sa.Column(sa.Boolean(), nullable=False, default=False)

    json_schema = {
        'venue': {
            'type': 'string',
            'optional': True,
        },
        'presenter': {
            'type': 'string',
            'optional': True,
        },
        'starts_at': {
            'type': 'string',
            'optional': True,
        },
        'ends_at': {
            'type': 'string',
            'optional': True,
        },
        'tentative': {
            'type': 'boolean',
            'optional': True,
            'default': False,
        },
        'published': {
            'type': 'boolean',
            'optional': True,
        },
        'cancelled': {
            'type': 'boolean',
            'optional': True,
        },
    }

    def __setattr__(self, key, value):
        if isinstance(value, basestring):
            with ReadSession() as session:
                with session.no_autoflush:
                    if key == 'venue':
                        try:
                            value = session.query(Venue).filter(Venue.organization == self.event.organization, Venue.slug == value).one()
                        except NoResultFound:
                            bottle.abort(404, {'code': 404, 'message': 'No such venue: "{}"'.format(value), 'data': {'slug': value}})
                    elif key == 'presenter':
                        try:
                            value = session.query(Presenter).filter(Presenter.organization == self.event.organization, Presenter.slug == value).one()
                        except NoResultFound:
                            bottle.abort(404, {'code': 404, 'message': 'No such presenter: "{}"'.format(value), 'data': {'slug': value}})
        super(Panel, self).__setattr__(key, value)

    @property
    def published(self):
        return True if self.published_at else False

    @published.setter
    def published(self, value):
        if value:
            self.published_at = arrow.utcnow()
        else:
            self.published_at = None
