import uuid
from .store import store

from langchain_core.tools import Tool

from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

import os 
import json

def get_balance(customer_id: str):
    from .store import store
    return store.get_balance(customer_id)

def get_risk_signals(customer_id: str):
    from .store import store
    from datetime import datetime, timedelta
    
    # For demo purposes, we'll simulate different risk scenarios based on customer_id
    # In a real system, these would come from actual database queries and risk engines
    
    # Simulate current timestamp
    current_time = datetime.now()
    
    # Initialize risk signals dictionary
    risk_signals = {
        "recent_disputes": 0,           # Number of payment disputes in last 30 days
        "device_change": False,         # New device detection
        "velocity_check": {             # Payment velocity/frequency checks
            "last_24h_count": 0,        # Number of transactions in last 24 hours
            "last_24h_amount": 0.0,     # Total amount in last 24 hours
        },
        "location_risk": {             # Location-based risks
            "unusual_country": False,   # Payment from unusual country
            "location_mismatch": False, # IP location != card country
        },
        "account_risk": {              # Account-related risks
            "account_age_days": 365,    # Age of the account
            "previous_failures": 0,     # Recent failed transactions
            "suspicious_activity": False # Any flagged suspicious activity
        },
        "transaction_pattern": {        # Transaction pattern analysis
            "unusual_time": False,      # Outside normal transaction hours
            "unusual_amount": False,    # Significantly different from usual amounts
            "high_risk_merchant": False # Known high-risk merchant category
        }
    }
    #TODO: we are simulating risk signals, in a real system these would be fetched from a database or risk engine
    # Simulate different risk profiles based on customer_id patterns
    if customer_id == "c_123":  # High risk customer
        risk_signals.update({
            "recent_disputes": 2,
            "device_change": True,
            "velocity_check": {
                "last_24h_count": 15,
                "last_24h_amount": 2000.0
            },
            "account_risk": {
                "previous_failures": 3,
                "suspicious_activity": True
            }
        })
    elif customer_id.startswith("new_"):  # New customer
        risk_signals.update({
            "account_risk": {
                "account_age_days": 5,
                "previous_failures": 0
            },
            "transaction_pattern": {
                "unusual_amount": True
            }
        })
    elif customer_id.startswith("intl_"):  # International customer
        risk_signals.update({
            "location_risk": {
                "unusual_country": True,
                "location_mismatch": True
            }
        })
    
    return risk_signals

def create_case(customer_id_reason_json: str):
    import json
    input_json = json.loads(customer_id_reason_json)
    customer_id = input_json.get("customer_id", "")
    reason = input_json.get("reason", "")
    
    return f"case_{uuid.uuid4().hex[:6]}"


#non AI agent decision function
def agent_decide(payment):
    trace = []
    reasons = []

    trace.append({"step": "plan", "detail": "Check balance, risk, and limits"})

    balance = get_balance(payment.customerId)
    trace.append({"step": "tool:getBalance", "detail": f"balance={balance:.2f}"})

    risk = get_risk_signals(payment.customerId)
    trace.append({"step": "tool:getRiskSignals", "detail": str(risk)})

    decision = "allow"

    if balance < payment.amount:
        decision = "block"
        reasons.append("insufficient_balance")
    if payment.amount > 100.0:
        decision = "review"
        reasons.append("amount_above_daily_threshold")
    if risk["recent_disputes"] > 0:
        decision = "review"
        reasons.append("recent_disputes")

    if decision == "allow":
        ok = store.reserve(payment.customerId, payment.amount)
        if not ok:
            decision = "block"
            reasons = ["insufficient_balance"]

    if decision in ["review", "block"]:
        json_input = json.dumps({
            "customer_id": payment.customerId,
            "reason": ", ".join(reasons)
        })
        case_id = create_case(json_input)
        trace.append({"step": "tool:createCase", "detail": f"case_id={case_id}"})

    trace.append({"step": "tool:recommend", "detail": decision})

    return decision, reasons, trace


#NOTE: This is an AI agent decision function that uses Google Generative AI to make decisions based on the payment request.
#creating tools

get_balance_tool = Tool(
    name ="get_balance",
    func= get_balance,
    description=""" get customer's current balance
    """
)

get_risk_signals_tool = Tool(
    name = "get_risk_signal",
    func = get_risk_signals,
    description="Check for recent disputes or suspicious device changes"
)

create_case_tool = Tool(
    name = "create_case",
    func = create_case,
    description="""Create a case for manual review or block decisions.
    Args:
        the input shoudld be a json string with below two keys
            customer_id (str): The ID of the customer
            reason (str): The reason for creating the case (e.g., 'recent_disputes, suspicious_activity')
    Returns:
        str: The created case ID
    """
)

tools = [
    get_balance_tool,
    get_risk_signals_tool,
    create_case_tool
]

os.environ["GOOGLE_API_KEY"] = "AIzaSyDYdu8b50EGP8vtZN-yrD8wGKAtJCl-7os"

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.0)

def agent_decide_ai(payment):
    from .store import store

    trace = []
    reasons = []

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # Custom prompt that enforces tool usage and clear decision making
    custom_prompt = f"""You are a payment transaction agent. Use the provided tools to evaluate this payment:
    Customer {payment.customerId} wants to pay {payment.amount} {payment.currency} to {payment.payeeId}

    Follow these steps:
    1. Use get_balance tool to check customer's balance
    2. Use get_risk_signal tool to check for risk factors
    3. Make a decision based on these rules:
       - If balance < payment amount: BLOCK (insufficient_balance)
       - If payment > 100.0: REVIEW (amount_above_daily_threshold)
       - If recent disputes > 0: REVIEW (recent_disputes)
       - If suspicious activity or high velocity: REVIEW
       - Otherwise: ALLOW
    4. If decision is REVIEW or BLOCK, use create_case tool with:
        json input:
        "{{
            "customer_id": "{payment.customerId}",
            "reason": "comma-separated reasons"
        }}"
       - First key value: customer_id (the customer's ID)
       - second key value: a comma-separated string of all the reasons

    Example create_case usage:

    Return your analysis in this format:
    DECISION: [allow/review/block]
    REASONS: [comma-separated list of reasons]
    """

    trace.append({"step": "plan", "detail": "Initiating payment evaluation process"})

    # Let the agent make the decision using tools
    analysis = agent.run(custom_prompt)
    
    # Extract decision and reasons from AI analysis
    decision = "review"  # Default to review
    if "DECISION: allow" in analysis.lower():
        decision = "allow"
    elif "DECISION: block" in analysis.lower():
        decision = "block"
    
    # Parse reasons from the AI's response
    reasons = []
    if "insufficient_balance" in analysis.lower():
        reasons.append("insufficient_balance")
    if "amount_above_daily_threshold" in analysis.lower():
        reasons.append("amount_above_daily_threshold")
    if "recent_disputes" in analysis.lower():
        reasons.append("recent_disputes")
    if "suspicious_activity" in analysis.lower():
        reasons.append("suspicious_activity")
    if "high_velocity" in analysis.lower():
        reasons.append("high_transaction_velocity")
    
    # If no reasons were found but we have a review/block decision, add a generic reason
    if decision in ["review", "block"] and not reasons:
        reasons.append("ai_flagged_suspicious")

    # For ALLOW decisions, verify balance can be reserved
    if decision == "allow":
        ok = store.reserve(payment.customerId, payment.amount)
        if not ok:
            decision = "block"
            reasons = ["insufficient_balance"]
            trace.append({"step": "reserve", "detail": "Balance reservation failed"})

    # Create case for review/block decisions
    if decision in ["review", "block"]:
        json_input = json.dumps({
            "customer_id": payment.customerId,
            "reason": ", ".join(reasons)
        })
        case_id = create_case(json_input)
        trace.append({"step": "tool:createCase", "detail": f"case_id={case_id}"})

    trace.append({"step": "AI analysis", "detail": analysis})
    trace.append({"step": "final_decision", "detail": f"Decision: {decision}, Reasons: {reasons}"})

    return decision, reasons, trace
