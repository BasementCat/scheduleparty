import os
import sys
import bottle
import logging
from subprocess import call

import app

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'db':
            call(['alembic', '-c', os.path.join(os.path.dirname(__file__), 'migrations', 'alembic.ini')] + sys.argv[2:])
        elif sys.argv[1] == 'runserver':
            bottle.run(
                app=app.get_app(),
                **app.config.get(
                    'Server',
                    {
                        'server': 'wsgiref',
                        'host': '127.0.0.1',
                        'port': 8000,
                        'interval': 1,
                        'reloader': True,
                        'quiet': False,
                        'plugins': None,
                        'debug': True,
                        'config': None,
                    }
                )
            )
        else:
            logger.error("Don't know what to do with %s", sys.argv[1])
    else:
        logger.error("No arguments")