import bottle

import app
from app.lib.commands import option, command

@command
def runserver():
    #     if sys.argv[1] == 'db':
    #         call(['alembic', '-c', os.path.join(os.path.dirname(__file__), 'migrations', 'alembic.ini')] + sys.argv[2:])
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
