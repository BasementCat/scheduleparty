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

def get_app():
    main_app = Bottle()

    from views.api.v1.user import app as api_v1_user_app

    apps = [
        [main_app, None],
        [api_v1_user_app, '/v1.0/user'],
    ]

    plugins = [ApiPlugin()]

    for app, mountpoint in apps:
        if mountpoint is not None:
            main_app.mount(mountpoint, app)
        for plugin in plugins:
            app.install(plugin)

    return main_app