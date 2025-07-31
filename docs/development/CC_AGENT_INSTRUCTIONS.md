# CC Agent Instructions

## MANDATORY: Read Lessons Document First

**ALL CC subagents MUST read `docs/analysis/Notes/000-lessons.md` before beginning any work on this application.**

This document contains critical lessons learned from troubleshooting and development sessions that will help avoid common pitfalls and align with existing architecture.

## Key Requirements for CC Agents

1. **Always read the lessons document first** - Use the Read tool on `docs/analysis/Notes/000-lessons.md`
2. **Follow the established patterns** - Don't bypass the Master Flow Orchestrator (MFO)
3. **Use proper multi-tenant headers** - All API calls must include `X-Client-Account-ID` and `X-Engagement-ID`
4. **Never hardcode credentials** - Use environment variables exclusively
5. **Check database schema** - All tables are in the `migration` schema, not `public`
6. **Use atomic transactions** - For operations involving multiple state changes

## When Launching CC Subagents

Before launching any CC subagent, include this instruction in the prompt:

```
IMPORTANT: Before beginning any work, you MUST first read the lessons document at docs/analysis/Notes/000-lessons.md to understand critical architecture patterns, database schema requirements, and common pitfalls to avoid. This document contains essential guidance for working with this migration platform.
```

This ensures every CC agent starts with the proper context and follows established patterns.