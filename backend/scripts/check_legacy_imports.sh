#!/usr/bin/env bash
set -euo pipefail
FAILED=0

echo "🔍 Checking for legacy import patterns..."

# Check for imports from archive
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*(from|import)\s+(backend\.archive|app\.archive)" 2>/dev/null; then
  echo "❌ Import from archive detected in staged changes"
  echo "   Archive files should not be imported. Use active implementations instead."
  FAILED=1
fi

# Check for direct Crew() instantiation
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*\bCrew\s*\(" 2>/dev/null; then
  echo "❌ Direct Crew() instantiation detected. Use TenantScopedAgentPool instead."
  echo "   See ADR-015 and ADR-024 for persistent agent patterns."
  echo "   Example: await TenantScopedAgentPool.get_agent(context, agent_type, service_registry)"
  FAILED=1
fi

# Check for new crew_class usage
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*crew_class\s*=" 2>/dev/null; then
  echo "❌ crew_class assignment detected. Use child_flow_service instead."
  echo "   See ADR-025 for child flow service pattern."
  echo "   Example: child_flow_service=DiscoveryChildFlowService"
  FAILED=1
fi

# Check for imports from example agents
if git diff --cached -U0 -- '*.py' | grep -E "^\+.*from\s+docs\.examples\.agent_patterns" 2>/dev/null; then
  echo "❌ Import from docs/examples/agent_patterns detected."
  echo "   Example agents are for reference only. Use TenantScopedAgentPool in production."
  FAILED=1
fi

if [ $FAILED -eq 0 ]; then
  echo "✅ No legacy patterns detected"
fi

exit $FAILED
