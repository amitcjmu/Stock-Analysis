#!/usr/bin/env python3

try:
    from crewai.flow import persist
    from crewai.flow.flow import Flow, listen, start

    print("✅ CrewAI Flow imports successful")
except ImportError as e:
    print(f"❌ CrewAI Flow import failed: {e}")

try:
    from crewai import Agent, Crew, Task

    print("✅ CrewAI core imports successful")
except ImportError as e:
    print(f"❌ CrewAI core import failed: {e}")

try:
    from crewai.security import Fingerprint

    print("✅ CrewAI Fingerprint import successful")
except ImportError as e:
    print(f"❌ CrewAI Fingerprint import failed: {e}")

try:
    import crewai

    print(
        f"✅ CrewAI package found, version: {getattr(crewai, '__version__', 'unknown')}"
    )
except ImportError as e:
    print(f"❌ CrewAI package not found: {e}")

# Check requirements
try:
    import openai

    print("✅ OpenAI package available")
except ImportError:
    print("❌ OpenAI package missing")

# Check environment variables
import os

print(f"DEEPINFRA_API_KEY: {'set' if os.getenv('DEEPINFRA_API_KEY') else 'not set'}")
print(f"OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
