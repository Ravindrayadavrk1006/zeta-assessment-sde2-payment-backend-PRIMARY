import logging
import uuid
import json
from datetime import datetime
from typing import Any, Dict
from contextlib import contextmanager
import time
import traceback
import config as settings

# Configure logging
logger = logging.getLogger("paynow")
formatter = logging.Formatter(
    '%(asctime)s - %(module)s:%(funcName)s:%(lineno)d - %(levelname)s - [%(correlation_id)s] - %(message)s'
)

# Add handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

class ContextLogger:
    def __init__(self):
        self.correlation_id = None

    def set_correlation_id(self, correlation_id: str):
        self.correlation_id = correlation_id

    def get_correlation_id(self) -> str:
        return self.correlation_id or 'no-correlation-id'

context_logger = ContextLogger()

def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:6]}"

def redact_customer_id(cid: str) -> str:
    if not settings.REDACT_PII:
        return cid
    return cid[:2] + "***" + (cid[-2:] if len(cid) > 4 else "")

def redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact PII from dictionaries for logging"""
    pii_fields = ['customerId', 'payeeId', 'email', 'phone']
    redacted = data.copy()
    for field in pii_fields:
        if field in redacted:
            redacted[field] = redact_customer_id(str(redacted[field]))
    return redacted

def structured_log(level: str, event: str, data: Dict[str, Any]):
    """Log structured data with correlation ID and PII redaction"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "correlation_id": context_logger.get_correlation_id(),
        "data": redact_pii(data)
    }
    
    # Add stack trace for error events
    if level.lower() == "error":
        if data.get("traceback", False) and "exc_info" in data:
            exc_type, exc_value, exc_tb = data["exc_info"]
            # Format exception information
            stack_trace = traceback.format_exception(exc_type, exc_value, exc_tb)
            log_data["stack_trace"] = stack_trace
            # Remove exc_info from data to avoid serialization issues
            data.pop("exc_info")
        else:
            # Fallback to getting current stack if no exception info provided
            stack_trace = traceback.format_stack()
            # Remove the last frame which is this function call
            stack_trace = stack_trace[:-1]
            log_data["stack_trace"] = stack_trace
    
    getattr(logger, level.lower())(
        json.dumps(log_data),
        extra={"correlation_id": context_logger.get_correlation_id()}
    )

@contextmanager
def timed_operation(operation_name: str):
    """Context manager for timing operations"""
    start = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start) * 1000
        structured_log(
            "info",
            "operation_timing",
            {
                "operation": operation_name,
                "duration_ms": duration
            }
        )
