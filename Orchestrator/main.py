import json
import os
import time
from datetime import datetime

from checker import Checker
from utils import get_logger


def main():

    logger = get_logger("Orchestrator")

    checker_configs: list[str] = [
        "../CyberChallenge.IT-AD-2024/checkers/CCForms-1",
        "../CyberChallenge.IT-AD-2024/checkers/CCForms-2",
        "../CyberChallenge.IT-AD-2024/checkers/ExCCel-1/",
        "../CyberChallenge.IT-AD-2024/checkers/ExCCel-2/",
        "../CyberChallenge.IT-AD-2024/checkers/CCalendar-1/",
        "../CyberChallenge.IT-AD-2024/checkers/CCalendar-2/",
        "../CyberChallenge.IT-AD-2024/checkers/Inlook-1/",
        "../CyberChallenge.IT-AD-2024/checkers/Inlook-2/",
    ]

    checkers: list[Checker] = []

    for path in checker_configs:
        checkers.append(Checker(path))

    ROUNDS = 10
    ROUND_TIME = 150 # Seconds
    TEAMS = 3

    # NOTE: Figure out a better way to handle the timing? Currently goes around 0.000270 seconds faster than real time.
    for nround in range(ROUNDS):
        logger.info(f"Round {nround} started at {datetime.now().time()}")
        start_time = time.time_ns()

        # NOTE: Might be useful to multithread at least the checkers. One round with a single team takes almost a minute by itself.
        for checker in checkers:
            for team in range(TEAMS):
                checker.check_sla(team, nround)
                checker.check_put(team, nround)
                checker.check_get(team, nround)

        end_time = time.time_ns()

        elapsed_time = round((end_time - start_time) / 1_000_000_000, 5)  # Round nanoseconds to seconds

        if nround < ROUNDS - 1:  # Skip the waiting when exiting from the last round.
            logger.info(f"Going to sleep for {ROUND_TIME - elapsed_time} seconds")
            time.sleep(ROUND_TIME - elapsed_time)

    report_dir = "reports/" + datetime.now().strftime("%y-%m-%d_%H-%M-%S")
    os.makedirs(report_dir)

    for checker in checkers:
        with open(f"{report_dir}/checker_{checker.name}.json", "w") as f:
            json.dump(checker.status, f, default=lambda x: x.name, indent=2)


if __name__ == "__main__":
    main()
