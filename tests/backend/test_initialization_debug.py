import time
import sys

def test_step(step_name, func):
    """Test a step and measure time."""
    print(f"🔄 {step_name}...")
    start_time = time.time()
    try:
        result = func()
        end_time = time.time()
        print(f"✅ {step_name} completed in {end_time - start_time:.2f}s")
        return True, result
    except Exception as e:
        end_time = time.time()
        print(f"❌ {step_name} failed in {end_time - start_time:.2f}s: {e}")
        return False, str(e)

def step1_basic_imports():
    """Test basic imports."""
    import logging
    from typing import Dict, Any
    from datetime import datetime
    return "Basic imports OK"

def step2_config_import():
    """Test config import."""
    from app.core.config import settings
    return f"Config loaded: CREWAI_ENABLED={settings.CREWAI_ENABLED}"

def step3_memory_import():
    """Test memory service import."""
    from app.services.memory import AgentMemory
    return "Memory service imported"

def step4_memory_init():
    """Test memory initialization."""
    from app.services.memory import AgentMemory
    memory = AgentMemory()
    return f"Memory initialized with {len(memory.experiences)} experience types"

def step5_deepinfra_import():
    """Test DeepInfra LLM import."""
    from app.services.deepinfra_llm import create_deepinfra_llm
    return "DeepInfra LLM imported"

def step6_deepinfra_init():
    """Test DeepInfra LLM initialization."""
    from app.services.deepinfra_llm import create_deepinfra_llm
    from app.core.config import settings
    llm = create_deepinfra_llm(
        api_token=settings.DEEPINFRA_API_KEY,
        model_id=settings.DEEPINFRA_MODEL
    )
    return f"DeepInfra LLM created: {type(llm).__name__}"

def step7_agents_import():
    """Test agents import."""
    from app.services.agents import AgentManager
    return "Agent manager imported"

def step8_agents_init():
    """Test agents initialization."""
    from app.services.agents import AgentManager
    from app.services.deepinfra_llm import create_deepinfra_llm
    from app.core.config import settings
    
    llm = create_deepinfra_llm(
        api_token=settings.DEEPINFRA_API_KEY,
        model_id=settings.DEEPINFRA_MODEL
    )
    agent_manager = AgentManager(llm)
    return f"Agent manager created with {len(agent_manager.agents)} agents"

def step9_crewai_service_import():
    """Test CrewAI service import (this is where it likely hangs)."""
    from app.services.crewai_service_modular import CrewAIService
    return "CrewAI service class imported"

def step10_crewai_service_init():
    """Test CrewAI service initialization."""
    from app.services.crewai_service_modular import CrewAIService
    service = CrewAIService()
    return f"CrewAI service initialized"

def step11_crewai_global_import():
    """Test importing the global crewai_service instance."""
    from app.services.crewai_service_modular import crewai_service
    return f"Global CrewAI service imported: {type(crewai_service).__name__}"

if __name__ == "__main__":
    print("=" * 70)
    print("CrewAI Service Initialization Debug Test")
    print("=" * 70)
    
    steps = [
        ("Basic imports", step1_basic_imports),
        ("Config import", step2_config_import),
        ("Memory service import", step3_memory_import),
        ("Memory initialization", step4_memory_init),
        ("DeepInfra LLM import", step5_deepinfra_import),
        ("DeepInfra LLM initialization", step6_deepinfra_init),
        ("Agents import", step7_agents_import),
        ("Agents initialization", step8_agents_init),
        ("CrewAI service import", step9_crewai_service_import),
        ("CrewAI service initialization", step10_crewai_service_init),
        ("Global CrewAI service import", step11_crewai_global_import),
    ]
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        success, result = test_step(f"Step {i}: {step_name}", step_func)
        if not success:
            print(f"\n💥 HANGING DETECTED at Step {i}: {step_name}")
            print(f"Error: {result}")
            break
        print(f"   Result: {result}")
        print()
    else:
        print("🎉 All initialization steps completed successfully!") 