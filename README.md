# Zeta Assessment Backend

## How to Run Locally

Follow these steps to set up and run the backend project locally:

1. **Install Dependencies**
   ```bash
   # Navigate to the backend directory
   cd backend

   # Create a virtual environment (optional but recommended)
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   # Install required dependencies
   pip install -r requirements.txt
   ```

2. **Run the Backend Server**
   ```bash
   # Run the FastAPI server
   python -m uvicorn server:app
   ```

3. **Access the API**

   - The interactive API documentation is available at `http://127.0.0.1:8000/docs`.
   - Open your browser or API client (e.g., Postman) and navigate to `http://127.0.0.1:8000`.
   

---

## How to Run Tests

Follow these steps to run the backend tests:

1. **Navigate to the Backend Directory**
   ```bash
   cd backend
   ```

2. **Activate the Virtual Environment** (if not already activated):
   ```bash
   # On Windows:
   $env:PYTHONPATH = "."
   # On macOS/Linux:
   export PYTHONPATH=.
   ```
3. **Activate the Virtual Environment** (if not already activated):
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

4. **Run the Tests**
   ```bash
   # Run all tests using pytest
   pytest tests/
   ```

5. **View Test Results**
   - The test results will be displayed in the terminal.
   - Use the `-v` flag for more detailed output:
     ```bash
     pytest -v tests/
     ```

6. **Generate a Test Coverage Report** (optional):
   ```bash
   pytest --cov=app tests/
   ```
   - This will generate a coverage report for the `app` module.
   - Install `pytest-cov` if not already installed:
     ```bash
     pip install pytest-cov
     ```


---

## Architecture Diagram

Below is the architecture diagram for the backend:

![Backend Architecture](architecture-img.png)

The diagram illustrates the flow of requests through the FastAPI server, the decision-making logic, and the integration with external services like Google Generative AI.

---

## What You Optimized

### 1. **Latency**
- Introduced asynchronous processing in FastAPI endpoints to handle I/O-bound tasks efficiently.
- Optimized the `agent_decide` and `agent_decide_ai` functions with retries and fallbacks to ensure faster and more reliable decision-making.
- Reduced redundant computations by caching idempotency keys and frequently accessed data in `store.py`.

### 2. **Simplicity**
- Refactored the `agent_decide_ai` function to include modular retry logic and fallback mechanisms, making the code easier to maintain.
- Consolidated error handling and logging into reusable utilities in `utils.py`.
- Simplified the architecture by using in-memory storage for testing and development, reducing the need for external dependencies.

### 3. **Security**
- Enforced API key validation for all endpoints to restrict unauthorized access.
- Implemented rate limiting in `rate_limiter.py` to prevent abuse and denial-of-service attacks.
- Sanitized user inputs in `models.py` using Pydantic validators to prevent injection attacks.
- Added structured logging for better monitoring and debugging of security-related events.

---

## Trade-offs You Made

### 1. **In-Memory Rate Limiter vs Redis**
- **Decision**: Used an in-memory rate limiter instead of Redis.
- **Reason**: For simplicity and faster development during the initial implementation phase.
- **Trade-off**: While the in-memory rate limiter is sufficient for a single-instance deployment, it does not support distributed systems. Scaling to multiple instances would require replacing it with a Redis-based solution.

### 2. **In-Memory Storage vs Persistent Database**
- **Decision**: Used in-memory storage for customer balances and idempotency keys.
- **Reason**: Simplifies development and testing without requiring database setup.
- **Trade-off**: Data is lost on server restarts, making it unsuitable for production environments. A persistent database like PostgreSQL would be needed for production.

### 3. **Fallback to Non-AI Agent**
- **Decision**: Added a fallback to the non-AI agent in case the AI agent fails.
- **Reason**: Ensures reliability and continuity of service even if the AI model encounters issues.
- **Trade-off**: The fallback logic may not leverage the full capabilities of the AI agent, potentially leading to less optimal decisions.

### 4. **Simplified Security Measures**
- **Decision**: Focused on API key validation and input sanitization.
- **Reason**: Prioritized basic security measures to meet project requirements within the given timeline.
- **Trade-off**: Advanced security features like OAuth2 or JWT-based authentication were not implemented, which may be necessary for production-grade security.

---

## Defense-in-Depth Measures

### 1. **Redacting PII in Logs**
- **Implementation**: Used the `redact_pii` function in `utils.py` to sanitize sensitive information (e.g., customer IDs, payee IDs) before logging.
- **Benefit**: Prevents accidental exposure of personally identifiable information (PII) in logs, enhancing privacy and security.

### 2. **Separating User Display Text from System Reasons**
- **Implementation**: Differentiated between user-facing messages and internal system reasons in the `agent_decide` and `agent_decide_ai` functions.
- **Benefit**: Ensures that sensitive or technical details are not exposed to end users, while maintaining detailed logs for debugging and auditing.

### 3. **Simple Input Validation**
- **Implementation**: Added input validation using Pydantic models in `models.py`.
  - Validated fields like `customerId`, `amount`, and `currency`.
  - Enforced constraints such as minimum/maximum lengths and allowed patterns.
- **Benefit**: Prevents invalid or malicious data from being processed, reducing the risk of errors and security vulnerabilities.