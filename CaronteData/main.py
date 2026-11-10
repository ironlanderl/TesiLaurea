import argparse
import sys
from datetime import datetime, timedelta
from typing import TypedDict

import requests


class CaronteData(TypedDict):
    id: int
    started_at: str


def get_ports() -> list[str]:
    r = requests.get("http://127.0.0.1:3333/api/statistics/totals")
    ports = [x for x in r.json()["connections_per_service"]]

    return ports


def run_tests(rule: str, action: str, port: str) -> tuple[timedelta, timedelta]:

    data: list[CaronteData] = []

    i = 0

    while True:
        r = requests.get(
            f"http://127.0.0.1:3333/api/connections?matched_rules={rule}&service_port={port}"
            if len(data) == 0
            else f"http://127.0.0.1:3333/api/connections?matched_rules={rule}&service_port={port}&from={data[-1]['id']}"
        )
        if len(data) == 0 and len(r.json()) == 0:
            print("Empty response at the first loop. Exiting")
            sys.exit(1)

        print(f"Getting data. Loop {i}, size is {len(data)}")
        if len(data) != 0 and (r.json()[-1]["id"] == data[-1]["id"]):
            break
        data.extend(r.json())
        i += 1

    found = 0
    min_diff = timedelta(seconds=9999999)
    max_diff = timedelta(seconds=0)

    start_date = datetime(2026, 6, 19, 9, 00, 00)

    for tick in range(50 if action == "OUT" else 240):
        tick_start = start_date + timedelta(minutes=2 * tick)
        tick_end = tick_start + timedelta(minutes=2)

        for flag_in in data:
            time_happened = datetime.strptime(
                flag_in["started_at"],
                "%Y-%m-%dT%H:%M:%S.%fZ"
                if "." in flag_in["started_at"]
                else "%Y-%m-%dT%H:%M:%SZ",  # Handles the milliseconds not always being present
            )
            if tick_start <= time_happened <= tick_end:
                print(f"Action happened at tick {tick} and at {time_happened}")
                if tick < 6:
                    min_diff = min(min_diff, time_happened - tick_start)
                    max_diff = max(max_diff, time_happened - tick_start)
                found += 1

        if found == 0:
            print(f"No actions at tick {tick}")
        if found > 1:
            print(f"Multiple actions at tick {tick}. There were {found}")

        found = 0

    return (min_diff, max_diff)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("action", help="Action", choices=["IN", "OUT"])

    args = parser.parse_args()

    ports = get_ports()

    print(f"Available ports: {ports}")
    port = input("Port > ")

    r = requests.get("http://127.0.0.1:3333/api/rules")

    IN_RULE_ID = r.json()[1]["id"]
    OUT_RULE_ID = r.json()[0]["id"]

    min_diff, max_diff = run_tests(IN_RULE_ID if args.action == "IN" else OUT_RULE_ID, args.action, port)

    print(
        f"Min time after tick start: {min_diff.total_seconds()} seconds.\nMax time after tick start: {max_diff.total_seconds()} seconds ({max_diff.total_seconds() // 60} minutes {max_diff.total_seconds() % 60} seconds)."
    )


if __name__ == "__main__":
    main()
