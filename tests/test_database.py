import unittest
import os
# import browse
from browse.factory import create_web_app
from browse.models import db
from flask import Flask
from flask_testing import TestCase

TEST_DB = 'test.db'

class TestDatabase(TestCase):

    TESTING = True

    # TODO
    def create_app(self):
        app = create_web_app('config.py')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp' + os.path.join('/tmp', TEST_DB)
        # db.init_app(app)
        # db.drop_all()
        # db.create_all()

    # TODO
    def test_something(self):
        pass

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
