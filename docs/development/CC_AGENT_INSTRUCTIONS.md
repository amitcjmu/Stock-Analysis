# CC Agent Instructions

## MANDATORY: Read Required Documents First

**ALL CC subagents MUST read these documents before beginning any work on this application:**

1. **`docs/development/CODING_AGENT_KNOWLEDGE_SUMMARY.md`** ⚠️ **CRITICAL - READ FIRST**
   - Comprehensive distillation of 300+ Serena memories into actionable patterns
   - Contains top 10 critical patterns that prevent recurring bugs
   - Critical architecture patterns, common bug fixes, and development workflows

2. **`docs/analysis/Notes/000-lessons.md`**
   - Critical lessons learned from troubleshooting and development sessions
   - Helps avoid common pitfalls and align with existing architecture

These documents contain essential guidance for working with this migration platform and will help avoid common pitfalls and align with existing architecture.

## Key Requirements for CC Agents

1. **Always read the required documents first** - Use the Read tool on:
   - `docs/development/CODING_AGENT_KNOWLEDGE_SUMMARY.md` (READ FIRST - contains critical patterns)
   - `docs/analysis/Notes/000-lessons.md` (architecture patterns and pitfalls)
2. **Follow the established patterns** - Don't bypass the Master Flow Orchestrator (MFO)
3. **Use proper multi-tenant headers** - All API calls must include `X-Client-Account-ID` and `X-Engagement-ID`
4. **Never hardcode credentials** - Use environment variables exclusively
5. **Check database schema** - All tables are in the `migration` schema, not `public`
6. **Use atomic transactions** - For operations involving multiple state changes

## When Launching CC Subagents

Before launching any CC subagent, include this instruction in the prompt:

```
IMPORTANT: Before beginning any work, you MUST first read these documents in order:
1. docs/development/CODING_AGENT_KNOWLEDGE_SUMMARY.md - Critical patterns from 300+ development sessions (READ FIRST)
2. docs/analysis/Notes/000-lessons.md - Architecture patterns and common pitfalls

These documents contain essential guidance for working with this migration platform, including critical architecture patterns, database schema requirements, common bug patterns, and development workflows that must be followed.
```

This ensures every CC agent starts with the proper context and follows established patterns.