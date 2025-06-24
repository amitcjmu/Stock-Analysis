#!/usr/bin/env python3

# Test the correct import path for persist
try:
    from crewai.flow import persist
    print("✅ persist decorator imported successfully from crewai.flow")
    print(f"persist decorator: {persist}")
except ImportError as e:
    print(f"❌ persist import failed: {e}")

# Check FlowPersistence
try:
    from crewai.flow.flow import FlowPersistence
    print("✅ FlowPersistence imported successfully")
    print(f"FlowPersistence: {FlowPersistence}")
    print(f"FlowPersistence methods: {[attr for attr in dir(FlowPersistence) if not attr.startswith('_')]}")
except ImportError as e:
    print(f"❌ FlowPersistence import failed: {e}")

# Test if we can create a simple Flow with persistence
try:
    from crewai.flow.flow import Flow, start, listen
    from crewai.flow import persist
    from pydantic import BaseModel
    
    class TestState(BaseModel):
        counter: int = 0
        message: str = ""
    
    @persist()
    class TestFlow(Flow[TestState]):
        @start()
        def start_method(self):
            self.state.counter = 1
            self.state.message = "Started"
            return "started"
        
        @listen(start_method)
        def finish_method(self, result):
            self.state.counter = 2
            self.state.message = "Finished"
            return "finished"
    
    print("✅ Flow with persist decorator created successfully")
    
    # Test instantiation
    flow = TestFlow()
    print(f"✅ Flow instantiated successfully with state: {flow.state}")
    
except Exception as e:
    print(f"❌ Flow creation failed: {e}")

# Check if Flow has automatic state persistence
try:
    from crewai.flow.flow import Flow
    print(f"Flow class has state attribute: {hasattr(Flow, 'state')}")
    print(f"Flow class documentation: {Flow.__doc__}")
except Exception as e:
    print(f"❌ Could not check Flow class: {e}") 