"""
tests/conftest.py

Shared fixtures for the test suite.

Env vars are set before any app import so that config.py picks them up
at class-definition time. load_dotenv() in config.py does not override
vars that are already present in the environment.
"""

import os

# Must be set before any app module is imported so config.py picks them up.
# load_dotenv() in config.py does not override vars already in the environment.
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest'
os.environ['ADMIN_PASSWORD'] = 'test-password'

# In CI, DATABASE_URL is injected by the workflow and points at a PostgreSQL
# service container. Locally, fall back to a temp SQLite file so tests run
# without requiring a local PostgreSQL instance.
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/portfolio_test.db'

import pytest
from app.app import create_app
from app.models.models import Project, db as _db


@pytest.fixture(scope='session')
def app():
    _app = create_app()
    _app.config['TESTING'] = True
    _app.config['WTF_CSRF_ENABLED'] = False
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_db(app):
    project = Project(
        title='Test Project',
        slug='test-project',
        short_description='A test project.',
        full_description='Full description of the test project.',
        primary_category='web',
        featured=True,
    )
    _db.session.add(project)
    _db.session.commit()
    yield
    _db.session.query(Project).delete()
    _db.session.commit()
