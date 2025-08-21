from pydantic import BaseModel, Field, validator
from typing import List, Dict, Literal
import re
from datetime import datetime

class PaymentRequest(BaseModel):
    customerId: str = Field(..., pattern="^[a-zA-Z0-9_-]+$", min_length=3)
    amount: float = Field(..., gt=0, le=1000000)
    currency: str = Field(..., min_length=3, max_length=3)
    payeeId: str = Field(..., pattern="^[a-zA-Z0-9_-]+$", min_length=3)
    idempotencyKey: str = Field(..., min_length=3)

    @validator('currency')
    def validate_currency(cls, v):
        if v not in ['USD', 'EUR', 'GBP', 'JPY']:  # Add more currencies as needed
            raise ValueError('Unsupported currency')
        return v

    @validator('customerId', 'payeeId')
    def validate_ids(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid ID format')
        return v

class AgentStep(BaseModel):
    step: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.now)

class PaymentResponse(BaseModel):
    decision: Literal['allow', 'review', 'block']
    reasons: List[str] = Field(..., min_items=1)
    agentTrace: List[AgentStep]
    requestId: str = Field(..., pattern=r'^req_[a-f0-9]+$')

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "review",
                "reasons": ["recent_disputes", "amount_above_daily_threshold"],
                "agentTrace": [
                    {"step": "plan", "detail": "Check balance, risk, and limits"},
                    {"step": "tool:getBalance", "detail": "balance=300.00"}
                ],
                "requestId": "req_abc123"
            }
        }
