from datetime import datetime, timedelta

import requests

IN_RULE_ID = "6ae2580e0000000000000001"
OUT_RULE_ID = "6ae2580c0000000000000000"
PORT = 2222

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={IN_RULE_ID}&service_port={PORT}")

data: list[str] = r.json()

while True:
    r = requests.get(
        f"http://127.0.0.1:3333/api/connections?matched_rules={IN_RULE_ID}&service_port={PORT}&from={data[-1]['id']}"
    )
    if r.json()[-1]["id"] == data[-1]["id"]:
        break
    data.extend(r.json())

# Loop for each tick with time.
# Check for each data point if it is inside of the time frame for the tick
# Calculate the difference between tick start and FLAG_IN
# Save both the min and max differences.

min_diff = timedelta(seconds=9999999)
max_diff = timedelta(seconds=0)
found = 0

start_date = datetime(2025, 6, 20, 9, 00, 00)
for tick in range(240):
    tick_start = start_date + timedelta(minutes=2 * tick)
    tick_end = tick_start + timedelta(minutes=2)

    for flag_in in data:
        time_happened = datetime.strptime(flag_in["started_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        if tick_start <= time_happened <= tick_end:
            print(f"FLAG_IN tick {tick} happened at {time_happened}")
            min_diff = min(min_diff, time_happened - tick_start)
            max_diff = max(max_diff, time_happened - tick_start)

            found += 1

    if found == 0:
        print(f"No FLAG_IN at tick {tick}")
    if found > 1:
        print(f"Multiple FLAG_IN at tick {tick}")

    found = 0


print(
    f"Min time after tick start: {min_diff.total_seconds()} seconds.\nMax time after tick start: {max_diff.total_seconds()} seconds ({max_diff.total_seconds() // 60} minutes {max_diff.total_seconds() % 60} seconds)."
)

# ====================================================== #

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={OUT_RULE_ID}&service_port={PORT}")

data: list[str] = r.json()

while True:
    r = requests.get(
        f"http://127.0.0.1:3333/api/connections?matched_rules={OUT_RULE_ID}&service_port={PORT}&from={data[-1]['id']}"
    )
    if r.json()[-1]["id"] == data[-1]["id"]:
        break
    data.extend(r.json())

found = 0

start_date = datetime(2025, 6, 20, 9, 00, 00)
for tick in range(50):
    tick_start = start_date + timedelta(minutes=2 * tick)
    tick_end = tick_start + timedelta(minutes=2)

    for flag_in in data:
        time_happened = datetime.strptime(
            flag_in["started_at"], "%Y-%m-%dT%H:%M:%S.%fZ" if "." in flag_in["started_at"] else "%Y-%m-%dT%H:%M:%SZ"
        )
        if tick_start <= time_happened <= tick_end:
            print(f"FLAG_OUT happened at tick {tick} and at {time_happened}")
            found += 1

    if found == 0:
        print(f"No FLAG_OUT at tick {tick}")
    if found > 1:
        print(f"Multiple FLAG_OUT at tick {tick}. There were {found}")

    found = 0
