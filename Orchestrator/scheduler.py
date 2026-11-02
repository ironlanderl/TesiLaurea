import random
import time
from logging import Logger
from threading import Thread
from typing import Required, TypedDict

from checker import Checker
from utils import Action, get_logger


class ThreadDict(TypedDict):
    thread: Required[Thread]
    rng_wait: Required[float]
    wait: Required[float]


class Scheduler:
    def __init__(self, checkers: list[Checker], teams: int, tick_time: int) -> None:
        """
        Creates a new scheduler

        Args:
            checkers (list[Checker]): List of checkers that will run
            teams (int): Number of teams present
            tick_time (time): Length of a single tick
        """
        self.checkers: list[Checker] = checkers
        self.min_time: float = 0.1
        self.tick_time: int = (
            tick_time - 1
        )  # NOTE: Removes a second to make sure there's no issues with thread scheduling
        self.logger: Logger = get_logger("Scheduler")
        self.teams: int = teams

    def run(self, tick: int) -> None:
        """
        Main execution function.
        For each checker, team and action:
            1. Calculates the random time for SLA, PUT, and for each valid flag for GET
            2. Sorts the list by wait time
            3. Transforms from "wait from 0" to "wait from previous"
            4. Waits the time and launches the relevant thread

        Args:
            tick (int): Zero indexed tick to execute

        """

        thread_info: list[ThreadDict] = []

        for checker in self.checkers:
            checker.update_current_tick(tick)
            for team in range(self.teams):
                for action in Action:
                    if action == Action.CHECK_SLA:
                        checker_thread: ThreadDict = ThreadDict(
                            thread=Thread(
                                target=checker.check_sla,
                                args=(
                                    team,
                                    tick,
                                ),
                                name=f"{checker.name}_{team}_{action.name}",
                            ),
                            rng_wait=random.uniform(self.min_time, self.tick_time - checker.get_biggest_timeout()),
                            wait=-1,
                        )
                        thread_info.append(checker_thread)
                    elif action == Action.PUT_FLAG:
                        checker_thread: ThreadDict = ThreadDict(
                            thread=Thread(
                                target=checker.check_put,
                                args=(
                                    team,
                                    tick,
                                ),
                                name=f"{checker.name}_{team}_{action.name}",
                            ),
                            rng_wait=random.uniform(self.min_time, self.tick_time - checker.get_biggest_timeout()),
                            wait=-1,
                        )
                        thread_info.append(checker_thread)
                    elif action == Action.GET_FLAG:
                        flag_list = checker.get_valid_flags(team, tick)
                        if len(flag_list) == 0:  # Current hacky solution
                            flag_list.append("INVALID")
                        for i, flag in enumerate(flag_list):
                            checker_thread: ThreadDict = ThreadDict(
                                thread=Thread(
                                    target=checker.check_get_single,
                                    args=(team, tick, flag),
                                    name=f"{checker.name}_{team}_{action.name}",
                                ),
                                rng_wait=random.uniform(self.min_time, self.tick_time - checker.get_biggest_timeout()),
                                wait=-1,
                            )
                            thread_info.append(checker_thread)

        # Now we sort
        threads_sorted = sorted(thread_info, key=lambda x: x["rng_wait"])

        # Calculate the differences
        for i, v in enumerate(threads_sorted):
            # Skip first item
            if i == 0:
                v["wait"] = v["rng_wait"]
                continue

            v["wait"] = v["rng_wait"] - threads_sorted[i - 1]["rng_wait"]

        # We can now start the main calling loop
        for thread in threads_sorted:
            self.logger.info(f"Sleeping for {thread['wait']} and then starting {thread['thread'].name}")
            time.sleep(thread["wait"])
            thread["thread"].start()

        # Every thread should be done, but should probably still check
        for thread in threads_sorted:
            thread["thread"].join()
