import json
import logging
import os
from threading import Lock
from typing import Any

from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

logger = logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config["DEBUG"] = True
app_token = os.getenv("APP_TOKEN")
state = {}
lock = Lock()


@app.route("/postFlagId", methods=["POST"])
def postFlagId():

    print(f"{request.data}")

    data = request.get_json()

    token: str = data["token"]
    if token != app_token:
        return "Invalid token", 401

    service_id: str = data["serviceId"]
    team_id: int = data["teamId"]
    round_id: int = data["round"]
    flag_id: Any = data["flagId"]

    with lock:
        state.setdefault(service_id, {})
        state[service_id].setdefault(team_id, {})
        state[service_id][team_id].setdefault(round_id, flag_id)

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
            services = list(state.keys())
            teams = list(state[services[0]].keys())
            valid_ticks = list(state[services[0]][teams[0]].keys())[-5:]
    except Exception as e:
        return str(e), 500

    return {"services": services, "teams": teams, "ticks": valid_ticks}
