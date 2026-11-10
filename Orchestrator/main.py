import argparse
import json
import os
import pprint
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import utils
from checker import Checker
from collector import CheckerCollectorGauge
from dotenv import load_dotenv
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
from scheduler import Scheduler
from utils import get_logger


@dataclass
class Arguments(argparse.Namespace):
    ticks: int
    tick_time: int
    teams: int

    prometheus: bool
    prometheus_port: int
    prometheus_host: str

    colored: bool

    checkers: list[str]


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--ticks", help="Number of ticks to run", default=6, type=int)
    parser.add_argument("--tick-time", help="Tick duration in seconds", default=120, type=int)
    parser.add_argument("--teams", help="Number of teams present", default=1, type=int)

    parser.add_argument("--prometheus", help="Enables prometheus data exporting", action="store_true")
    parser.add_argument("--prometheus-port", help="Port to use for prometheus", default=8500, type=int)
    parser.add_argument("--prometheus-host", help="Host to use for prometheus", default="0.0.0.0", type=str)

    parser.add_argument("--colored", help="Enables colored console output", action="store_true")

    parser.add_argument(
        "checkers",
        help="Path to a checker directory. Defaults to the ccitAD2024 checkers if not provided",
        type=str,
        action="extend",
        nargs="*",
        default=None,
    )

    args: type[Arguments] = parser.parse_args(namespace=Arguments)

    checker_configs: list[str] = (
        args.checkers
        if args.checkers != []
        else [
            "../CyberChallenge.IT-AD-2024/checkers/CCForms-1",
            "../CyberChallenge.IT-AD-2024/checkers/CCForms-2",
            "../CyberChallenge.IT-AD-2024/checkers/ExCCel-1/",
            "../CyberChallenge.IT-AD-2024/checkers/ExCCel-2/",
            "../CyberChallenge.IT-AD-2024/checkers/CCalendar-1/",
            "../CyberChallenge.IT-AD-2024/checkers/CCalendar-2/",
            "../CyberChallenge.IT-AD-2024/checkers/Inlook-1/",
            "../CyberChallenge.IT-AD-2024/checkers/Inlook-2/",
        ]
    )

    if args.colored:
        utils.IS_COLOR_ENABLED = True

    logger = get_logger("Orchestrator")

    logger.debug(f"Enabled checkers: {pprint.pformat(checker_configs)}")

    if not load_dotenv():
        logger.critical("Failed to load .env.")
        sys.exit(-1)

    if args.ticks > 0:
        TICKS: int = args.ticks
    else:
        logger.critical(f"Invalid ticks '{args.ticks}'. Must be a positive integer")
        sys.exit(-1)

    if args.tick_time > 0:
        TICK_TIME: int = args.tick_time
    else:
        logger.critical(f"Invalid tick duration '{args.ticks}'. Must be a positive integer")
        sys.exit(-1)

    if args.teams > 0:
        TEAMS: int = args.teams
    else:
        logger.critical(f"Invalid team amount '{args.ticks}'. Must be a positive integer")
        sys.exit(-1)

    checkers: list[Checker] = []

    for i, path in enumerate(checker_configs):
        checkers.append(Checker(path, i, TEAMS, TICKS))

    scheduler = Scheduler(checkers, TEAMS, TICK_TIME)

    if args.prometheus:
        logger.info(f"Prometheus is enabled on {args.prometheus_host}:{args.prometheus_port}")
        start_http_server(args.prometheus_port, args.prometheus_host)
        data_collector = CheckerCollectorGauge(checkers, TEAMS)
        REGISTRY.register(data_collector)

    start_time = datetime.now()
    logger.debug(f"Main start time is {start_time}")
    for nround in range(TICKS):
        logger.info(f"Round {nround} started at {datetime.now().time()}")

        scheduler.run(nround)

        if nround < TICKS - 1:  # Skip the waiting when exiting from the last round.
            sleep_time = start_time + timedelta(seconds=TICK_TIME * (nround + 1)) - datetime.now()
            logger.info(f"Going to sleep for {sleep_time.total_seconds()} seconds")
            time.sleep(sleep_time.total_seconds())

    report_dir = "reports/" + datetime.now().strftime("%y-%m-%d_%H-%M-%S")
    os.makedirs(report_dir)

    for checker in checkers:
        with open(f"{report_dir}/checker_{checker.name}.json", "w") as f:
            json.dump(checker.status, f, default=lambda x: x.name, indent=2)

    for checker in checkers:
        checker.update_current_tick(checker.current_tick + 1)  # Extra tick for prometheus to fetch the latest tick data

    while input("Exit? [y/N] ").lower() != "y":
        pass


if __name__ == "__main__":
    main()
