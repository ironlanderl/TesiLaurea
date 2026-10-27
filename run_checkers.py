import json
import pathlib
import random
import string
import subprocess
import time
from datetime import datetime
from enum import Enum
from pprint import pprint
from typing import override


class Status(Enum):
    OK = 101
    DOWN = 104
    CHECKER_DISABLED = 109
    ERROR = 110


class Action(Enum):
    CHECK_SLA = "CHECK_SLA"
    PUT_FLAG = "PUT_FLAG"
    GET_FLAG = "GET_FLAG"


def generate_flag() -> str:
    alphabet: str = string.ascii_uppercase + string.digits

    return "".join(random.choices(alphabet, k=31)) + "="


class Checker:
    """
    Initialize a new checker

    Args:
        path (str): Path to the base dir of the checker
    """

    def __init__(self, path: str) -> None:

        json_file = f"{path}/checker.json"

        with open(json_file, "r") as f:
            data = json.load(f)

        self.name: str = pathlib.Path(path).as_posix().split("/")[-1]
        self.path: str = path

        self.command: str = data["command"]
        self.SLA_timeout: int = data["timeout"]["CHECK_SLA"] / 1000
        self.PUT_timeout: int = data["timeout"]["PUT_FLAG"] / 1000
        self.GET_timeout: int = data["timeout"]["GET_FLAG"] / 1000

        self.status = {}

    def check_sla(self, team: int, nround: int) -> None:
        # Since sla is always checked first (for now at least), always have it initialize the round status dict
        self.__create_dict_data(team, nround)
        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.SLA_timeout,
                env={
                    "ACTION": Action.CHECK_SLA.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(nround),
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for {self.name}")
            self.status[nround][team]["SLA"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # TODO: Filter for only the enum return values
            print(
                f"Checker {self.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["SLA"] = Status(e.returncode)
        except Exception as e:
            print(f"Generic exception happened: {e}")

    def check_get(self, team: int, nround: int) -> None:
        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.GET_timeout,
                env={
                    "ACTION": Action.GET_FLAG.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(nround),
                    "FLAG": "B" * 31 + "=",
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for {self.name}")
            self.status[nround][team]["GET"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            print(
                f"Checker {self.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["GET"] = Status(e.returncode)
        except Exception as e:
            print(f"Generic exception happened: {e}")

    def check_put(self, team: int, nround: int) -> None:
        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.PUT_timeout,
                env={
                    "ACTION": Action.PUT_FLAG.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(nround),
                    "FLAG": "B" * 31 + "=",
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for {self.name}")
            self.status[nround][team]["PUT"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            print(
                f"Checker {self.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["PUT"] = Status(e.returncode)
        except Exception as e:
            print(f"Generic exception happened: {e}")

    def __create_dict_data(self, team: int, nround: int) -> None:
        # NOTE: Probably not thread safe.

        # Check if the current round is present. If not, add it as null.
        if nround not in self.status:
            self.status[nround] = {}

        # Now check if the team exists. If it doesn't, add it with some sane defaults.
        if team not in self.status[nround]:
            self.status[nround][team] = {"SLA": None, "GET": None, "PUT": None}

    @override
    def __str__(self) -> str:
        return f"{self.name}: {self.command}, {self.SLA_timeout}, {self.PUT_timeout}, {self.GET_timeout}"

    @override
    def __repr__(self) -> str:
        return f"{self.name}: {self.command}, {self.SLA_timeout}, {self.PUT_timeout}, {self.GET_timeout}"


checker_configs: list[str] = [
    "./CyberChallenge.IT-AD-2024/checkers/CCForms-1",
    "./CyberChallenge.IT-AD-2024/checkers/CCForms-2",
]

checkers: list[Checker] = []

for path in checker_configs:
    checkers.append(Checker(path))

ROUNDS = 3
ROUND_TIME = 30  # Seconds
TEAMS = 3

for nround in range(3):
    print(f"Round {nround} started at {datetime.now().time()}")
    start_time = time.time_ns()

    for checker in checkers:
        for team in range(TEAMS):
            checker.check_sla(team, nround)
            checker.check_put(team, nround)
            checker.check_get(team, nround)

    end_time = time.time_ns()

    elapsed_time = round((end_time - start_time) / 1_000_000_000, 5)  # Round nanoseconds to seconds

    print(f"Going to sleep for {ROUND_TIME - elapsed_time} seconds")

    time.sleep(ROUND_TIME - elapsed_time)


print("=" * 30)
pprint(checkers[0].status)
print("-" * 30)
pprint(checkers[1].status)

print("=" * 30)
print(json.dumps(checkers[0].status, default=lambda x: x.name, indent=2))
print("-" * 30)
print(json.dumps(checkers[1].status, default=lambda x: x.name, indent=2))
