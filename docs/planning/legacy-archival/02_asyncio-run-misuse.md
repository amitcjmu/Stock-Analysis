# `asyncio.run()` Misuse in Application Code

## Context
Per platform rules, never use `asyncio.run()` inside async contexts or application services. It is acceptable in standalone scripts/tests.

## Findings (Application Layer)
- `backend/app/services/tools/base_tool.py`: `AsyncBaseDiscoveryTool.run` wraps async `arun` with `asyncio.run()`.
- `backend/app/services/agents/intelligent_flow_agent/tools/status_tool.py`: sync → async bridging uses thread executor with `asyncio.run()`.
- `backend/app/services/crewai_flows/tools/asset_creation_tool_legacy.py`: legacy tool calls `asyncio.run()` in thread executor.

## Risks
- Event loop conflicts in FastAPI workers.
- Database session misuse when mixing sync wrappers with async `AsyncSessionLocal`.

## Migration Guidance
- Prefer pure async call chains: expose `async` APIs and `await` them at call sites.
- For sync-only entry points (e.g., CrewAI BaseTool), use `anyio.from_thread.run` or `asyncio.get_running_loop().create_task` and await upstream; avoid `asyncio.run()`.
- Keep `asyncio.run()` in `scripts/`, `tests/`, `seeding/` only.

## Action Items
- Replace `asyncio.run()` wrappers in the three files above with safe async patterns.
- Add lint/CI rule to block `asyncio.run(` in `backend/app/**` (allowlist `scripts/`, `tests/`, `seeding/`).
- If `AsyncBaseDiscoveryTool` and `asset_creation_tool_legacy` are unused, remove instead of refactoring.


