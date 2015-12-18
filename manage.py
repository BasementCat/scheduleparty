import bottle

from app import app as main_app


if __name__ == '__main__':
    bottle.run(
        app=main_app,
        server='wsgiref',
        host='127.0.0.1',
        port=8000,
        interval=1,
        reloader=True,
        quiet=False,
        plugins=None,
        debug=True,
        config=None,
    )