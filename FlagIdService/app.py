import argparse
import json
import logging
import os
import pathlib
import sqlite3
import sys
from threading import Lock
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, request

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "{asctime} - {levelname} - {name} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(file_formatter)
logger.addHandler(stream_handler)

if not load_dotenv():
    logger.critical("Failed to load .env file.")
    sys.exit(-1)

app = Flask(__name__)
lock = Lock()


@app.route("/health")
def health():
    """
    Simple health check as a sanity check for the tests

    Returns:
        ("ok", 200)
    """
    return "ok", 200


@app.route("/postFlagId", methods=["POST"])
def postFlagId():
    """
    Adds a new flagId to the database

    Args:
        serviceId (str): Name of the service
        teamId (int): Zero indexed id of the team
        round (int): Zero indexed current tick
        flagId (Json): Information about how to retrieve the flag

    Returns:
        ("Invalid token", 401) if the token is invalid
        ("Invalid round", 400) if `round` is an invalid number
        ("Invalid teamId", 400) if `teamId` is an invalid number
        ("Invalid serviceId", 400) if `serviceId` is an empty string
        ("ok", 200) if the flagId was successfully inserted
    """

    con: sqlite3.Connection = app.config["DB_CON"]
    data = request.get_json()

    token: str = data["token"]
    if token != app.config["APP_TOKEN"]:
        return "Invalid token", 401

    service_id: str = str(data["serviceId"])
    try:
        team_id: int = int(data["teamId"])
    except ValueError:
        return "Invalid teamId", 400
    try:
        round_id: int = int(data["round"])
    except ValueError:
        return "Invalid round", 400
    flag_id: Any = data["flagId"]

    if service_id == "":
        return "Invalid serviceId", 400

    if round_id < 0:
        return "Invalid round", 400

    if team_id < 0:
        return "Invalid teamId", 400

    with lock:
        cur = con.cursor()

        cur.execute(
            "INSERT INTO data VALUES(?, ?, ?, ?, ?)", (str(uuid4()), service_id, team_id, round_id, json.dumps(flag_id))
        )  # NOTE: Always assuming flag_id is a dict.

        con.commit()

    return "ok", 200


@app.route("/flagIds", methods=["GET"])
def flagIds():
    """
    Returns information about the last five valid flag ids.

    Args:
        service (Optional[str]): Name of the service to filter
        team (Optional[int]): Zero indexed id of the team to filter
        round (Optional[int]): Zero indexed number of the tick to filter

    Returns:
        ("Invalid tick", 400) if `round` is invalid
        ("Invalid service", 400) if `service` does not exist
        ("Invalid team", 400) if `team` does not exist
        (Json object, 200) if the request was valid, where the object is
        {
            service_name: str {
                team_id: str {
                    tick: str {
                        flag_id: json
                    }
                }
            }
        }
    """
    con: sqlite3.Connection = app.config["DB_CON"]
    cur = con.cursor()
    service_id: str = request.args.get("service", "")
    try:
        team_id: int = int(request.args.get("team", -1))
    except ValueError:
        return "Invalid team", 400
    try:
        round_id: int = int(request.args.get("round", -1))
    except ValueError:
        return "Invalid tick", 400

    return_data = {}

    services, teams, ticks = __get_data()

    if round_id != -1 and round_id not in ticks:
        return "Invalid tick", 400

    if service_id != "" and service_id not in services:
        return "Invalid service", 400

    if team_id != -1 and team_id not in teams:
        return "Invalid team", 400

    if len(ticks) == 0:
        return {}

    last_valid_tick = ticks[-1]

    query = "SELECT service, team, tick, flag_id FROM data WHERE tick >= ?"
    query_data: list[str | int] = [last_valid_tick]

    if service_id != "":
        query += " AND service = ?"
        query_data.append(service_id)

    if team_id != -1:
        query += " AND team = ?"
        query_data.append(team_id)

    if round_id != -1:
        query += " AND tick = ?"
        query_data.append(round_id)

    for result in cur.execute(query, query_data).fetchall():
        service, team, tick, flagId = result
        return_data.setdefault(service, {}).setdefault(team, {}).setdefault(tick, json.loads(flagId))

    return return_data


@app.route("/", methods=["GET"])
def root():
    """
    Returns the available services, teams and ticks

    Returns:
        {
            "services": list[str],
            "teams": list[str],
            "ticks": list[str],
        }
    """
    services, teams, ticks = __get_data()

    return {"services": services, "teams": [str(x) for x in teams], "ticks": [str(x) for x in ticks]}


def __get_data() -> tuple[list[str], list[int], list[int]]:
    """
    Gets the available and relevant data

    Returns:
        Tuple with:
            - List of the services as strings
            - List of the teams as int
            - List of the five last valid ticks as int
    """
    con: sqlite3.Connection = app.config["DB_CON"]
    cur = con.cursor()

    # cur.execute.fetchall returns a list of lists with just a single element inside each of the sublists
    # So we extract them, convert them, and flatten them to a single list

    services = [str(x[0]) for x in cur.execute("SELECT DISTINCT service FROM data").fetchall()]
    teams = [int(x[0]) for x in cur.execute("SELECT DISTINCT team FROM data").fetchall()]
    ticks = [int(x[0]) for x in cur.execute("SELECT DISTINCT tick FROM data ORDER BY tick DESC LIMIT 5").fetchall()]

    return (services, teams, ticks)


if __name__ == "__main__":
    exists = pathlib.Path("flagIds.db").exists()
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", help="Resets the persistence db", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect("flagIds.db", check_same_thread=False)
    app.config["DB_CON"] = con
    app.config["APP_TOKEN"] = os.getenv("APP_TOKEN")
    app.config["DEBUG"] = True

    if not exists or args.reset:
        con.execute("DROP TABLE IF EXISTS data")
        con.execute("""CREATE TABLE data (
                    uuid text PRIMARY KEY,
                    service text NOT NULL,
                    team int NOT NULL,
                    tick int NOT NULL,
                    flag_id blob NOT NULL
                    )""")

    app.run()
