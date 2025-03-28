import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import pytest
from flask import Flask

from routes.decklists import decklists_bp

# Sentinel bucket for testing
SENTINEL_BUCKETS = [{"id": "sentinel_bucket"}]


class DummyStorage:
    def list_buckets(self):
        """Return a sentinel list of buckets."""
        return SENTINEL_BUCKETS


class DummySupabase:
    def __init__(self):
        self.storage = DummyStorage()


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = Flask(__name__)
    app.register_blueprint(decklists_bp)
    app.testing = True
    return app


@pytest.fixture
def client(app):
    """Provide a test client for the Flask app."""
    return app.test_client()


def test_list_buckets_success(monkeypatch, client):
    """
    Test the /list-buckets route returns the sentinel buckets list.
    """
    monkeypatch.setattr("routes.decklists.supabase", DummySupabase())
    response = client.get("/list-buckets")
    data = response.get_json()
    assert response.status_code == 200
    assert data == SENTINEL_BUCKETS


def test_list_buckets_error(monkeypatch, client):
    """
    Test the /list-buckets route handles exceptions and returns a 500 error.
    """

    def failing_list_buckets():
        raise Exception("Sentinel error")

    class FailingStorage:
        def list_buckets(self):
            return failing_list_buckets()

    class FailingSupabase:
        def __init__(self):
            self.storage = FailingStorage()

    monkeypatch.setattr("routes.decklists.supabase", FailingSupabase())
    response = client.get("/list-buckets")
    data = response.get_json()
    assert response.status_code == 500
    assert "Sentinel error" in data.get("error", "")
