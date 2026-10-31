import os
import random
import time
from threading import Thread
from typing import NotRequired, Required, TypedDict

from checker import Checker
from dotenv import load_dotenv
from utils import Action, get_logger


class ThreadDict(TypedDict):
    thread: Required[Thread]
    rng_wait: Required[float]
    wait: NotRequired[float]


class Scheduler:
    def __init__(self, checkers: list[Checker]) -> None:
        self.checkers: list[Checker] = checkers
        self.min_time: int = int(os.getenv("MIN_WAIT"))
        self.max_time: int = int(os.getenv("MAX_WAIT"))
        self.logger = get_logger("Scheduler")

    def run(self, tick: int) -> None:

        thread_info: list[ThreadDict] = []

        teams = int(os.getenv("TEAMS"))
        # For each checker, team and action:
        # Calculate the random time for SLA and PUT
        # Then get the list of valid flags, and calculate the times for them
        # Once done, normalize the times to the difference between one another

        for checker in self.checkers:
            checker.update_current_tick(tick)
            for team in range(teams):
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
                            rng_wait=random.uniform(self.min_time, self.max_time),
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
                            rng_wait=random.uniform(self.min_time, self.max_time),
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
                                rng_wait=random.uniform(self.min_time, self.max_time),
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
            self.logger.info(f"Sleeping for {thread['wait']} and then starting {thread['thread'].name}")  # pyright: ignore[reportTypedDictNotRequiredAccess]
            time.sleep(thread["wait"])  # pyright: ignore[reportTypedDictNotRequiredAccess] Always gets set before this
            thread["thread"].start()

        # Every thread should be done, but should probably still check
        for thread in threads_sorted:
            thread["thread"].join()


if __name__ == "__main__":
    load_dotenv()

    checker_configs: list[str] = [
        "../CyberChallenge.IT-AD-2024/checkers/CCForms-1",
    ]

    checkers: list[Checker] = []

    for i, path in enumerate(checker_configs):
        checkers.append(Checker(path, i))

    scheduler = Scheduler(checkers)

    scheduler.run(0)
