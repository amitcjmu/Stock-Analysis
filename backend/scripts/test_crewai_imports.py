#!/usr/bin/env python3

try:
    from crewai.flow import persist  # noqa: F401
    from crewai.flow.flow import Flow, listen, start  # noqa: F401

    print("✅ CrewAI Flow imports successful")
except ImportError as e:
    print(f"❌ CrewAI Flow import failed: {e}")

try:
    from crewai import Agent, Crew, Task  # noqa: F401

    print("✅ CrewAI core imports successful")
except ImportError as e:
    print(f"❌ CrewAI core import failed: {e}")

try:
    from crewai.security import Fingerprint  # noqa: F401

    print("✅ CrewAI Fingerprint import successful")
except ImportError as e:
    print(f"❌ CrewAI Fingerprint import failed: {e}")

try:
    import crewai  # noqa: F401

    print(
        f"✅ CrewAI package found, version: {getattr(crewai, '__version__', 'unknown')}"
    )
except ImportError as e:
    print(f"❌ CrewAI package not found: {e}")

# Check requirements
try:
    import openai  # noqa: F401

    print("✅ OpenAI package available")
except ImportError:
    print("❌ OpenAI package missing")

# Check environment variables
import os

print(f"DEEPINFRA_API_KEY: {'set' if os.getenv('DEEPINFRA_API_KEY') else 'not set'}")
print(f"OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
