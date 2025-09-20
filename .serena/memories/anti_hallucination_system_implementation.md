# Anti-Hallucination System Implementation

## Problem: Agent Hallucinations
Agents were jumping to conclusions without proper investigation, like assuming URL prefix issues when the real problem was authentication/context headers.

## Solution: 5-Step Investigation Protocol

### Core Implementation Files
```python
# backend/app/utils/agent_investigation_helpers.py
class AgentInvestigator:
    def collect_backend_logs(self, tail_lines=100, grep_pattern=None)
    def collect_frontend_logs(self, tail_lines=50)
    def form_hypothesis(description, confidence_score, evidence, test_method)
    def test_hypothesis(hypothesis, test_result)
    def determine_root_cause() -> (root_cause, ConfidenceLevel)
```

### Configuration Structure
```json
# .claude/agent_config.json v2.0.0
{
  "anti_hallucination": {
    "investigation_protocol": {
      "steps": ["investigate", "hypothesize", "verify", "confirm", "implement"],
      "minimum_evidence_sources": 3,
      "confidence_threshold": 80
    }
  }
}
```

### Agent-Specific Override
```json
"issue-triage-coordinator": {
  "require_evidence_collection": true,
  "minimum_evidence_sources": 3,
  "confidence_threshold": 80,
  "prepend_text_override": "CRITICAL: Investigate thoroughly..."
}
```

## Key Files Created
- `.claude/anti_hallucination_protocol.md` - 5-step protocol
- `.claude/ANTI_HALLUCINATION_QUICK_REFERENCE.md` - Quick commands
- `.claude/example_investigations.md` - Good vs bad examples
- `backend/app/utils/agent_investigation_helpers.py` - Python utilities

## Evidence Collection Commands
```bash
# Always run first
docker logs migration_backend --tail 100 | grep -iE "error|exception|failed"
docker logs migration_frontend --tail 50
git log --oneline -5

# Browser checks (tell user)
F12 → Console (errors?)
F12 → Network (failed requests?)
```

## Confidence Thresholds
- **90-100%**: Propose fix with evidence
- **70-89%**: Present multiple options
- **<70%**: Ask for clarification

## When to Apply
- Any issue investigation
- Bug triaging
- Performance problems
- API failures
- Agent memory issues
