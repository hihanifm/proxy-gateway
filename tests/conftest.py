import pytest
from fastapi.testclient import TestClient

from gateway.adapters.stub import StubAdapter
from gateway.main import create_app


@pytest.fixture()
def app():
    application = create_app()
    application.state.adapter = StubAdapter()
    return application


@pytest.fixture()
def client(app):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
