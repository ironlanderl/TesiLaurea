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


def run_tests(rule: str, action: str, port: str) -> tuple[timedelta, timedelta] | tuple[None, None]:

    data: list[CaronteData] = []

    i = 0

    while True:
        r = requests.get(
            f"http://127.0.0.1:3333/api/connections?matched_rules={rule}&service_port={port}"
            if len(data) == 0
            else f"http://127.0.0.1:3333/api/connections?matched_rules={rule}&service_port={port}&from={data[-1]['id']}"
        )
        if len(data) == 0 and len(r.json()) == 0:
            print("Empty response at the first loop.")
            return None, None

        print(f"Getting data. Loop {i}, size is {len(data)}")
        if len(data) != 0 and (r.json()[-1]["id"] == data[-1]["id"]):
            break
        data.extend(r.json())
        i += 1

    found = 0
    min_diff = timedelta(seconds=9999999)
    max_diff = timedelta(seconds=-1)

    start_date = datetime(2026, 6, 20, 9, 00, 00)

    for tick in range(20 if action == "OUT" else 240):
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
                min_diff = min(min_diff, time_happened - tick_start)
                max_diff = max(max_diff, time_happened - tick_start)
                found += 1

        if found == 0:
            print(f"No actions at tick {tick}")
        if found > 1:
            print(f"Multiple actions at tick {tick}. There were {found}")

        found = 0

    return (min_diff, max_diff)


def latex_handler():

    r = requests.get("http://127.0.0.1:3333/api/rules")

    IN_RULE_ID = r.json()[1]["id"]
    OUT_RULE_ID = r.json()[0]["id"]

    data: dict[str, dict[str, None | timedelta]] = {}

    ports = get_ports()

    for port in ports:
        min_diff, max_diff = run_tests(IN_RULE_ID, "IN", port)
        data[port] = {"in_min": min_diff, "in_max": max_diff}

        min_diff, max_diff = run_tests(OUT_RULE_ID, "OUT", port)
        data[port] = data[port] | {"out_min": min_diff, "out_max": max_diff}

    __import__("pprint").pprint(data)

    output_str: str = "Operazione "

    for port in data:
        if data[port]["in_min"] is not None and data[port]["out_min"] is not None:
            output_str += f"& Port {port} "

    output_str += "\\\\ \n \\midrule \\\\ \n PUT\\_FLAG minimo"

    for port in data:
        if data[port]["in_min"] is not None and data[port]["out_min"] is not None:
            output_str += f"& {data[port]['in_min'].total_seconds()}s "

    output_str += "\\\\\n PUT\\_FLAG massimo"

    for port in data:
        if data[port]["in_min"] is not None and data[port]["out_min"] is not None:
            output_str += f"& {data[port]['in_max'].total_seconds()}s "

    output_str += "\\\\\n GET\\_FLAG minimo"

    for port in data:
        if data[port]["in_min"] is not None and data[port]["out_min"] is not None:
            output_str += f"& {data[port]['out_min'].total_seconds()}s "

    output_str += "\\\\\n GET\\_FLAG massimo"

    for port in data:
        if data[port]["in_min"] is not None and data[port]["out_min"] is not None:
            output_str += f"& {data[port]['out_max'].total_seconds()}s "

    output_str += "\\\\"

    print(output_str)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("action", help="Action", choices=["IN", "OUT", "LATEX"])

    args = parser.parse_args()

    if args.action == "LATEX":
        latex_handler()

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
