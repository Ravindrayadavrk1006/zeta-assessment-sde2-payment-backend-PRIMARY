import uuid
from .store import store

from langchain_core.tools import Tool

from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os 
def get_balance(customer_id: str):
    return store.get_balance(customer_id)

def get_risk_signals(customer_id: str):
    # Hardcoded risk for demo
    return {"recent_disputes": 2 if customer_id == "c_123" else 0,
            "device_change": True}

def create_case(customer_id: str, reason: str):
    return f"case_{uuid.uuid4().hex[:6]}"

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
        case_id = create_case(payment.customerId, ", ".join(reasons))
        trace.append({"step": "tool:createCase", "detail": f"case_id={case_id}"})

    trace.append({"step": "tool:recommend", "detail": decision})

    return decision, reasons, trace



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
   description="Create a case for manual review or block"
)

tools = [
    get_balance_tool,
    get_risk_signals_tool,
    create_case_tool
]

os.environ["GOOGLE_API_KEY"] = "your-google-api-key"

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.0)

def agent_decide_ai(payment):
    from .store import store

    trace = []

    # Build prompt for AI
    messages = [
        SystemMessage(content="You are an agent that decides payment transactions: allow, review, or block."),
        HumanMessage(content=f"Customer {payment.customerID} wants to pay {payment.amount} {payment.currency} to {payment.payeeId}. Check balance, risk, and rules.")
    ]

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # Run agent
    result = agent.run(input=messages[1].content)

    # For demo, parse AI output into decision, reasons, trace
    # This depends on how you instruct the AI
    decision = "review"  # placeholder
    reasons = ["recent_disputes", "amount_above_daily_threshold"]
    trace.append({"step": "AI reasoning", "detail": result})

    return decision, reasons, trace
