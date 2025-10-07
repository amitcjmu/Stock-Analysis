"""Constants for AI enhancement processing."""

# Per-asset timeout (600 seconds = 10 minutes for agentic analysis with LLM calls)
# Frontend polls for 12 minutes (720s), so backend should allow at least 10 minutes
PER_ASSET_TIMEOUT = 600

# Circuit breaker threshold (abort if failure rate > 50% AND at least 2 attempts)
CIRCUIT_BREAKER_THRESHOLD = 0.5
MIN_ATTEMPTS_BEFORE_BREAKING = 2
