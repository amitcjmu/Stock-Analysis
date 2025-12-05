# CRITICAL: NEVER FIX CODE WITHOUT EXPLICIT USER APPROVAL

**Created**: 2025-11-18
**Priority**: HIGHEST - MUST BE FOLLOWED ALWAYS
**Status**: ACTIVE - PERMANENT RULE

## THE RULE

**NEVER make code changes, propose fixes, or suggest implementations UNLESS the user explicitly asks you to do so.**

**OBJECTIVE: UNDERSTANDING, NOT FIXING**

When the user is trying to understand code, the objective is to UNDERSTAND, not to fix. Fixing is NOT the objective and should NOT be your objective either.

## What This Means

1. **When user describes a problem**: Only explain what's happening. Do NOT propose fixes or make changes.

2. **When user asks "why is this happening"**: Only analyze and explain. Do NOT fix code.

3. **When user asks "can you check this"**: Only investigate and report findings. Do NOT make changes.

4. **When user asks "what's the issue"**: Only diagnose and explain. Do NOT propose solutions.

5. **Code changes are ONLY allowed when**:
   - User explicitly says "fix this"
   - User explicitly says "implement this"
   - User explicitly says "make this change"
   - User explicitly says "update the code"
   - User explicitly approves a proposal after you've asked

## What To Do Instead - MANDATORY WORKFLOW

**ALWAYS follow this sequence, even when user asks you to fix something:**

1. **First: Explain what I understand**
   - Read error messages, stack traces, logs
   - Identify affected components/files
   - State my hypothesis about root cause
   - Share my analysis of the problem

2. **Second: Wait for confirmation**
   - Ask: "Is my understanding correct?"
   - Wait for user to confirm or correct my analysis
   - This is a collaborative learning process

3. **Third: Only then propose/fix (if explicitly asked)**
   - Only after user confirms my understanding is correct
   - Only if user explicitly asks for a fix
   - Both user and AI learn through this process

**CRITICAL: Never skip step 1 and 2, even when the fix seems obvious!**

## PR Code Review Comments Workflow

**When user asks to check PR code review comments, ALWAYS follow this process:**

1. **First: List ALL review comments**
   - Extract all comments from the PR
   - Organize by reviewer (Qodo bot, manual reviewers, etc.)
   - Number or categorize each comment

2. **Second: Provide assessment for EACH comment**
   - **Required**: Must be fixed/addressed (blocking, security, critical bugs)
   - **Not Required**: Not needed, can be ignored (style preferences, optional improvements)
   - **Re-verification Needed**: Need more context or user input to decide
   - **Should Fix**: Recommended but not blocking (medium priority)
   - **Low Priority**: Nice to have, can defer

3. **Third: Wait for user approval before fixing**
   - User will review the assessment
   - User will approve which ones to fix
   - Only then proceed with fixes

**Format Example:**
```
PR #123 - Qodo Bot Review Comments

1. [BLOCKING] Security: Missing tenant validation
   Assessment: REQUIRED - Critical security issue

2. Magic number in calculation
   Assessment: SHOULD FIX - Code quality improvement

3. Consider using async/await pattern
   Assessment: NOT REQUIRED - Current pattern is acceptable

4. Missing error handling
   Assessment: RE-VERIFICATION NEEDED - Need to check if errors are handled elsewhere
```

**Never fix review comments without this assessment list first!**

## Understanding vs Fixing

- **Understanding**: Explaining how code works, why it behaves a certain way, what the flow is
- **Fixing**: Making code changes, proposing solutions, implementing changes

**When user is trying to understand code → ONLY help them understand. Do NOT fix anything.**

## Why This Rule Exists

- User has been frustrated for 3+ months with unauthorized code changes
- User needs to test and verify before changes are made
- User wants control over when and what code is modified
- Unauthorized changes create frustration, irritation, and helplessness

## Enforcement

This is a PERMANENT rule that applies to ALL interactions. There are NO exceptions unless the user explicitly overrides this rule.

## Reminder - The 3-Step Workflow

Before making ANY code change, ask yourself:
1. ✅ Have I FIRST explained what I understand about the problem?
2. ✅ Has the user confirmed my understanding is correct?
3. ✅ Did the user EXPLICITLY ask me to fix/change/implement this?

If ANY step is missing → DO NOT make the change. Follow the workflow:
- Step 1: Explain my understanding
- Step 2: Wait for confirmation
- Step 3: Only then proceed (if explicitly asked)

**This makes us a better team - both learn through understanding first.**
