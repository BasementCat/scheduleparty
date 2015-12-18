import logging
import os
import json

from bottle import Bottle

import multiconfig

from app.lib.apitools import ApiPlugin


config = multiconfig.getConfig('scheduleparty')
config.load(os.path.join(os.path.dirname(__file__), '..', 'config', 'config-base.json'))
# TODO: real env
config.load(os.path.join(os.path.dirname(__file__), '..', 'config', 'config-dev.json'))


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
            env = os.getenv('SCHEDULEPARTY_ENV', 'dev')

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


app = Bottle()

app.install(ApiPlugin())