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

    # Check flow methods for persistence
    flow_methods = [method for method in dir(Flow) if "persist" in method.lower()]
    print(f"Flow persistence methods: {flow_methods}")
except ImportError as e:
    print(f"❌ Flow import failed: {e}")
except Exception:
    print("❌ Could not check Flow methods")

# Check decorators
try:
    from crewai.flow.flow import start  # noqa: F401

    print("✅ start decorator available")
except ImportError as e:
    print(f"❌ Decorator imports failed: {e}")

# Check for alternative persistence options
try:
    from crewai import persist  # noqa: F401

    print("✅ persist available from crewai main")
    
    # Also check crewai.flow.persist in same try block to avoid redefinition
    try:
        from crewai.flow import persist as flow_persist  # noqa: F401
        print("✅ persist available from crewai.flow")
    except ImportError:
        print("❌ persist not available from crewai.flow")
        
except ImportError:
    print("❌ persist not available from crewai main")
    
    # Only try flow persist if main persist failed
    try:
        from crewai.flow import persist  # noqa: F401
        print("✅ persist available from crewai.flow")
    except ImportError:
        print("❌ persist not available from crewai.flow")

# Check the Flow class structure
try:
    from crewai.flow.flow import Flow

    print(
        f"Flow class attributes: {[attr for attr in dir(Flow) if not attr.startswith('_')]}"
    )
except Exception:
    print("❌ Could not check Flow attributes")
