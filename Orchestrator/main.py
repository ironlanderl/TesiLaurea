import json
import time
from datetime import datetime
from pprint import pprint

from checker import Checker


def main():
    checker_configs: list[str] = [
        "../CyberChallenge.IT-AD-2024/checkers/CCForms-1",
        "../CyberChallenge.IT-AD-2024/checkers/CCForms-2",
    ]

    checkers: list[Checker] = []

    for path in checker_configs:
        checkers.append(Checker(path))

    ROUNDS = 3
    ROUND_TIME = 30  # Seconds
    TEAMS = 3

    for nround in range(ROUNDS):
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


if __name__ == "__main__":
    main()
