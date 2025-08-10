### ADR 017: Redis-backed Failure Journal (DLQ) with PostgreSQL Write-through

Status: Accepted

Context
- Collection write-backs and readiness validation are best-effort operations that must not break user flows.
- We need durable auditability and fast retries for transient errors, without blocking API responses.

Decision
- Implement a hybrid failure journal:
  - PostgreSQL: canonical failure_journal table for durability and reporting
  - Redis: DLQ for fast, non-blocking retries with backoff

Architecture
- Write-through on failure paths:
  1) Persist minimal failure event in Postgres (failure_journal)
  2) Enqueue the same event to Redis (fj:queue:{client}:{engagement}) and store payload at fj:payload:{failure_id}
  3) A background worker drains the queue and retries; on failure schedules backoff in fj:retry:{client}:{engagement} (ZSET)
  4) On success, ACK: delete fj:payload and Postgres row or mark resolved

Redis keys
- fj:queue:{client}:{engagement} (LIST): RPUSH failure_id
- fj:payload:{failure_id} (JSON): failure payload with retry_count
- fj:retry:{client}:{engagement} (ZSET): member=failure_id, score=retry_at_epoch
- fj:metrics:* (HASH/COUNTERS): optional operational metrics

API additions
- backend/app/services/caching/redis_cache.py: enqueue_failure, schedule_retry, claim_due, ack_failure
- backend/app/services/integration/failure_journal.py: log_failure(db, ...)

Worker behavior (phase 1)
- Periodically:
  - LPOP from fj:queue; process; on failure schedule backoff
  - Claim due from fj:retry (ZRANGEBYSCORE .. now), process; reschedule on failure with capped exponential backoff

Rationale
- Redis provides low-latency queuing compatible with Upstash/serverless constraints.
- Postgres preserves a complete audit trail and supports analytics, dashboards, and manual interventions.

Consequences
- Additional background task required (can run in the same container under an async loop initially)
- Failure payloads must be sanitized (no secrets/PII)
- Multi-tenant isolation enforced by key names and DB scoping

Security & multi-tenancy
- Keys are partitioned by client_account_id and engagement_id
- Payloads in fj:payload are JSON; avoid embedding credentials; TTL default 7 days

Alternatives considered
- Postgres-only DLQ: simpler, but slower retries and more load
- Redis-only DLQ: fast, but lacks durability and auditability


