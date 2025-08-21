import json
from fastapi.testclient import TestClient
from server import app, API_KEY

client = TestClient(app)

with open("sample_evals.json") as f:
    cases = json.load(f)

passed = 0
for case in cases:
    headers = {"X-API-Key": API_KEY}
    r = client.post("/payments/decide", json=case["input"], headers=headers)
    decision = r.json()["decision"]
    print(f"Input={case['input']} -> Got={decision}, Expected={case['expected']}")
    if decision == case["expected"]:
        passed += 1

print(f"Accuracy: {passed}/{len(cases)} = {passed/len(cases):.2f}")
