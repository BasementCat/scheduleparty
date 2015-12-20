import logging
import os
import json

from bottle import Bottle

import multiconfig
from bottleutils.apps import setup
from bottleutils.response import JsonResponsePlugin


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

def get_app():
    main_app = Bottle()

    from views.api.v1.user import app as api_v1_user_app
    from views.api.v1.organization import app as api_v1_organization_app

    apps = [
        [api_v1_user_app, '/v1.0/user'],
        [api_v1_organization_app, '/v1.0/organization'],
    ]

    plugins = [JsonResponsePlugin()]

    setup(
        main_app,
        sub_apps=apps,
        plugins=plugins,
        error_handler_generators=[JsonResponsePlugin.getErrorHandler],
    )

    return main_app