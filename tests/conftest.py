import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# DB_URL must be set before importing app: it resolves the DB URL at import time.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DB_URL"] = "sqlite:///" + _db_path

import pytest  # noqa: E402
from app import app as flask_app, db  # noqa: E402


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
    with flask_app.test_client() as test_client:
        yield test_client
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


def pytest_sessionfinish(session, exitstatus):
    try:
        os.remove(_db_path)
    except OSError:
        pass