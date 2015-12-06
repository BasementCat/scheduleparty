#!/usr/bin/python

import sys

from flask.ext.script import (
    Manager,
    Server,
    )
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand

from app import (
    get_app,
    db,
    )

from app.commands import (
    importer as importer_commands,
    test as test_commands,
    )

if __name__ == '__main__':
    # HAX
    env = None
    try:
        env_index = sys.argv.index('--env')
        env = sys.argv[env_index + 1]
        del sys.argv[env_index + 1]
        del sys.argv[env_index]
    except ValueError:
        # env is not in args
        pass
    except IndexError:
        raise Exception("No argument for --env")

    app = get_app(env=env)
    manager = Manager(app)

    migrate = Migrate(app, db)
    manager.add_command('db', MigrateCommand)

    @manager.command
    def runserver(host='0.0.0.0', port=8000, debug=True, reloader=True):
        app = get_app()
        app.run(host=host, port=port, debug=debug, use_debugger=debug, use_reloader=reloader)

    for mod in [importer_commands, test_commands]:
        if hasattr(mod, 'make_commands'):
            mod.make_commands(app, manager)

    manager.run()
