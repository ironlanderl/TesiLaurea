import argparse
import json
import logging
import os
import pathlib
from threading import Lock
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, request
import sqlite3

load_dotenv()

logger = logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/health")
def health():
    return "ok", 200


@app.route("/postFlagId", methods=["POST"])
def postFlagId():

    con: sqlite3.Connection = app.config["DB_CON"]
    data = request.get_json()

    token: str = data["token"]
    if token != app.config["APP_TOKEN"]:
        return "Invalid token", 401

    service_id: int = data["serviceId"]
    team_id: int = data["teamId"]
    round_id: int = data["round"]
    flag_id: Any = data["flagId"]

    cur = con.cursor()

    cur.execute(
        "INSERT INTO data VALUES(?, ?, ?, ?, ?)", (str(uuid4()), service_id, team_id, round_id, json.dumps(flag_id))
    )  # NOTE: Always assuming flag_id is a dict.

    con.commit()

    return "ok", 200


@app.route("/flagIds", methods=["GET"])
def flagIds():
    con: sqlite3.Connection = app.config["DB_CON"]
    service_id: str = request.args.get("service", "")
    team_id: int = int(request.args.get("team", -1))
    round_id: int = int(request.args.get("round", -1))

    # TODO: Implement filters
    with lock:
        return json.dumps(state), {"Content-Type": "application/json"}


@app.route("/", methods=["GET"])
def root():

    con: sqlite3.Connection = app.config["DB_CON"]
    cur = con.cursor()

    # cur.execute.fetchall returns a list of lists with just a single element inside each of the sublists
    # So we extract them, convert them to strings, and flatten them to a single list

    services = [str(x[0]) for x in cur.execute("SELECT DISTINCT service FROM data").fetchall()]
    teams = [str(x[0]) for x in cur.execute("SELECT DISTINCT team FROM data").fetchall()]
    ticks = [str(x[0]) for x in cur.execute("SELECT DISTINCT tick FROM data ORDER BY tick DESC LIMIT 5").fetchall()]

    return {"services": services, "teams": teams, "ticks": ticks}


if __name__ == "__main__":
    exists = pathlib.Path("flagIds.db").exists()
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", help="Resets the persistence db", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect("flagIds.db")
    app.config["DB_CON"] = con
    app.config["APP_TOKEN"] = os.getenv("APP_TOKEN")

    if not exists or args.reset:
        con.execute("DROP TABLE IF EXISTS data")
        con.execute("""CREATE TABLE data (
                    uuid text PRIMARY KEY,
                    service int NOT NULL,
                    team int NOT NULL,
                    tick int NOT NULL,
                    flag_id blob NOT NULL
                    )""")

    app.run()
