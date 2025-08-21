from pydantic import BaseModel
from typing import List, Dict

class PaymentRequest(BaseModel):
    customerId: str
    amount: float
    currency: str
    payeeId: str
    idempotencyKey: str

class AgentStep(BaseModel):
    step: str
    detail: str

class PaymentResponse(BaseModel):
    decision: str
    reasons: List[str]
    agentTrace: List[AgentStep]
    requestId: str
