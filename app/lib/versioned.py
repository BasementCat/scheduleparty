from flask import (
    Blueprint,
    url_for,
    )


class Versioned(object):
    def __init__(self, version):
        self.version = 'v' + str(version)

    def _make_versioned(self, string):
        return self.version.replace('.', '_') + '__' + string

    def Blueprint(self, *args, **kwargs):
        args = list(args)
        args[0] = self._make_versioned(args[0])
        prefix = ''
        if 'url_prefix' in kwargs:
            prefix = kwargs['url_prefix']
            del kwargs['url_prefix']
        prefix = '/' + self.version + prefix
        out = Blueprint(*args, **kwargs)
        out._extra_url_prefix = prefix
        return out

    def url_for(self, *args, **kwargs):
        args = list(args)
        args[0] = self._make_versioned(args[0])
        return url_for(*args, **kwargs)
