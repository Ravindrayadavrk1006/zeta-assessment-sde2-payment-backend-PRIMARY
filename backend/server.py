from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Optional
import asyncio

from app.models import PaymentRequest, PaymentResponse, AgentStep
from app.store import store, LockTimeoutError, TransactionError
from app.agent import agent_decide, agent_decide_ai
from app.rate_limiter import rate_limiter
from app.utils import (
    generate_request_id, structured_log, timed_operation,
    context_logger, redact_customer_id
)
import config as settings
import os
app = FastAPI(title="PayNow API",
             description="Payment processing API with AI-assisted decision making",
             version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics storage
metrics = {
    "totalRequests": 0,
    "decisionCounts": {},
    "latencies": [],
    "errors": {},
}

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Set correlation ID for request
    correlation_id = request.headers.get("X-Correlation-ID") or generate_request_id()
    context_logger.set_correlation_id(correlation_id)
    
    # Add timing headers
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

@app.exception_handler(LockTimeoutError)
async def lock_timeout_handler(request: Request, exc: LockTimeoutError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)}
    )

@app.exception_handler(TransactionError)
async def transaction_error_handler(request: Request, exc: TransactionError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.post("/payments/decide", response_model=PaymentResponse)
async def decide_payment(
    request: PaymentRequest,
    x_api_key: str = Header(None),
):
    with timed_operation("decide_payment"):
        # Validate API key
        if x_api_key != settings.API_KEY:
            structured_log("warning", "auth_failed", {
                "reason": "invalid_api_key"
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key"
            )

        # Check rate limit
        if not rate_limiter.allow(request.customerId):
            structured_log("warning", "rate_limit_exceeded", {
                "customer_id": request.customerId
            })
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        idempotency_key = request.idempotencyKey
        # Check idempotency
        if idempotency_key:
            cached = store.get_idempotency(idempotency_key)
            if cached:
                return cached

        request_id = generate_request_id()
        structured_log("info", "payment_request_received", {
            "request_id": request_id,
            "customer_id": request.customerId,
            "amount": str(request.amount),
            "currency": request.currency
        })

        try:
            # Use AI agent if enabled, otherwise use regular agent
            agent = agent_decide_ai if settings.USE_AI_AGENT else agent_decide
            decision, reasons, trace = await asyncio.to_thread(agent, request)

            response = PaymentResponse(
                decision=decision,
                reasons=reasons,
                agentTrace=[AgentStep(**s) for s in trace],
                requestId=request_id
            )

            if idempotency_key:
                store.save_idempotency(idempotency_key, response)

            # Update metrics
            metrics["totalRequests"] += 1
            metrics["decisionCounts"][decision] = metrics["decisionCounts"].get(decision, 0) + 1
            
            # Log decision event
            structured_log("info", "payment.decided", {
                "request_id": request_id,
                "decision": decision,
                "reasons": reasons,
                "customer_id": request.customerId
            })

            return response

        except Exception as e:
            metrics["errors"][type(e).__name__] = metrics["errors"].get(type(e).__name__, 0) + 1
            
            # Get exception info including traceback
            import sys
            exc_info = sys.exc_info()
            
            structured_log("error", "payment_processing_failed", {
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": True,  # This signals to structured_log to include traceback
                "exc_info": exc_info
            })

            # Handle validation errors specifically
            if "ValidationError" in type(e).__name__:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Validation error: {str(e)}"
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred processing the payment"
            )

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



if __name__ == "__main__":
    import uvicorn
    # Start FastAPI server with configuration
    uvicorn.run(
        app,
        host =  settings.conf.get("host"),
        port = settings.conf.get("port")
    )