import threading

class InMemoryStore:
    def __init__(self):
        self.balances = {"c_123": 300.0}
        self.idempotency = {}
        self.locks = {}

    def get_balance(self, customer_id: str) -> float:
        return self.balances.get(customer_id, 0.0)

    def reserve(self, customer_id: str, amount: float):
        if customer_id not in self.locks:
            self.locks[customer_id] = threading.Lock()
        with self.locks[customer_id]:
            balance = self.get_balance(customer_id)
            if balance >= amount:
                self.balances[customer_id] = balance - amount
                return True
            return False

    def save_idempotency(self, key: str, response):
        self.idempotency[key] = response

    def get_idempotency(self, key: str):
        return self.idempotency.get(key)


store = InMemoryStore()
