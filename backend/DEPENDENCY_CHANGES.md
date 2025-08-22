# Dependency Changes Documentation

## Summary
This document explains the dependency changes made to resolve Docker build conflicts and security vulnerabilities.

## Changes Made

### 1. Removed Dependencies
- **crewai-tools==0.51.1**: Removed due to irreconcilable dependency conflict with embedchain

### 2. Downgraded Dependencies
- **mem0ai**: 0.1.114 → 0.1.99
  - Reason: Version 0.1.114 had pytz version conflicts
  - Impact: None - using stable version with same API

- **pytz**: 2025.2 → 2024.2
  - Reason: Required by mem0ai 0.1.99
  - Impact: None - timezone data is backwards compatible

### 3. Security Updates
- **pypdf**: Updated to 6.0.0
  - Reason: Fix CVE-2025-3429 RAM exhaustion vulnerability
  - Impact: Positive - security vulnerability resolved

## Conflict Resolution Details

### The Original Conflict
```
embedchain (required by crewai-tools) needs:
  - chromadb <0.5.0
  - pypdf <6.0.0

crewai needs:
  - chromadb >=0.5.23

Security requirement:
  - pypdf ==6.0.0 (CVE-2025-3429 fix)
```

This created an unsolvable dependency conflict.

### Solution Applied
1. Removed crewai-tools package (optional extension)
2. Retained core crewai functionality through main package
3. Implemented fallback patterns for tool functionality

## Impact Analysis

### What Still Works
- ✅ All CrewAI core functionality (Agents, Tasks, Crews, Flows)
- ✅ Custom tool creation using `crewai.tools.BaseTool`
- ✅ Memory systems (mem0ai)
- ✅ All existing application features

### What Was Removed
- ❌ Pre-built tools from crewai-tools package:
  - Web scraping tools
  - Search tools (SerperDev, Tavily, etc.)
  - File operation tools
  - Database search tools

### Mitigation Strategy
If pre-built tools are needed, they can be:
1. Implemented as custom tools using `BaseTool`
2. Installed separately (e.g., `pip install tavily-python`)
3. Created using alternative packages (beautifulsoup4, requests, etc.)

## Code Adaptations

### Fallback Pattern Implementation
```python
try:
    from crewai.tools import BaseTool  # Main package (works)
except ImportError:
    try:
        from crewai_tools import BaseTool  # Optional (removed)
    except ImportError:
        class BaseTool:  # Dummy fallback
            pass
```

### Custom Tool Example
```python
from crewai.tools import BaseTool

class CustomWebScrapeTool(BaseTool):
    name: str = "Web Scraper"
    description: str = "Scrapes content from websites"

    def _run(self, url: str) -> str:
        # Implementation using requests/beautifulsoup
        pass
```

## Testing Verification
- Docker build: ✅ Successful
- Application startup: ✅ Working
- CrewAI flows: ✅ Functional
- Discovery features: ✅ Operational
- Collection features: ✅ Operational

## Future Considerations

### If Tools Are Needed
1. **Option 1**: Create custom tools as needed
2. **Option 2**: Install specific tool packages directly
3. **Option 3**: Fork crewai-tools and remove embedchain dependency

### Monitoring
- Monitor for any runtime errors related to missing tools
- Track if users report missing functionality
- Consider implementing commonly needed tools

## Rollback Plan
If issues arise:
1. Can reinstall crewai-tools if embedchain conflict is resolved upstream
2. Can implement specific tools as custom implementations
3. Can use alternative packages for missing functionality

## References
- CVE-2025-3429: https://nvd.nist.gov/vuln/detail/CVE-2025-3429
- CrewAI Documentation: https://docs.crewai.com/
- Original PR: #187
