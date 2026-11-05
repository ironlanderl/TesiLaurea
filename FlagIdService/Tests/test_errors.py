import os
import sqlite3
import tempfile
from collections.abc import Generator
from uuid import uuid4

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from ..app import app


@pytest.fixture
def client() -> Generator[FlaskClient]:
    tempdir = tempfile.mkdtemp()
    app.config.update({"TESTING": True, "APP_TOKEN": "TEST_TOKEN", "DB_CON": sqlite3.connect(f"{tempdir}/db.sql")})

    con: sqlite3.Connection = app.config["DB_CON"]

    con.execute("DROP TABLE IF EXISTS data")
    con.execute("""CREATE TABLE data (
                uuid text PRIMARY KEY,
                service int NOT NULL,
                team int NOT NULL,
                tick int NOT NULL,
                flag_id blob NOT NULL
                )""")

    with app.test_client() as client:
        yield client

    con.close()
    os.system(f"rm -rf {tempdir}")


def test_health_check(client: FlaskClient):
    response: TestResponse = client.get("/health")
    assert b"ok" == response.data
    assert 200 == response.status_code


def test_insert_bad_token(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": "Invalid_Token",
            "serviceId": "TestService",
            "teamId": 0,
            "round": 0,
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 401


def test_insert_bad_serviceId(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": app.config["APP_TOKEN"],
            "serviceId": "",
            "teamId": 0,
            "round": 0,
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 400
    assert response.text == "Invalid serviceId"


def test_insert_bad_teamId(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": app.config["APP_TOKEN"],
            "serviceId": "TestService",
            "teamId": -1,
            "round": 0,
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 400
    assert response.text == "Invalid teamId"


def test_insert_string_teamId(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": app.config["APP_TOKEN"],
            "serviceId": "TestService",
            "teamId": "TestString",
            "round": 0,
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 400
    assert response.text == "Invalid teamId"


def test_insert_bad_round(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": app.config["APP_TOKEN"],
            "serviceId": "TestService",
            "teamId": 0,
            "round": -1,
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 400
    assert response.text == "Invalid round"


def test_insert_string_round(client: FlaskClient):
    response: TestResponse = client.post(
        "/postFlagId",
        json={
            "token": app.config["APP_TOKEN"],
            "serviceId": "TestService",
            "teamId": 0,
            "round": "TestString",
            "flagId": {
                "username": "Username",
                "note_id": str(uuid4()),
            },
        },
    )
    assert response.status_code == 400
    assert response.text == "Invalid round"


def test_flagId_bad_service(client: FlaskClient):
    response: TestResponse = client.get(
        "/flagIds?service=NotExisting",
    )
    assert response.status_code == 400
    assert response.text == "Invalid service"


def test_flagIds_bad_round(client: FlaskClient):
    response: TestResponse = client.get(
        "/flagIds?round=40",
    )
    assert response.status_code == 400
    assert response.text == "Invalid tick"


def test_flagIds_string_round(client: FlaskClient):
    response: TestResponse = client.get(
        "/flagIds?round=test_string",
    )
    assert response.status_code == 400
    assert response.text == "Invalid tick"


def test_flagIds_bad_team(client: FlaskClient):
    response: TestResponse = client.get(
        "/flagIds?team=40",
    )
    assert response.status_code == 400
    assert response.text == "Invalid team"


def test_flagIds_string_team(client: FlaskClient):
    response: TestResponse = client.get(
        "/flagIds?team=test_string",
    )
    assert response.status_code == 400
    assert response.text == "Invalid team"
