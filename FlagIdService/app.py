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


con = sqlite3.connect("flagIds.db")

app = Flask(__name__)
app.config["DEBUG"] = True
app_token = os.getenv("APP_TOKEN")


@app.route("/health")
def health():
    return "ok", 200


@app.route("/postFlagId", methods=["POST"])
def postFlagId():
    data = request.get_json()

    token: str = data["token"]
    if token != app_token:
        return "Invalid token", 401

    service_id: str = data["serviceId"]
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
    service_id: str = request.args.get("service", "")
    team_id: int = int(request.args.get("team", -1))
    round_id: int = int(request.args.get("round", -1))

    # TODO: Implement filters
    with lock:
        return json.dumps(state), {"Content-Type": "application/json"}


@app.route("/", methods=["GET"])
def root():
    try:
        with lock:
            services = [str(x) for x in list(state.keys())]
            teams = [str(x) for x in list(state[services[0]].keys())]
            valid_ticks = [str(x) for x in list(state[services[0]][teams[0]].keys())[-5:]]
    except Exception as e:
        return str(e), 500

    return {"services": services, "teams": teams, "ticks": valid_ticks}


if __name__ == "__main__":
    exists = pathlib.Path("flagIds.db").exists()
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", help="Resets the persistence db", action="store_true")
    args = parser.parse_args()

    if not exists or args.reset:
        con.execute("DROP TABLE IF EXISTS data")
        con.execute("""CREATE TABLE data (
                    uuid text PRIMARY KEY,
                    service text NOT NULL,
                    team text NOT NULL,
                    round text NOT NULL,
                    flag_id blob NOT NULL
                    )""")

    app.run()
