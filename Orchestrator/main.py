import json
import os
import time
from datetime import datetime, timedelta

from checker import Checker
from dotenv import load_dotenv
from scheduler import Scheduler
from utils import get_logger

logger = get_logger("Orchestrator")

if not load_dotenv():
    logger.error("Failed to load .env. Using defaults")
    os.environ["ROUNDS"] = str(10)
    os.environ["ROUND_TIME"] = str(120)
    os.environ["TEAMS"] = str(2)

    os.environ["MIN_WAIT"] = str(1)
    os.environ["MAX_WAIT"] = str(100)


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

    for i, path in enumerate(checker_configs):
        checkers.append(Checker(path, i))

    scheduler = Scheduler(checkers)

    ROUNDS = int(os.getenv("ROUNDS"))
    ROUND_TIME = int(os.getenv("ROUND_TIME"))  # Seconds

    start_time = datetime.now()
    logger.debug(f"Main start time is {start_time}")
    for nround in range(ROUNDS):
        logger.info(f"Round {nround} started at {datetime.now().time()}")

        scheduler.run(nround)

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
