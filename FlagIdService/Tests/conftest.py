import sqlite3
from collections.abc import Generator

from flask import Flask
import pytest
from flask.testing import FlaskClient

from ..app import app


@pytest.fixture()
def app_fixture() -> Generator[Flask]:
    app.config.update({"TESTING": True, "APP_TOKEN": "TEST_TOKEN", "DB_CON": sqlite3.connect(":memory:")})

    con: sqlite3.Connection = app.config["DB_CON"]

    con.execute("DROP TABLE IF EXISTS data")
    con.execute("""CREATE TABLE data (
                uuid text PRIMARY KEY,
                service int NOT NULL,
                team int NOT NULL,
                tick int NOT NULL,
                flag_id blob NOT NULL
                )""")

    yield app

    con.close()


@pytest.fixture()
def client(app_fixture: Flask) -> FlaskClient:
    return app_fixture.test_client()
