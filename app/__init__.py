import logging
import os
import json
import hashlib
import pickle

from werkzeug.exceptions import default_exceptions

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bootstrap import Bootstrap

from app.lib.apitools import json_error_handler


apps = {}

db = SQLAlchemy()

logging.basicConfig()


class Config(object):
    CONFIG_DIRS = [
        os.path.join(os.sep, 'etc', 'scheduleparty'),
        os.path.expanduser(os.path.join('~', '.config', 'scheduleparty')),
        os.path.join(os.path.dirname(__file__), '..', 'config'),
    ]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        # # Global configs that cannot be overridden
        # self.TRAP_HTTP_EXCEPTIONS = False

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

    for code in default_exceptions.iterkeys():
        app.errorhandler(code)(json_error_handler)
    app.errorhandler(Exception)(json_error_handler)

    from views.api.v1 import (
        user as api_v1_user_view,
        )
    for blueprint, prefix in ((api_v1_user_view.app, '/api/v1.0/user'),):
        app.register_blueprint(blueprint, url_prefix=prefix)

    return app


def get_app(config=None, env=None, force_new=False):
    global apps

    if config is None:
        config = Config.from_env(env=env)

    key = hashlib.sha256(pickle.dumps(config)).hexdigest()
    if force_new or key not in apps:
        apps[key] = create_app(config)
    return apps[key]
