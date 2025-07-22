"""CrewAI Memory Management Module"""

try:
    from .tenant_memory_manager import LearningScope, MemoryIsolationLevel, TenantMemoryManager
    MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError:
    MEMORY_MANAGEMENT_AVAILABLE = False
    class LearningScope:
        DISABLED = "disabled"
    class TenantMemoryManager:
        def __init__(self, *args, **kwargs): pass

__all__ = ["TenantMemoryManager", "LearningScope", "MEMORY_MANAGEMENT_AVAILABLE"]
