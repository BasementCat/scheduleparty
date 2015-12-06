import os
import json
import hashlib
import pickle

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bootstrap import Bootstrap

from app.lib.session import Session


apps = {}

db = SQLAlchemy()


class Config(object):
    CONFIG_DIRS = [
        os.path.join(os.sep, 'etc', 'ortalis'),
        os.path.expanduser(os.path.join('~', '.config', 'ortalis')),
        os.path.join(os.path.dirname(__file__), '..', 'config'),
    ]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_dicts(self, *dicts):
        conf = {}
        for dict_ in dicts:
            conf.update(dict_)
        assert conf, "No configuration to load"
        return self(**conf)

    @classmethod
    def from_files(self, *filenames):
        configs = []
        for filename in filenames:
            with open(filename, 'r') as fp:
                configs.append(json.load(fp))
        assert configs, "No files to load config from"
        return self.from_dicts(*configs)

    @classmethod
    def from_env(self, env=None):
        if env is None:
            env = os.getenv('ORTALIS_ENV', 'dev')

        files = []
        for dirname in self.CONFIG_DIRS:
            basefile = os.path.join(dirname, 'config-base.json')
            envfile = os.path.join(dirname, 'config-' + env + '.json')
            if os.path.exists(basefile):
                files.append(basefile)
            if os.path.exists(envfile):
                files.append(envfile)
        assert files, "No files to load config from for env: " + env
        return self.from_files(*files)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    Bootstrap(app)

    Session.install(app)

    from views import (
        index as index_view,
        user as user_view,
    )
    app.register_blueprint(index_view.app, url_prefix=None)
    app.register_blueprint(user_view.app, url_prefix='/user')

    return app


def get_app(config=None, env=None, force_new=False):
    global apps

    if config is None:
        config = Config.from_env(env=env)

    key = hashlib.sha256(pickle.dumps(config)).hexdigest()
    if force_new or key not in apps:
        apps[key] = create_app(config)
    return apps[key]
