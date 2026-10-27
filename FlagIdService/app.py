import json
from pprint import pprint
from typing import Any
from flask import Flask, request
import logging

logger = logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config["DEBUG"] = True
app_token = "5774A8F69DDEC6C954D2CBBDE2B5A7EF"
state = {}

@app.route("/postFlagId", methods = ["POST"])
def postFlagId():
    global state

    print(f"{request.data}")


    data = request.get_json()

    print(f"{data=}")

    token: str = data["token"]
    if token != app_token:
        return "Invalid token", 401

    service_id: str = data["serviceId"]
    team_id: int = data["teamId"]
    round_id: int = data["round"]
    flag_id: Any = data["flagId"]

    state.setdefault(service_id, {})
    state[service_id].setdefault(team_id, {})
    state[service_id][team_id].setdefault(round_id, flag_id)

    pprint(state)
    return "ok", 200

@app.route("/flagIds", methods = ["GET"])
def flagIds():
    global state
    service_id: str = request.args.get("service", '')
    team_id: int = int(request.args.get("team", 0))
    round_id: int = int(request.args.get("round", 0))

    # TODO: Implement filters

    return json.dumps(state), {"Content-Type": "application/json"}
