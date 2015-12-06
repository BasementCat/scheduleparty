import sys
import os
import glob
import subprocess

from app import db


class TestBase(object):
    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)

        self.assertions = 0

    def before_suite(self):
        pass

    def after_suite(self):
        pass

    def before_test(self):
        self.after_test()
        subprocess.check_output('./manage.py --env test db upgrade 2>&1', shell=True)

    def after_test(self):
        # TODO: get from config...
        db.session.execute('drop database if exists ortalis_test;')
        db.session.execute('create database if not exists ortalis_test;')

    def assertTrue(self, value, reason=None):
        self.assertions += 1
        if reason:
            assert value, reason
        else:
            assert value


__all__ = [os.path.basename(f)[:-3] for f in glob.glob(os.path.join(os.path.dirname(__file__), '*.py'))]
