#!/usr/bin/env python3

import crewai

print(f"CrewAI version: {getattr(crewai, '__version__', 'unknown')}")

# Check what's available in crewai.flow.flow
try:
    from crewai.flow.flow import Flow
    print("✅ Flow class available")
    
    # Check what's available in the Flow module
    from crewai.flow import flow
    print("Available in crewai.flow.flow:", dir(flow))
except ImportError as e:
    print(f"❌ Flow import failed: {e}")

# Check decorators
try:
    from crewai.flow.flow import listen, start
    print("✅ start and listen decorators available")
except ImportError as e:
    print(f"❌ Decorator imports failed: {e}")

# Check for alternative persistence options
try:
    from crewai import persist
    print("✅ persist available from crewai main")
except ImportError:
    print("❌ persist not available from crewai main")

try:
    from crewai.flow import persist
    print("✅ persist available from crewai.flow")
except ImportError:
    print("❌ persist not available from crewai.flow")

# Check if persistence is built into Flow class
try:
    from crewai.flow.flow import Flow
    flow_methods = [method for method in dir(Flow) if 'persist' in method.lower()]
    print(f"Flow persistence methods: {flow_methods}")
except:
    print("❌ Could not check Flow methods")

# Check the Flow class structure
try:
    from crewai.flow.flow import Flow
    print(f"Flow class attributes: {[attr for attr in dir(Flow) if not attr.startswith('_')]}")
except:
    print("❌ Could not check Flow attributes") 