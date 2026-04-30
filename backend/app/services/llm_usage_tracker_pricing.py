"""Default pricing constants for LLM usage tracker."""

DEFAULT_PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    },
    "deepinfra": {
        "meta-llama/Llama-2-70b-chat-hf": {"input": 0.0007, "output": 0.0009},
        "meta-llama/Llama-2-13b-chat-hf": {"input": 0.0002, "output": 0.0002},
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.0005, "output": 0.0005},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-opus-4-6": {"input": 0.005, "output": 0.025},
    },
}
