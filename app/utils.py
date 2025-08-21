import logging
import uuid

logger = logging.getLogger("paynow")
logging.basicConfig(level=logging.INFO)

def generate_request_id():
    return f"req_{uuid.uuid4().hex[:6]}"

def redact_customer_id(cid: str) -> str:
    return cid[:2] + "***"
