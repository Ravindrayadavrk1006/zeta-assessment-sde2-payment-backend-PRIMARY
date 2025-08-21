from fastapi import FastAPI, Request, Header, HTTPException
import time
from app.models import PaymentRequest, PaymentResponse, AgentStep
from app.store import store
from app.agent import agent_decide
from app.rate_limiter import rate_limiter
from app.utils import generate_request_id, logger, redact_customer_id

app = FastAPI()

API_KEY = "secret-test-key"

metrics = {
    "totalRequests": 0,
    "decisionCounts": {},
    "latencies": []
}

@app.post("/payments/decide", response_model=PaymentResponse)
def decide_payment(request: PaymentRequest,
                   x_api_key: str = Header(None),
                   idempotency_key: str = Header(None)):
    start = time.time()

    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not rate_limiter.allow(request.customerId):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    cached = store.get_idempotency(request.idempotencyKey)
    if cached:
        return cached

    request_id = generate_request_id()
    logger.info(f"[{request_id}] Received request for {redact_customer_id(request.customerId)}")

    decision, reasons, trace = agent_decide(request)

    response = PaymentResponse(
        decision=decision,
        reasons=reasons,
        agentTrace=[AgentStep(**s) for s in trace],
        requestId=request_id
    )

    store.save_idempotency(request.idempotencyKey, response)

    metrics["totalRequests"] += 1
    metrics["decisionCounts"][decision] = metrics["decisionCounts"].get(decision, 0) + 1
    latency = (time.time() - start) * 1000
    metrics["latencies"].append(latency)

    print(f"EVENT: payment.decided {response.model_dump()}")

    return response

@app.get("/metrics")
def get_metrics():
    latencies = sorted(metrics["latencies"])
    p95 = 0
    if latencies:
        idx = int(len(latencies) * 0.95) - 1
        p95 = latencies[max(idx, 0)]
    return {
        "totalRequests": metrics["totalRequests"],
        "decisionCounts": metrics["decisionCounts"],
        "p95LatencyMs": p95
    }
