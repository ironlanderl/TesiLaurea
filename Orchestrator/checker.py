import json
import os
import pathlib
import pprint
import subprocess
from logging import Logger
from threading import Lock
from typing import NotRequired, Required, TypedDict, override

from utils import Action, Status, generate_flag, get_logger


class TickInfo(TypedDict):
    SLA: Required[Status]
    GET: Required[Status]
    PUT: Required[Status]
    flag: NotRequired[str]


class Checker:
    """
    Initialize a new checker

    Args:
        path (str): Path to the base dir of the checker
    """

    def __init__(self, path: str, service_number: int) -> None:

        json_file = f"{path}/checker.json"

        with open(json_file, "r") as f:
            data = json.load(f)

        self.name: str = pathlib.Path(path).as_posix().split("/")[-1]
        self.path: str = path

        self.command: str = data["command"]
        self.SLA_timeout: int = data["timeout"]["CHECK_SLA"] / 1000
        self.PUT_timeout: int = data["timeout"]["PUT_FLAG"] / 1000
        self.GET_timeout: int = data["timeout"]["GET_FLAG"] / 1000

        self.service_number: int = service_number

        self.status: dict[int, dict[int, TickInfo]] = {}

        self.logger: Logger = get_logger(self.name)

        self.init_lock: Lock = Lock()
        self.get_lock: Lock = Lock()

        self.current_tick: int = 0

    def check_sla(self, team: int, tick: int) -> None:
        """
        Checks the SLA status of the service

        Args:
            team (int): zero indexed team number
            tick(int): zero indexed current tick number
        """
        self.__create_dict_data(team, tick)
        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.SLA_timeout,
                env={
                    "ACTION": Action.CHECK_SLA.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(tick),
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            self.logger.info(f"Timeout expired for {self.name}")
            self.status[tick][team]["SLA"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                self.status[tick][team]["SLA"] = Status.ERROR
                return
            self.logger.info(
                f"Operation {Action.CHECK_SLA.name} for team {team} at tick {tick} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[tick][team]["SLA"] = Status(e.returncode)
        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")
            self.status[tick][team]["SLA"] = Status.ERROR

    def check_get_single(self, team: int, tick: int, flag: str) -> None:
        """
        Checks the ability to retrieve a specific flag from the system

        Args:
            team (int): zero indexed team number
            tick(int): zero indexed current tick number
            flag(str): the flag to check
        """
        self.__create_dict_data(team, tick)

        # NOTE: The entire get operation is under lock
        with self.get_lock:
            # If down or Disabled, skip to save time
            if self.status[tick][team]["GET"] in (Status.DOWN, Status.CHECKER_DISABLED, Status.ERROR):
                return

            if tick == 0:
                self.logger.info("First tick. Skipping GET_CHECK")
                self.status[tick][team]["GET"] = Status.CHECKER_DISABLED
                return

            try:
                _ = subprocess.check_output(
                    self.command.split(" "),
                    cwd=self.path,
                    timeout=self.GET_timeout,
                    env={
                        "ACTION": Action.GET_FLAG.name,
                        "TEAM_ID": str(team),
                        "ROUND": str(tick),
                        "FLAG": flag,
                    },
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                # Filter out eventual non compliant return values (such as -1)
                if e.returncode not in Status:
                    self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                    self.status[tick][team]["GET"] = Status.ERROR
                    return
                self.logger.info(
                    f"Operation {Action.GET_FLAG.name} for team {team} at tick {tick} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
                )
                self.status[tick][team]["GET"] = Status(e.returncode)

            except subprocess.TimeoutExpired:
                self.logger.info("Timeout expired")
                self.status[tick][team]["GET"] = Status.DOWN

            except Exception as e:
                self.logger.error(f"Generic exception happened: {e}")
                self.status[tick][team]["GET"] = Status.ERROR

    def check_get(self, team: int, tick: int) -> None:
        """
        Checks the ability to retrieve the last five valid flags from the system

        Args:
            team (int): zero indexed team number
            tick(int): zero indexed current tick number
        """
        self.__create_dict_data(team, tick)

        if tick == 0:
            self.logger.info("First tick. Skipping GET_CHECK")
            self.status[tick][team]["GET"] = Status.CHECKER_DISABLED
            return

        flags_to_check = self.get_valid_flags(team, tick)

        if len(flags_to_check) == 0:
            self.logger.info(f"No valid flags for tick {tick}")
            self.status[tick][team]["GET"] = Status.DOWN
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
                            "ROUND": str(tick),
                            "FLAG": current_flag,
                        },
                        stderr=subprocess.STDOUT,
                    )
                except subprocess.CalledProcessError as e:
                    # Filter out eventual non compliant return values (such as -1)
                    if e.returncode not in Status:
                        self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                        self.status[tick][team]["GET"] = Status.ERROR
                        return
                    self.logger.info(
                        f"Operation {Action.GET_FLAG.name} for team {team} at tick {tick} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
                    )
                    self.status[tick][team]["GET"] = Status(e.returncode)

        except subprocess.TimeoutExpired:
            self.logger.info("Timeout expired")
            self.status[tick][team]["GET"] = Status.DOWN

        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")
            self.status[tick][team]["GET"] = Status.ERROR

    def check_put(self, team: int, tick: int) -> None:
        """
        Checks the ability to insert flags into the system
        Gets skipped if ran on the last tick

        Args:
            team (int): zero indexed team number
            tick(int): zero indexed current tick number
        """
        self.__create_dict_data(team, tick)

        if tick == int(os.getenv("ROUNDS")) - 1:  # pyright: ignore[reportArgumentType]. Gets forced by main
            self.logger.info("Reached last round. Skipping FLAG_IN")
            self.status[tick][team]["PUT"] = Status.CHECKER_DISABLED
            return

        new_flag = generate_flag(team, tick, self.service_number)
        self.status[tick][team]["flag"] = new_flag

        try:
            _ = subprocess.check_output(
                self.command.split(" "),
                cwd=self.path,
                timeout=self.PUT_timeout,
                env={
                    "ACTION": Action.PUT_FLAG.name,
                    "TEAM_ID": str(team),
                    "ROUND": str(tick),
                    "FLAG": new_flag,
                    "FLAGID_SERVICE": str(os.getenv("FLAGID_SERVICE")),
                    "FLAGID_TOKEN": str(os.getenv("FLAGID_TOKEN")),
                },
                stderr=subprocess.STDOUT,
            )
        except subprocess.TimeoutExpired:
            self.logger.info(f"Timeout expired for {self.name}")
            self.status[tick][team]["PUT"] = Status.DOWN
        except subprocess.CalledProcessError as e:
            # Filter out eventual non compliant return values (such as -1)
            if e.returncode not in Status:
                self.logger.error(f"Invalid return code '{e.returncode}'. Text is {e.output}")
                self.status[tick][team]["PUT"] = Status.ERROR
                return
            self.logger.info(
                f"Operation {Action.PUT_FLAG.name} for team {team} at tick {tick} returned error {e.returncode} with text {e.output}. Corresponds to {Status(e.returncode).name}"
            )
            self.status[tick][team]["PUT"] = Status(e.returncode)
        except Exception as e:
            self.logger.error(f"Generic exception happened: {e}")
            self.status[tick][team]["PUT"] = Status.ERROR

    def get_valid_flags(self, team: int, ntick: int) -> list[str]:
        """
        Gets the last 5 valid flags
        Returns nothing if on first tick
        """

        flags: list[str] = []

        if ntick == 0:
            return flags

        for tick in range(ntick - 1, max(ntick - 1 - 5, -1), -1):
            self.logger.debug(f"Checking flag for tick {tick} team {team}. Status is {self.status[tick][team]['PUT']}")
            if self.status[tick][team]["PUT"] == Status.OK:
                flags.append(self.status[tick][team]["flag"])  # pyright: ignore[reportTypedDictNotRequiredAccess]. Check down by is ok

        return flags

    def get_last_tick_team_info(self, team: int) -> TickInfo:
        """
        Returns a TickInfo of the last game tick.
        Returns NOT_YET_CHECKED on all of the actions if errors occur
        """
        if self.current_tick == 0:
            self.logger.debug("Tried accessing info on tick 0. Returning default values")
            return TickInfo(SLA=Status.NOT_YET_CHECKED, GET=Status.NOT_YET_CHECKED, PUT=Status.NOT_YET_CHECKED)

        last_tick = self.current_tick - 1

        if last_tick not in self.status:
            self.logger.critical("Tried accessing non existing tick somehow. Returning default values")
            return TickInfo(SLA=Status.NOT_YET_CHECKED, GET=Status.NOT_YET_CHECKED, PUT=Status.NOT_YET_CHECKED)

        return self.status[last_tick][team]

    def update_current_tick(self, tick: int) -> None:
        self.current_tick = tick

    def __create_dict_data(self, team: int, tick: int) -> None:
        """
        Creates the basic structure for the status dict
        """
        with self.init_lock:
            _ = self.status.setdefault(tick, {}).setdefault(
                team, TickInfo(SLA=Status.NOT_YET_CHECKED, GET=Status.NOT_YET_CHECKED, PUT=Status.NOT_YET_CHECKED)
            )

    @override
    def __str__(self) -> str:
        return f"{self.name}: {self.command}, {self.SLA_timeout}, {self.PUT_timeout}, {self.GET_timeout}"

    @override
    def __repr__(self) -> str:
        return f"{self.name}: {self.command}, {self.SLA_timeout}, {self.PUT_timeout}, {self.GET_timeout}"
