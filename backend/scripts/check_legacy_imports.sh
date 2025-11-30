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

# Check for direct Crew() instantiation (filter out comments, docstrings, and approved exceptions)
# Exceptions:
#   - decommission agent pool: domain-specific requirements (see crew_factory.py docstring)
#   - wave planning service: uses persistent agents from TenantScopedAgentPool (ADR-015 compliant)
# Process file by file to respect exemptions
CREW_VIOLATIONS=""
for file in $(git diff --cached --name-only -- '*.py'); do
  # Skip decommission agent pool files (architecturally justified)
  if echo "$file" | grep -q "app/services/agents/decommission/agent_pool"; then
    continue
  fi

  # Skip wave planning service (uses TenantScopedAgentPool for persistent agents, ADR-015 compliant)
  if echo "$file" | grep -q "app/services/planning/wave_planning_service"; then
    continue
  fi

  # Check for Crew() instantiation in this file
  VIOLATIONS=$(git diff --cached -U0 -- "$file" | \
    grep -v -E "^\+\s*#" | \
    grep -E "^\+.*\bCrew\s*\(" 2>/dev/null || true)

  if [ -n "$VIOLATIONS" ]; then
    CREW_VIOLATIONS="$CREW_VIOLATIONS
File: $file
$VIOLATIONS
"
  fi
done

if [ -n "$CREW_VIOLATIONS" ]; then
  echo "❌ Direct Crew() instantiation detected. Use TenantScopedAgentPool instead."
  echo "   See ADR-015 and ADR-024 for persistent agent patterns."
  echo "   Example: await TenantScopedAgentPool.get_agent(context, agent_type, service_registry)"
  echo ""
  echo "   Note: Decommission agent pool is exempt due to domain-specific requirements."
  echo ""
  echo "Violations:"
  echo "$CREW_VIOLATIONS"
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
