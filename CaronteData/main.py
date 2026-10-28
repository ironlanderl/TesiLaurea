import json
from pprint import pprint
import requests

RULE_ID = "6ae21a2b0000000000000001"
PORT = 2222

data = {}

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={RULE_ID}&service_port={PORT}")

data: list[str] = r.json()

pprint(data)

print(f"len is {len(data)}")

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={RULE_ID}&service_port={PORT}&from={data[-1]['id']}")

data.extend(r.json())

pprint(data)

print(f"len is {len(data)}")

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={RULE_ID}&service_port={PORT}&from={data[-1]['id']}")

data.extend(r.json())

pprint(data)

print(f"len is {len(data)}")

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={RULE_ID}&service_port={PORT}&from={data[-1]['id']}")

data.extend(r.json())

pprint(data)

print(f"len is {len(data)}")

r = requests.get(f"http://127.0.0.1:3333/api/connections?matched_rules={RULE_ID}&service_port={PORT}&from={data[-1]['id']}")

data.extend(r.json())

pprint(data)

print(f"len is {len(data)}")


# Loop for each tick with time.
# Check for each data point if it is inside of the time frame for the tick
# Calculate the difference between tick start and FLAG_IN
# Save both the min and max differences.
