import json
import pathlib
import subprocess
from typing import override

from utils import Action, Status, generate_flag


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

        self.status: dict[int, dict[int, dict[str, Status | str | None]]] = {}

    def check_sla(self, team: int, nround: int) -> None:
        """
        Checks the SLA status of the service

        Args:
            team (int): zero indexed team number
            nround(int): zero indexed current tick number
        """
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
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                print(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                return
            print(
                f"Checker {self.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["SLA"] = Status(e.returncode)
        except Exception as e:
            print(f"Generic exception happened: {e}")

    def check_get(self, team: int, nround: int) -> None:
        """
        Checks the ability to retrieve flags from the system

        Args:
            team (int): zero indexed team number
            nround(int): zero indexed current tick number
        """
        # TODO: Don't check if there are no valid flags in the last five ticks

        current_flag: str = self.status[nround][team]["flag"]

        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.GET_timeout,
                env={
                    "ACTION": Action.GET_FLAG.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(nround),
                    "FLAG": current_flag,
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
        """
        Checks the ability to insert flags into the system

        Args:
            team (int): zero indexed team number
            nround(int): zero indexed current tick number
        """
        # TODO: Don't execute on last round.

        new_flag = generate_flag(team, nround)
        self.status[nround][team]["flag"] = new_flag

        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.PUT_timeout,
                env={
                    "ACTION": Action.PUT_FLAG.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(nround),
                    "FLAG": new_flag,
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
