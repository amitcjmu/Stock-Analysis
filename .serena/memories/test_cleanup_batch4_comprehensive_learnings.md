# Test Cleanup Batch 4 - Comprehensive Learnings

## Insight 1: Git Merge Conflict Resolution After Security Fixes
**Problem**: Merge conflicts after applying security fixes to PR
**Solution**: Navigate to project root before staging resolved files
**Code**:
```bash
# Fix path duplication issue
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator
git status
git commit -m "Merge branch 'main' - Resolved conflicts"
git push origin feat/test-cleanup-batch4-comprehensive
```
**Usage**: When git shows "pathspec did not match" errors after conflict resolution

## Insight 2: Command Injection Security Fix Pattern
**Problem**: Using shell=True with subprocess.run() creates security vulnerabilities
**Solution**: Convert to list-based commands and Python filtering
**Code**:
```python
# VULNERABLE:
cmd = f"docker logs {container} --tail {lines} | grep '{pattern}'"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

# SECURE:
cmd = ["docker", "logs", container, "--tail", str(lines)]
result = subprocess.run(cmd, capture_output=True, text=True, check=False)
# Filter in Python instead
if pattern:
    filtered = [line for line in result.stdout.splitlines() 
                if pattern.lower() in line.lower()]
```
**Usage**: Always use list-based commands for subprocess calls

## Insight 3: Test vs Debug Script Identification Pattern
**Problem**: 80% of "test" files were actually debug scripts
**Solution**: Check for pytest/unittest imports and test class/function patterns
**Code**:
```python
def is_real_test(file_path):
    content = Path(file_path).read_text()
    return any([
        'import pytest' in content,
        'from pytest' in content,
        'import unittest' in content,
        'class Test' in content,
        'def test_' in content,
        '@pytest.mark' in content
    ])
```
**Usage**: Distinguish real tests from debug utilities during cleanup

## Insight 4: MFO Pattern Migration for Tests
**Problem**: Tests using deprecated direct Crew() instantiation
**Solution**: Update to TenantScopedAgentPool and MFO endpoints
**Code**:
```python
# OLD:
from crewai import Crew
crew = Crew(agents=[...])

# NEW:
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
from tests.fixtures.mfo_fixtures import demo_tenant_context, mock_tenant_scoped_agent_pool

@pytest.mark.mfo
async def test_function(demo_tenant_context, mock_tenant_scoped_agent_pool):
    # Use MFO endpoints
    response = await api_client.post(
        "/api/v1/master-flows/initialize",  # Not /api/v1/discovery/
        headers={"X-Client-Account-ID": demo_tenant_context.client_account_id}
    )
```
**Usage**: Modernize tests to use Master Flow Orchestrator patterns

## Insight 5: Pre-commit Compliance for Debug Scripts
**Problem**: Flake8 E402 errors when moving debug scripts
**Solution**: Add noqa comments for legitimate sys.path modifications
**Code**:
```python
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# noqa: E402 - imports after sys.path modification
from app.models import SomeModel  # noqa: E402
```
**Usage**: When debug scripts need path modifications before imports