# Investigation Report Format

## Standard Format for Issue Investigation

### Template Structure
```markdown
## Investigation Results

### Evidence Collected:
- ✅ Backend logs: [Summary]
- ✅ Browser console: [Summary]
- ✅ Network requests: [Summary]
- ✅ Code reviewed: [Files examined]

### Hypotheses Tested:
1. **[Most likely]** (Confidence: 95%)
   - Evidence: [Specific citations with file:line]
   - Verification: [How tested]
   - Result: [Confirmed/Rejected]

2. **[Alternative]** (Confidence: 40%)
   - Evidence: [Citations]
   - Result: [Rejected because...]

### Root Cause:
[Clear statement with evidence]

### Proposed Solution:
[Specific fix with code]

Would you like me to proceed?
```

## Evidence Citation Format
```markdown
BAD:  "Authentication error"
GOOD: "Authentication error (backend/auth.py:45, log line 234)"

BAD:  "Missing headers"
GOOD: "Missing X-Client-Account-Id header (Network tab, request #3)"
```

## When Uncertain Template
```markdown
"I need more information to diagnose this properly.

What I've checked:
- ✅ Backend logs: [summary]
- ❓ Browser console: [need user to check]

Could you please:
1. Check browser console (F12)
2. Tell me exact reproduction steps
3. Share recent changes

This will help identify the root cause."
```

## Usage
- All issue investigations
- Bug reports
- Performance analysis
- User-reported problems
