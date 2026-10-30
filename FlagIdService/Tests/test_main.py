import os
import sys
import tempfile
from typing import Generator

from flask.testing import FlaskClient
import pytest
from werkzeug.test import TestResponse


from ..app import app


@pytest.fixture
def client() -> Generator[FlaskClient]:
    print(os.getcwd(), file=sys.stderr)

    app.config.update({"TESTING": True})

    with app.test_client() as client:
        yield client


def test_health_check(client: FlaskClient):
    response: TestResponse = client.get("/health")
    assert b"ok" == response.data
    assert 200 == response.status_code
