import json
import os
import time
from datetime import datetime, timedelta
from checker import Checker
from dotenv import load_dotenv
from utils import get_logger

# TODO: Change how this works.
# After some research, checks only seem to happen between 1 second and 1 minute and 40 seconds after the tick starts.
# Current idea: Main (thread 1) -> Scheduler (thread 1) -> Checker per team (each one it's own thread. All operations still happen one after the other for now)
# As in, the main just calls the scheduler, the scheduler randomizes execution times, starts a thread for each checker with a sleep until their time, then returns. The main will then calculate the time until the next tick, at which point the cycle repeats
# There shouldn't be an issue with having to wait for processes, but still might be needed.
# Also will have to use locks for concurrent access to the state dict.
# Options 2:
# Main thread 1 -> scheduler thread 2 -> checker thread n
# Instead of spawning multiple threads, the scheduler just generates a 'wait distance' between each check, and sleeps to start it

logger = get_logger("Orchestrator")

if not load_dotenv():
    logger.error("Failed to load .env. Using defaults")
    os.environ["ROUNDS"] = str(10)
    os.environ["ROUND_TIME"] = str(120)
    os.environ["TEAMS"] = str(2)


def main():

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

    ROUNDS = int(os.getenv("ROUNDS"))
    ROUND_TIME = int(os.getenv("ROUND_TIME"))  # Seconds
    TEAMS = int(os.getenv("TEAMS"))

    start_time = datetime.now()
    logger.debug(f"Main start time is {start_time}")
    for nround in range(ROUNDS):
        logger.info(f"Round {nround} started at {datetime.now().time()}")

        # NOTE: Might be useful to multithread at least the checkers. One round with a single team takes almost a minute by itself.
        for checker in checkers:
            for team in range(TEAMS):
                checker.check_sla(team, nround)
                checker.check_put(team, nround)
                checker.check_get(team, nround)

        if nround < ROUNDS - 1:  # Skip the waiting when exiting from the last round.
            sleep_time = start_time + timedelta(seconds=ROUND_TIME * (nround + 1)) - datetime.now()
            logger.info(f"Going to sleep for {sleep_time.total_seconds()} seconds")
            time.sleep(sleep_time.total_seconds())

    report_dir = "reports/" + datetime.now().strftime("%y-%m-%d_%H-%M-%S")
    os.makedirs(report_dir)

    for checker in checkers:
        with open(f"{report_dir}/checker_{checker.name}.json", "w") as f:
            json.dump(checker.status, f, default=lambda x: x.name, indent=2)


if __name__ == "__main__":
    main()
