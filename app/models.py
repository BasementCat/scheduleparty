import functools
import os
import uuid

import arrow
from slugify import slugify
import bcrypt

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask import (
    current_app,
    abort,
    g,
    request,
    )

import sqlalchemy_utils as sau

# from app.lib.times import parse_duration

from app import db
from app.lib.apitools import ApiError


class Model(db.Model):
    __abstract__ = True

    def to_json(self):
        out = {}
        for attrname, clsattr in vars(self.__class__).items():
            if isinstance(clsattr, InstrumentedAttribute):
                attr = getattr(self, attrname)
                if isinstance(attr, arrow.arrow.Arrow):
                    attr = str(attr)
                elif isinstance(attr, Model):
                    continue
                out[attrname] = attr
        return out


class TimestampMixin(object):
    created_at = db.Column(sau.ArrowType(), index=True, default=arrow.utcnow)
    updated_at = db.Column(sau.ArrowType(), index=True, default=arrow.utcnow, onupdate=arrow.utcnow)


class NameDescMixin(object):
    name = db.Column(db.UnicodeText(), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False, unique=True)
    description = db.Column(db.UnicodeText())

    @classmethod
    def slugify_name(self, name):
        return slugify(name, max_length=255, word_boundary=True, save_order=True)

    def __setattr__(self, key, value):
        super(NameDescMixin, self).__setattr__(key, value)
        if key == 'name':
            self.slug = self.slugify_name(value)


# permission_to_role = db.Table('permission_to_role', Model.metadata,
#     db.Column('parent_role_id', db.BigInteger(), db.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     db.Column('child_permission_id', db.BigInteger(), db.ForeignKey('permission.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


# role_to_role = db.Table('role_to_role', Model.metadata,
#     db.Column('parent_role_id', db.BigInteger(), db.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     db.Column('child_role_id', db.BigInteger(), db.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


# role_to_user = db.Table('role_to_user', Model.metadata,
#     db.Column('parent_user_id', db.BigInteger(), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
#     db.Column('child_role_id', db.BigInteger(), db.ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
# )


class User(TimestampMixin, Model):
    __tablename__ = 'user'
    id = db.Column(db.BigInteger(), primary_key=True)
    username = db.Column(db.Unicode(255), nullable=False, index=True, unique=True)
    username_slug = db.Column(db.Unicode(255), nullable=False, index=True, unique=True, default=u'')
    email = db.Column(db.Unicode(255), nullable=False, index=True)
    password = db.Column(sau.PasswordType(schemes=['bcrypt']), nullable=False)
    # email_verification_code = db.Column(db.String(64), index=True)
    # email_verification_expiration = db.Column(sau.ArrowType(), index=True)
    # email_reset_code = db.Column(db.String(64), index=True)
    # email_reset_expiration = db.Column(sau.ArrowType(), index=True)
    # panels = db.relationship('Panel', secondary='Presenter')

    @classmethod
    def slugify_username(self, username):
        return slugify(username, max_length=255, word_boundary=True, save_order=True)

    def __setattr__(self, key, value):
        super(User, self).__setattr__(key, value)
        if key == 'username':
            self.username_slug = self.slugify_username(value)

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
    key = db.Column(db.String(36), primary_key=True, autoincrement=False)
    user_id = db.Column(db.BigInteger(), db.ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('api_keys'))
    expires_at = db.Column(sau.ArrowType(), index=True)
    used_at = db.Column(sau.ArrowType(), index=True)

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
            error = None
            try:
                auth_method, given_key = request.headers['Authorization'].split(' ', 1)
                assert auth_method == 'X-API-Key', "Invalid authorization method: " + auth_method
                assert given_key, "No key provided in authorization header"
                key = self.query.options(joinedload('user')).filter(self.key == given_key).one()
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
                error = "Malformed authorization header: '" + request.headers['Authorization'] + "'"
            except NoResultFound as e:
                # Can't find the key
                error = "Invalid credentials"

            raise ApiError(401, str(error), None, {'WWW-Authenticate': 'X-API-Key'})
        return _authenticated_impl


class Organization(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'organization'
    id = db.Column(db.BigInteger(), primary_key=True)
    website = db.Column(db.UnicodeText())


class Presenter(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'presenter'
    id = db.Column(db.BigInteger(), primary_key=True)
    organization_id = db.Column(db.BigInteger(), db.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = db.relationship('Organization', backref=db.backref('presenters'))
    user_id = db.Column(db.BigInteger(), db.ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    user = db.relationship('User', backref=db.backref('presenters'))


class Event(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'event'
    id = db.Column(db.BigInteger(), primary_key=True)
    organization_id = db.Column(db.BigInteger(), db.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = db.relationship('Organization', backref=db.backref('events'))
    inherit_description = db.Column(db.Boolean(), nullable=False, default=False)
    website = db.Column(db.UnicodeText())
    inherit_website = db.Column(db.Boolean(), nullable=False, default=True)
    starts_at = db.Column(sau.ArrowType(), index=True)
    ends_at = db.Column(sau.ArrowType(), index=True)
    all_day = db.Column(db.Boolean(), nullable=False, default=True)
    published_at = db.Column(sau.ArrowType(), index=True)


class Venue(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'venue'
    id = db.Column(db.BigInteger(), primary_key=True)
    organization_id = db.Column(db.BigInteger(), db.ForeignKey('organization.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    organization = db.relationship('Organization', backref=db.backref('venues'))


class Panel(NameDescMixin, TimestampMixin, Model):
    __tablename__ = 'panel'
    id = db.Column(db.BigInteger(), primary_key=True)
    event_id = db.Column(db.BigInteger(), db.ForeignKey('event.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, index=True)
    event = db.relationship('Event', backref=db.backref('panels'))
    venue_id = db.Column(db.BigInteger(), db.ForeignKey('venue.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    venue = db.relationship('Venue', backref=db.backref('panels'))
    presenter_id = db.Column(db.BigInteger(), db.ForeignKey('presenter.id', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    presenter = db.relationship('Presenter', backref=db.backref('panels'))
    starts_at = db.Column(sau.ArrowType(), nullable=False, index=True)
    ends_at = db.Column(sau.ArrowType(), nullable=False, index=True)
    tentative = db.Column(db.Boolean(), nullable=False, default=False)
    published_at = db.Column(sau.ArrowType(), index=True)
    cancelled = db.Column(db.Boolean(), nullable=False, default=False)
