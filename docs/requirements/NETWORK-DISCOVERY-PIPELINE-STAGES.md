# **Network Discovery Processing Pipeline - Stage-by-Stage Design**

## **Pipeline Overview**

This document describes the 9-stage internal data processing pipeline within AIForce-Assess that progressively reduces millions of raw network connection records down to actionable insights, with strategic ML and AI application at specific stages.

**Integration Point:** Discovery/Application Dependency Data UI in AIForce-Assess platform

**Key Principle:** AI sees only small, curated slices where human judgment adds value—not raw data.

---

## **Stage 0: Ingest → Sessionization (No AI)**

### **Goal**
Parse and normalize raw connection data without reduction.

### **Input**
- 1–10M raw connection rows from discovery tools

### **Processing**
- **ML/Logic:** None
- Fast parsing + hostname normalization
- Bound to a capture window (3-4 weeks)

### **Output Forward**
- Same rows (normalized)

### **Data Reduction**
- **0×** (no reduction)

### **AI Usage**
- None

---

## **Stage 1: Edge Aggregation (Server Level) — ML-Free, Big Cut**

### **Goal**
Collapse repeated rows into unique server edges.

### **How**
Group by `(src_host, dest_host, dest_port, protocol)` and roll up:
- `first_seen` / `last_seen`
- `conn_count_total`
- `bytes_total`
- `days_seen`

### **Output Forward**
- Aggregated server edges

### **Data Reduction**
- **Typical:** 10M → 200–500k
- **Ratio:** ≈20–50×

### **Why This Matters**
AI never sees raw rows. Everything downstream works on aggregates.

### **AI Usage**
- None

---

## **Stage 2: Business vs. Infra/Noise Classifier — ML Pass #1**

### **Goal**
Keep business traffic, down-rank noise.

### **Model**
Lightweight classifier (Logistic Regression / GBM) on engineered features:
- Ports/protocol/process tokens
- Fan-in/out degree
- Environment pairing
- Persistence (days_seen)
- Diurnal pattern (time-of-day distribution)

**Training:** Weak supervision from rules (protocol/process lists)

### **Decision Logic**

| Condition | Action |
|-----------|--------|
| P(business) ≥ τ_keep (e.g., 0.6) | **Keep** |
| P(business) ≤ τ_drop (e.g., 0.2) | **Drop** |
| Between thresholds | **Ambiguous bucket** |

### **Output Forward**
- Business + ambiguous server edges

### **Data Reduction**
- **Typical:** 200–500k → 60–120k
- **Ratio:** ≈2–4×

### **AI Usage**
- **None yet.** We keep "ambiguous" for later review, but still as aggregates.

---

## **Stage 3: Shared/Infra Service Inference — ML Pass #2 (Graphy)**

### **Goal**
Flag likely AD/DNS/SMB/Backup/EDR hubs to exclude from "business" dependencies.

### **Model**
Rule + graph features:
- Many-to-one hub patterns
- Well-known ports (389, 445, 53, etc.)
- Process name hints
- High fan-in degree

### **Decision**
Mark edges as `infra_candidate` with confidence score.

### **Output Forward**
- Business edges (minus high-confidence infra)
- Keep low-confidence infra as ambiguous

### **Data Reduction**
- **Typical:** 60–120k → 30–60k
- **Ratio:** ≈2×

### **AI Usage**
- **None.** No need yet; we're still cutting mechanically.

---

## **Stage 4: Lift to Applications (Per Environment) — Aggregation Cut**

### **Goal**
Convert server→server edges into app→app edges with evidence.

### **How**
1. Map hosts to applications (using CMDB + ML predictions)
2. Roll up per `(src_app, dest_app)`:
   - Keep top-N ports/protocols with metrics
   - Keep `server_pairs` list
   - Sum totals (bytes, connections)
   - Track persistence (days_seen)
3. Emphasize production environment

### **Output Forward**
- App-level edges (prod emphasis)

### **Data Reduction**
- **Typical:** 30–60k server edges → 2–6k app edges
- **Ratio:** ≈10×

### **AI Usage**
- **None by default.** We now have compact, scored edges.

---

## **Stage 5: Rank & Select App Edges — ML Pass #3 (Scoring)**

### **Goal**
Surface the most meaningful edges; isolate uncertain ones.

### **Model**
Scoring function (learned weights) on:
- **Volume:** bytes_total, conn_count
- **Stability:** days_seen, consistency
- **Centrality:** fan-in/out (how many apps depend on it)
- **Recency:** last_seen timestamp

**Output:**
- `composite_score` (0-100)
- `ambiguity_score` (low = confident, high = uncertain)

### **Selection for Export**

**Primary export:**
- All prod app→app edges, ranked

**For AI review:**
- Only low-margin/ambiguous edges
- Examples: bottom confidence decile, conflicting signals

### **What AI Sees (Small Slice)**

Per ambiguous app-edge, a compact card with:
- App names (source → destination)
- Top ports/protocols + stats
- Number of server-pairs
- Persistence (days_seen)
- Short evidence summary

### **Data Reduction to AI**
- **Typical:** 2–6k → 150–400 edges
- **Ratio:** ≈15–30×

### **AI Usage**
- **Limited to ambiguous cases only.**
- AI reviews context and provides reasoning for classification.

---

## **Stage 6: Server → Application Tagging — ML Pass #4 (Ranking), Targeted AI**

### **Goal**
Assign all plausible apps to each server with confidence bands.

### **Model**
Learning-to-rank / GBM over:
- Name similarity (server name vs app name patterns)
- Role/port fit (web server using 80/443)
- Communications affinity (talks mostly to app X servers)
- Environment/domain/datacenter alignment
- Persistence (stable vs transient)

**Output Bands:**
- **High (0.8–1.0):** Confident assignment
- **Medium (0.5–0.8):** Likely correct
- **Low (<0.5):** Uncertain, needs review

### **Selection for AI**

**Only hard cases:**
- Top-2 candidates within Δ≤0.05 (too close to call)
- Low band (<0.5) confidence

### **Payload to AI**

Small comparison bundle per server:
- Server name, environment, role
- Top peer apps + ports/protocols + stats
- Candidate app names with model scores
- Ask AI to pick/justify or leave both with rationales

### **Data Reduction to AI**
- **Typical:** All servers → ~5–10% of servers

### **AI Usage**
- **Targeted:** Only for tie-breakers and low-confidence cases.
- Provides human-interpretable reasoning.

---

## **Stage 7: Orphan Detection — ML Pass #5 (Time-Series/Outlier)**

### **Goal**
Find inactive/low-use servers (business or infra) that are candidates for decommissioning.

### **Model**
Threshold + outlier detector on:
- Total bytes/connections over observation period
- `days_seen` (active days)
- Idle spans (long gaps in activity)
- `% noise` vs `% business` traffic

**Output:**
- `orphan_probability` (0.0–1.0)
- Classification: definite / likely / borderline / active

### **Selection for AI**

**Only borderline cases:**
- Near thresholds (e.g., probability 0.4–0.6)
- Contradicting signals (low volume but critical ports)

### **Payload to AI**

Compact time-series summary:
- Server name, environment
- Activity timeline (days_seen distribution)
- Peer connections snippet
- Ask for keep/drop with reason code

### **Data Reduction to AI**
- **Typical:** ~5% of orphan candidates

### **AI Usage**
- **Minimal:** Only edge cases where ML is uncertain.
- Provides decommissioning recommendation rationale.

---

## **Stage 8: Cross-Environment Leakage — Rule + Tiny AI Review**

### **Goal**
Flag Dev/QA ↔ Prod edges (security/governance issues).

### **Model**
Rules-based detection with severity scoring:
- Volume (bytes transferred cross-env)
- Recency (when did it happen)
- % of total traffic (is it accidental or systematic)

### **Selection for AI**

**High-impact cases only:**
- Where app tags conflict with CMDB
- Systematic leakage (not one-off)
- Unclear root cause

### **Payload to AI**

Short case packet:
- Source app/server (environment)
- Destination app/server (environment)
- Traffic summary
- CMDB vs detected mapping conflict
- Ask for likely cause: "CMDB gap vs clone drift vs DNS mispoint"

### **Data Reduction to AI**
- **Typical:** Handfuls, not thousands

### **AI Usage**
- **Minimal:** Only for root cause analysis notes.
- Used to generate human-readable issue reports.

---

## **Pipeline Summary Table**

| Stage | Description | Input Volume | Output Volume | Reduction | ML Used | AI Used |
|-------|-------------|--------------|---------------|-----------|---------|---------|
| **0** | Ingest & Sessionization | 10M rows | 10M rows | 0× | ❌ No | ❌ No |
| **1** | Edge Aggregation | 10M rows | 200–500k | 20–50× | ❌ No | ❌ No |
| **2** | Business/Noise Classifier | 200–500k | 60–120k | 2–4× | ✅ Yes | ❌ No |
| **3** | Shared Service Inference | 60–120k | 30–60k | 2× | ✅ Yes | ❌ No |
| **4** | Lift to Applications | 30–60k | 2–6k | 10× | ❌ No | ❌ No |
| **5** | Rank & Select App Edges | 2–6k | 150–400 | 15–30× | ✅ Yes | ⚠️ Limited |
| **6** | Server → App Tagging | All servers | 5–10% | N/A | ✅ Yes | ⚠️ Targeted |
| **7** | Orphan Detection | Candidates | ~5% | N/A | ✅ Yes | ⚠️ Minimal |
| **8** | Cross-Env Leakage | Issues | Handful | N/A | ❌ No | ⚠️ Minimal |

### **Total Data Reduction**
- **Input:** 10M raw connection records
- **Output:** 2–6k app edges + targeted reports
- **Overall Reduction:** **≈2,000–5,000×**

### **AI Usage Summary**
- AI sees **< 1%** of data
- Applied only where ML is uncertain or human reasoning adds value
- Focus on explanation, not classification

---

## **Key Design Principles**

### **1. Aggressive Early Reduction**
- First 4 stages cut 10M → 2–6k without AI
- ML does heavy lifting for classification/scoring
- AI only touches curated slices

### **2. Work on Aggregates**
- Never pass raw rows to AI
- All AI inputs are pre-aggregated summaries
- Context cards include only relevant statistics

### **3. Stratified AI Application**
- **Stage 5:** Ambiguous app edges only
- **Stage 6:** Hard server-to-app assignments only
- **Stage 7:** Borderline orphan cases only
- **Stage 8:** High-impact cross-env issues only

### **4. Confidence-Based Routing**
- High-confidence ML predictions → auto-accept
- Low-confidence predictions → flag for AI
- Middle ground → accept with lower priority

### **5. Explainability**
- AI provides reasoning for all decisions
- Used for user-facing reports
- Feeds back into ML training data

---

## **Expected Performance**

### **Processing Time**
- **Stages 0-4:** < 10 minutes (10M records) - Background job
- **Stages 5-8:** < 5 minutes (ML scoring + limited AI) - Background job
- **Total:** < 15 minutes for full pipeline
- **User Experience:** Upload → Background processing → Email notification when ready for review

### **AI Token Usage**
- **Per ambiguous edge:** ~500 tokens (context + response)
- **Total edges to AI:** ~400
- **Total tokens:** ~200k (≈$0.40 at GPT-4 pricing)

### **Accuracy Targets**
- **Stage 2 (Business/Noise):** 95%+ precision
- **Stage 3 (Shared Services):** 90%+ recall
- **Stage 5 (App Edge Ranking):** 85%+ user approval
- **Stage 6 (Server Tagging):** 90%+ correct assignments

---

## **Output Files Generated**

1. **application_dependencies.json** (2–6k records)
2. **orphan_servers.json** (100–500 candidates)
3. **unmapped_servers.json** (200–800 servers)
4. **batch_job_servers.json** (50–200 servers)
5. **data_integration_servers.json** (50–150 servers)
6. **cmdb_corrections.json** (300–1000 suggestions)
7. **cross_env_issues.json** (20–100 issues)
8. **processing_metrics.json** (pipeline statistics)

---

---

## **Platform Integration**

### **User Workflow**

1. **Upload File**
   - Navigate to Discovery → Application Dependency Data
   - Upload raw CSV/JSON from discovery tool
   - Platform validates format and starts background processing

2. **Processing (Background)**
   - 9-stage pipeline executes automatically
   - User receives notification when complete
   - Processing status visible in UI

3. **Review Results**
   - View auto-detected application clusters
   - Review dependency map with criticality scores
   - Split/merge clusters as needed
   - Override scores with business context

4. **Import**
   - Approve final results
   - Import into platform database
   - Data available for assessment and planning

### **Technical Architecture**

**Frontend:**
- Use existing Discovery/Application Dependency Data UI
- Processing status indicator with progress
- Result review and refinement interface

**Backend:**
- Background job queue for pipeline execution
- ML models deployed as internal services
- AI integration via existing GenAI services
- Database storage for intermediate and final results

**Processing:**
- Async job execution (Celery/background worker)
- Checkpointing for resume on failure
- Real-time progress updates via WebSocket/polling

---

**Document Version:** 1.1  
**Last Updated:** 2025-10-22  
**Owner:** Data Science & Engineering Team  
**Status:** Technical Specification - Platform Integration Design  

---

