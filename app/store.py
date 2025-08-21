import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time
import config as settings
from .utils import structured_log

class LockTimeoutError(Exception):
    """Raised when a lock cannot be acquired within the timeout period"""
    pass

class TransactionError(Exception):
    """Raised when a transaction fails"""
    pass

class InMemoryStore:
    DEFAULT_INITIAL_BALANCE = 100.00  # Default initial balance for new customers

    def __init__(self):
        # Initialize with some test accounts with specific balances
        self.balances: Dict[str, float] = {
            "c_123": 300.00,  # Keep this test account with higher balance for testing
            "c_456": 150.00,  # Additional test account
        }
        self.idempotency: Dict[str, Dict[str, Any]] = {}
        self.idempotency_expiry: Dict[str, datetime] = {}
        self.locks: Dict[str, threading.Lock] = {}
        self.lock_timeouts: Dict[str, datetime] = {}
        self._cleanup_lock = threading.Lock()
        
        # Start cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        def cleanup():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired_data()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def _cleanup_expired_data(self):
        """Clean up expired idempotency keys and stale locks"""
        now = datetime.now()
        with self._cleanup_lock:
            # Clean up expired idempotency keys
            expired_keys = [
                k for k, v in self.idempotency_expiry.items()
                if v < now
            ]
            for k in expired_keys:
                self.idempotency.pop(k, None)
                self.idempotency_expiry.pop(k, None)
            
            # Clean up stale locks
            stale_locks = [
                k for k, v in self.lock_timeouts.items()
                if v < now
            ]
            for k in stale_locks:
                self.locks.pop(k, None)
                self.lock_timeouts.pop(k, None)

    def get_balance(self, customer_id: str) -> float:
        """
        Get customer balance. If customer doesn't exist, automatically initialize
        with default balance and return it.
        """
        if customer_id not in self.balances:
            # Initialize new customer with default balance
            with self._cleanup_lock:  # Use cleanup lock for new account creation
                self.balances[customer_id] = self.DEFAULT_INITIAL_BALANCE
                structured_log("info", "new_account_created", {
                    "customer_id": customer_id,
                    "initial_balance": self.DEFAULT_INITIAL_BALANCE
                })
        return self.balances[customer_id]

    def _acquire_lock(self, customer_id: str) -> bool:
        """Try to acquire a lock with timeout"""
        if customer_id not in self.locks:
            self.locks[customer_id] = threading.Lock()
        
        lock = self.locks[customer_id]
        start_time = time.time()
        
        while time.time() - start_time < settings.LOCK_TIMEOUT:
            if lock.acquire(blocking=False):
                self.lock_timeouts[customer_id] = datetime.now() + timedelta(seconds=settings.LOCK_TIMEOUT)
                return True
            time.sleep(0.1)
        
        return False

    def reserve(self, customer_id: str, amount: float) -> bool:
        """Reserve amount from customer's balance with timeout and retry"""
        if not self._acquire_lock(customer_id):
            structured_log("error", "lock_timeout", {
                "customer_id": customer_id,
                "operation": "reserve"
            })
            raise LockTimeoutError(f"Could not acquire lock for customer {customer_id}")

        try:
            balance = self.get_balance(customer_id)
            if balance >= amount:
                self.balances[customer_id] = balance - amount
                structured_log("info", "balance_reserved", {
                    "customer_id": customer_id,
                    "amount": amount,
                    "new_balance": self.balances[customer_id]
                })
                return True
            return False
        finally:
            self.locks[customer_id].release()

    def save_idempotency(self, key: str, response: Any, ttl_hours: int = 24):
        """Save idempotency key with expiration"""
        self.idempotency[key] = response
        self.idempotency_expiry[key] = datetime.now() + timedelta(hours=ttl_hours)
        structured_log("info", "idempotency_saved", {
            "key": key,
            "expires_at": self.idempotency_expiry[key].isoformat()
        })

    def get_idempotency(self, key: str) -> Optional[Any]:
        """Get idempotency key if not expired"""
        if key in self.idempotency and key in self.idempotency_expiry:
            if datetime.now() < self.idempotency_expiry[key]:
                structured_log("info", "idempotency_hit", {"key": key})
                return self.idempotency[key]
            else:
                # Clean up expired key
                self.idempotency.pop(key)
                self.idempotency_expiry.pop(key)
        return None

store = InMemoryStore()
