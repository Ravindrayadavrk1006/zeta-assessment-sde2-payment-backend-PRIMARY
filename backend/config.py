import json
import os

#the config.json is ignored, refer to config_sample.json and provide the secrets in that file and rename it to config.json before starting the server
with open('config.json', "r") as f:
    config = json.load(f)

conf = config.get("application", {})
API_KEY: str = os.getenv("API_KEY", conf["API_KEY"])
    
# Rate Limiting
RATE_LIMIT_PER_SECOND = conf.get("RATE_LIMIT_PER_SECOND", 5)
RATE_LIMIT_WINDOW = conf.get("RATE_LIMIT_WINDOW", 1.0)

# Payment Thresholds
MAX_PAYMENT_AMOUNT = conf.get("MAX_PAYMENT_AMOUNT", 1000000.0)
REVIEW_THRESHOLD = conf.get("REVIEW_THRESHOLD", 100.0)

# Timeouts (in seconds)
LOCK_TIMEOUT = conf.get("LOCK_TIMEOUT", 5)
REQUEST_TIMEOUT = conf.get("REQUEST_TIMEOUT", 30)

# Feature Flags
USE_AI_AGENT = True if conf.get("USE_AI_AGENT") else False

#NOTE: if USE_AI_AGENT is True, then GOOGLE_API_KEY should be provided in config.json
if USE_AI_AGENT:
    os.environ["GOOGLE_API_KEY"] = conf.get("GOOGLE_API_KEY", "yrD8wGKAtJCl-7os")
# Logging
LOG_LEVEL = conf.get("LOG_LEVEL", "INFO")
REDACT_PII = conf.get("REDACT_PII", True)

class Config:
    env_prefix = "PAYNOW_"