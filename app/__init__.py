import logging
import os
import json

from bottle import Bottle

import multiconfig

from app.lib.apitools import ApiPlugin


ENV = os.environ.get('SCHEDULEPARTY_ENV', 'dev')

config = multiconfig.getConfig('scheduleparty')
config.loadMany(
    candidate_directories=[
        os.path.join(os.sep, 'etc', 'scheduleparty'),
        os.path.expanduser(os.path.join('~', '.config', 'scheduleparty')),
        os.path.join(os.path.dirname(__file__), '..', 'config'),
    ],
    candidate_filenames=[
        'config-base',
        'config-' + ENV,
    ],
    candidate_extensions=[
        'json',
        'yaml',
    ],
)

logging.basicConfig()

app = Bottle()

app.install(ApiPlugin())