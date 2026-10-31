import os
from pprint import pprint
import sqlite3
import sys
import tempfile
from typing import Generator
from uuid import uuid4

from flask.testing import FlaskClient
import pytest
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


def __generate_test_data() -> Generator[tuple[str, str, str]]:
    # 3 services, 4 teams, 6 ticks
    for service in range(3):
        for team in range(4):
            for tick in range(6):
                yield (str(service), str(team), str(tick))


def test_health_check(client: FlaskClient):
    response: TestResponse = client.get("/health")
    assert b"ok" == response.data
    assert 200 == response.status_code


def test_insertion(client: FlaskClient):
    for test in __generate_test_data():
        response: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": str(uuid4()),
                },
            },
        )
        assert response.text == "ok"


def test_root(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    response: TestResponse = client.get("/")
    assert response.status_code == 200

    response_json = response.get_json()

    for service, team, tick in __generate_test_data():
        assert service in response_json["services"]
        assert team in response_json["teams"]
        if tick == "0":
            assert tick not in response_json["ticks"]
        else:
            assert tick in response_json["ticks"]


def test_flag_id(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    response: TestResponse = client.get("/flagIds")
    assert response.status_code == 200

    response_json = response.get_json()

    for service, team, tick in __generate_test_data():
        assert service in response_json
        assert team in response_json[service]
        if tick == "0":
            assert tick not in response_json[service][team]
        else:
            assert tick in response_json[service][team]
            assert f"{service}_{team}_{tick}" == response_json[service][team][tick]["username"]


def test_flag_id_filter_service(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    for service in range(3):
        service = str(service)
        response: TestResponse = client.get(f"/flagIds?service={service}")
        assert response.status_code == 200

        response_json = response.get_json()

        for gen_service, team, tick in __generate_test_data():
            if gen_service == service:
                assert gen_service in response_json
            else:
                assert gen_service not in response_json
                continue
            assert team in response_json[gen_service]
            if tick == "0":
                assert tick not in response_json[gen_service][team]
            else:
                assert tick in response_json[gen_service][team]
                assert f"{gen_service}_{team}_{tick}" == response_json[gen_service][team][tick]["username"]


def test_flag_id_filter_team(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    for team in range(4):
        team = str(team)
        response: TestResponse = client.get(f"/flagIds?team={team}")
        assert response.status_code == 200

        response_json = response.get_json()

        for service, gen_team, tick in __generate_test_data():
            assert service in response_json
            if team == gen_team:
                assert gen_team in response_json[service]
            else:
                assert gen_team not in response_json[service]
                break
            if tick == "0":
                assert tick not in response_json[service][gen_team]
            else:
                assert tick in response_json[service][gen_team]
                assert f"{service}_{gen_team}_{tick}" == response_json[service][gen_team][tick]["username"]


def test_flag_id_filter_tick(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    for tick in range(6):
        tick = str(tick)
        response: TestResponse = client.get(f"/flagIds?round={tick}")

        if tick == "0":
            assert response.status_code == 410
            continue

        assert response.status_code == 200

        response_json = response.get_json()

        for service, team, gen_tick in __generate_test_data():
            assert service in response_json
            assert team in response_json[service]

            if gen_tick == tick:
                assert tick in response_json[service][team]
                assert f"{service}_{team}_{gen_tick}" == response_json[service][team][gen_tick]["username"]

            else:
                assert tick not in response_json[service][team]


def test_flag_id_filter_all(client: FlaskClient):
    for test in __generate_test_data():
        _: TestResponse = client.post(
            "/postFlagId",
            json={
                "token": app.config["APP_TOKEN"],
                "serviceId": test[0],
                "teamId": test[1],
                "round": test[2],
                "flagId": {
                    "username": f"{test[0]}_{test[1]}_{test[2]}",
                    "note_id": "50021da4-7851-4c1d-9e7b-6357c2ea3673",
                },
            },
        )

    for service, team, tick in __generate_test_data():
        tick = str(tick)
        response: TestResponse = client.get(f"/flagIds?round={tick}")

        if tick == "0":
            assert response.status_code == 410
            continue

        assert response.status_code == 200

        response_json = response.get_json()

        for gen_service, gen_team, gen_tick in __generate_test_data():
            if gen_service == service and gen_team == team and gen_tick == tick:
                assert gen_service in response_json
                assert gen_team in response_json[gen_service]
                assert tick in response_json[gen_service][gen_team]
                assert (
                    f"{gen_service}_{gen_team}_{gen_tick}" == response_json[gen_service][gen_team][gen_tick]["username"]
                )
            else:
                assert gen_service not in response_json
                assert gen_team not in response_json[gen_service]
                assert tick not in response_json[gen_service][gen_team]
