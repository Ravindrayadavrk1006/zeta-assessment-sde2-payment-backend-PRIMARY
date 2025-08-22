import pytest
from fastapi.testclient import TestClient
from server import app
import config as settings
from app.store import store, LockTimeoutError
import threading
import time
import asyncio

client = TestClient(app)

@pytest.fixture
def api_headers():
    return {"X-API-Key": settings.API_KEY}

@pytest.fixture
def valid_payment_request():
    return {
        "customerId": "c_123",
        "amount": 50.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "test_idem_key"
    }

def test_idempotency(api_headers, valid_payment_request):
    """Test that identical requests return identical responses"""
    r1 = client.post("/payments/decide", json=valid_payment_request, headers=api_headers)
    assert r1.status_code == 200
    r2 = client.post("/payments/decide", json=valid_payment_request, headers=api_headers)
    assert r2.status_code == 200
    assert r1.json() == r2.json()

def test_rate_limit(api_headers, valid_payment_request):
    """Test rate limiting functionality"""
    # Clear any existing rate limit state
    for _ in range(settings.RATE_LIMIT_PER_SECOND + 1):
        r = client.post("/payments/decide", json=valid_payment_request, headers=api_headers)
        if r.status_code == 429:
            break
    else:
        pytest.fail("Rate limit was not enforced")

def test_authentication(valid_payment_request):
    """Test API key authentication"""
    # Test missing API key
    r = client.post("/payments/decide", json=valid_payment_request)
    assert r.status_code == 403

    # Test invalid API key
    r = client.post("/payments/decide", json=valid_payment_request, 
                    headers={"X-API-Key": "invalid-key"})
    assert r.status_code == 403

def test_input_validation(api_headers):
    """Test input validation"""
    # Test invalid amount
    invalid_request = {
        "customerId": "c_123",
        "amount": -50.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "test_key"
    }
    r = client.post("/payments/decide", json=invalid_request, headers=api_headers)
    assert r.status_code == 422

    # Test invalid currency
    invalid_request["amount"] = 50.00
    invalid_request["currency"] = "INVALID"
    r = client.post("/payments/decide", json=invalid_request, headers=api_headers)
    assert r.status_code == 422

def test_decision_paths(api_headers):
    """Test different decision paths"""
    # Test ALLOW path (small amount, new customer with default balance)
    allow_request = {
        "customerId": "test_new_customer",  # New customer gets 100.0 balance
        "amount": 50.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "allow_test"
    }
    r = client.post("/payments/decide", json=allow_request, headers=api_headers)
    assert r.status_code == 200
    response = r.json()
    assert response["decision"] == "allow"
    
    # Verify default balance was created
    assert store.get_balance("test_new_customer") == 50.0  # Initial balance 100.0 - payment 50.0

    # Add delay to avoid rate limiting
    time.sleep(1)

    # Test REVIEW path (amount above threshold but within balance)
    review_request = {
        "customerId": "c_123",  # Has 300.0 balance
        "amount": 150.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "review_test"
    }
    r = client.post("/payments/decide", json=review_request, headers=api_headers)
    assert r.status_code == 200
    assert r.json()["decision"] == "review"

    # Add delay to avoid rate limiting
    time.sleep(1)

    # Test BLOCK path (amount above default balance for new customer)
    block_request = {
        "customerId": "test_new_customer2",  # Will get 100.0 balance
        "amount": 150.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "block_test"
    }
    r = client.post("/payments/decide", json=block_request, headers=api_headers)
    assert r.status_code == 200
    assert r.json()["decision"] == "block"

    # Add delay to avoid rate limiting
    time.sleep(1)

    # Test existing account with specific balance
    specific_balance_request = {
        "customerId": "c_456",  # Has 150.0 balance
        "amount": 120.00,
        "currency": "USD",
        "payeeId": "p_1",
        "idempotencyKey": "specific_test"
    }
    r = client.post("/payments/decide", json=specific_balance_request, headers=api_headers)
    assert r.status_code == 200
    assert r.json()["decision"] == "review"  # Amount > 100.0 triggers review

def test_metrics_endpoint(api_headers, valid_payment_request):
    """Test metrics endpoint"""
    # Make a few requests to generate metrics
    for _ in range(3):
        client.post("/payments/decide", 
                   json=valid_payment_request, 
                   headers=api_headers)

    # Check metrics
    r = client.get("/metrics")
    assert r.status_code == 200
    metrics = r.json()
    assert metrics["totalRequests"] > 0
    assert len(metrics["decisionCounts"]) > 0
    assert "p95LatencyMs" in metrics




def test_concurrent_requests(api_headers):
    """Test concurrent request handling"""
    def make_request():
        request = {
            "customerId": "c_123",
            "amount": 100.00,
            "currency": "USD",
            "payeeId": "p_1",
            "idempotencyKey": f"concurrent_{threading.get_ident()}"
        }
        return client.post("/payments/decide", json=request, headers=api_headers)

    # Create multiple threads to simulate concurrent requests
    threads = []
    responses = []
    for _ in range(5):
        thread = threading.Thread(target=lambda: responses.append(make_request()))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that all requests were processed
    assert len(responses) == 5
    # Check that at least one request succeeded
    assert any(r.status_code == 200 for r in responses)