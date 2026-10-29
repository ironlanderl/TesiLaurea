import json
import os
import pathlib
import subprocess
from typing import override

from utils import Action, Status, generate_flag, get_logger


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

        self.logger = get_logger(self.name)

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
            self.logger.info(f"Timeout expired for {self.name}")
            self.status[nround][team]["SLA"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                return
            self.logger.info(
                f"Operation {Action.CHECK_SLA.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["SLA"] = Status(e.returncode)
        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")

    def check_get(self, team: int, nround: int) -> None:
        """
        Checks the ability to retrieve flags from the system

        Args:
            team (int): zero indexed team number
            nround(int): zero indexed current tick number
        """
        # TODO: Don't check if there are no valid flags in the last five ticks
        # Also, check if all of the five previous flags are valid

        if nround == 0:
            self.logger.info("First tick. Skipping GET_CHECK")
            self.status[nround][team]["GET"] = Status.CHECKER_DISABLED
            return

        flags_to_check = self.__get_valid_flags(team, nround)

        if len(flags_to_check) == 0:
            self.logger.info(f"No valid flags for tick {nround}")
            self.status[nround][team]["GET"] = Status.DOWN
            return

        self.logger.info(f"Going to check {len(flags_to_check)} flags")

        try:  # Main try except. Only test timeouts and generic exceptions
            for current_flag in flags_to_check:
                try:  # Second try except. Check for the return value
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
                except subprocess.CalledProcessError as e:
                    # Filter out eventual non compliant return values (such as -1)
                    if e.returncode not in Status:
                        self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                        return
                    self.logger.info(
                        f"Operation {Action.GET_FLAG.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
                    )
                    self.status[nround][team]["GET"] = Status(e.returncode)

        except subprocess.TimeoutExpired:
            self.logger.info("Timeout expired")
            self.status[nround][team]["GET"] = Status.DOWN

        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")

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
            self.logger.info(f"Timeout expired for {self.name}")
            self.status[nround][team]["GET"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                return
            self.logger.info(
                f"Operation {Action.GET_FLAG.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["GET"] = Status(e.returncode)
        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")

    def check_put(self, team: int, nround: int) -> None:
        """
        Checks the ability to insert flags into the system
        Gets skipped if ran on the last tick

        Args:
            team (int): zero indexed team number
            nround(int): zero indexed current tick number
        """
        if nround == int(os.getenv("ROUNDS")) - 1:
            self.logger.info("Reached last round. Skipping FLAG_IN")
            self.status[nround][team]["PUT"] = Status.CHECKER_DISABLED
            return

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
                    "FLAGID_SERVICE": "http://127.0.0.1:5000",  # TODO: Don't hardcode these
                    "FLAGID_TOKEN": "5774A8F69DDEC6C954D2CBBDE2B5A7EF",
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            self.logger.info(f"Timeout expired for {self.name}")
            self.status[nround][team]["PUT"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                return
            self.logger.info(
                f"Operation {Action.PUT_FLAG.name} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[nround][team]["PUT"] = Status(e.returncode)
        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")

    def __get_valid_flags(self, team: int, nround: int) -> list[str]:
        """
        Gets the last 5 flags
        Returns nothing if on first tick
        """

        flags: list[str] = []

        if nround == 0:
            return flags

        for tick in range(nround - 1, max(nround - 1 - 5, -1), -1):
            self.logger.debug(f"Checking flag for tick {tick}. Status is {self.status[tick][team]['PUT']}")
            if self.status[tick][team]["PUT"] == Status.OK:
                flags.append(self.status[tick][team]["flag"])

        return flags

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
