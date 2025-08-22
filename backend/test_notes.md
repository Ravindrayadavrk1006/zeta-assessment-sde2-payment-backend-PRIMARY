# Test Cases Documentation

## Overview
This document describes the test cases implemented in `test_app.py` for the payment decision API.

## Test Cases

### 1. Idempotency Test (`test_idempotency`)
Tests that identical payment requests return identical responses.
- Makes two identical requests with same idempotency key
- Verifies:
  - Both requests succeed (200 status)
  - Both responses are identical
- Uses customer ID: c_123, amount: 50.00 USD

### 2. Rate Limiting Test (`test_rate_limit`)
1. **Test Order Impact**
   - `test_rate_limit` runs before `test_decision_paths`
   - `test_rate_limit` deliberately exhausts the rate limit for customer ID "c_123"
   - When `test_decision_paths` later tries to use "c_123", it hits the rate limit

2. **Rate Limiter Behavior**
   - Rate limit: 5 requests per second per customer ID
   - Rate limits persist across different test functions
   - The same customer ID (c_123) was being used in multiple tests:
     * `test_idempotency` (2 requests)
     * `test_rate_limit` (multiple requests until 429)
     * `test_metrics_endpoint` (3 requests)

3. **Test Structure**
   ```python
   def test_decision_paths(api_headers):
       # ALLOW path test (test_new_customer)
       # REVIEW path test (c_123)
       # BLOCK path test (test_new_customer2)
       # Specific balance test (c_456)
   ```

### Solution Implemented
Added delays between requests in `test_decision_paths` to prevent rate limiting:
```python
# Added 1-second delays before:
- REVIEW path test
- BLOCK path test
- Specific balance test
```

### Alternative Solutions Considered
1. **Reset Rate Limiter**
   - Could add a pytest fixture to reset rate limiter between tests
   - More complex but would solve the root cause

2. **Unique Customer IDs**
   - Use different customer IDs for each test
   - Would avoid rate limit conflicts but require more test data setup

3. **Test Isolation**
   - Move rate limit tests to a separate test class
   - Run them last to avoid affecting other tests

### Current Implementation Details
- Store has predefined test accounts:
  * c_123: 300.00 balance
  * c_456: 150.00 balance
- New customers get default balance of 100.00
- Rate limiter uses token bucket algorithm
- Idempotency keys expire after 24 hours

### Recommendations for Future Testing
1. Use unique customer IDs across different test functions
2. Add rate limiter reset capability for testing
3. Consider test order dependencies when using shared resources
4. Add test fixtures to manage test data state
5. Document rate limit considerations in test comments
