from fastapi.testclient import TestClient
from server import app, API_KEY

client = TestClient(app)

def test_idempotency():
    body = {"customerId": "c_123", "amount": 10, "currency": "USD", "payeeId": "p_1", "idempotencyKey": "idem1"}
    headers = {"X-API-Key": API_KEY}
    r1 = client.post("/payments/decide", json=body, headers=headers)
    r2 = client.post("/payments/decide", json=body, headers=headers)
    assert r1.json() == r2.json()

def test_rate_limit():
    body = {"customerId": "c_999", "amount": 1, "currency": "USD", "payeeId": "p_1", "idempotencyKey": "idem2"}
    headers = {"X-API-Key": API_KEY}
    for _ in range(5):
        client.post("/payments/decide", json=body, headers=headers)
    r = client.post("/payments/decide", json=body, headers=headers)
    assert r.status_code == 429

def test_allow_path():
    body = {"customerId": "c_123", "amount": 50, "currency": "USD", "payeeId": "p_1", "idempotencyKey": "idem3"}
    headers = {"X-API-Key": API_KEY}
    r = client.post("/payments/decide", json=body, headers=headers)
    assert r.json()["decision"] in ["allow", "review", "block"]
