# Decommission Flow User Guide

## Table of Contents
1. [Overview](#overview)
2. [When to Use Decommission Flow](#when-to-use-decommission-flow)
3. [Quick Start](#quick-start)
4. [Flow Phases](#flow-phases)
5. [System Eligibility](#system-eligibility)
6. [Decommission Strategies](#decommission-strategies)
7. [Managing Flows](#managing-flows)
8. [Metrics and Reporting](#metrics-and-reporting)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Decommission Flow is a comprehensive workflow for safely retiring legacy systems after cloud migration. It ensures data preservation, dependency management, compliance tracking, and cost savings validation before systems are decommissioned.

**Key Capabilities:**
- Automated dependency analysis to prevent service disruptions
- Data retention policy enforcement and archival management
- Cost savings estimation and tracking
- Compliance monitoring and audit trail generation
- Rollback support for safe execution

**Supported Scenarios:**
- **Pre-Migration**: Retiring systems marked as "Retire" in 6R assessment
- **Post-Migration**: Decommissioning successfully migrated systems after grace period

---

## When to Use Decommission Flow

### Pre-Migration Retirement
Use decommission flow for systems identified as "Retire" during assessment:
- Legacy systems with no cloud equivalent needed
- Redundant applications being consolidated
- End-of-life systems scheduled for retirement

### Post-Migration Decommissioning
After successful migration, use decommission flow to:
- Retire source systems no longer needed
- Archive data from legacy environments
- Shut down on-premises infrastructure
- Validate cost savings from migration

---

## Quick Start

### Step 1: Select Systems for Decommission

1. Navigate to **Asset Inventory** or **Assessment Results**
2. Filter for eligible systems:
   - Pre-migration: `6R Strategy = "Retire"`
   - Post-migration: `Migration Status = "Completed"` + grace period elapsed
3. Select 1-100 systems (recommended: start with 5-10 for first flow)

### Step 2: Initialize Decommission Flow

1. Click **"Start Decommission Flow"**
2. Provide flow details:
   - **Flow Name**: Descriptive name (e.g., "Q1 2025 Legacy System Retirement")
   - **Priority**: `cost_savings`, `risk_reduction`, or `compliance`
   - **Execution Mode**: `immediate`, `scheduled`, or `phased`
   - **Rollback**: Enable for safe execution (recommended)
3. Click **"Initialize Flow"**

### Step 3: Monitor Progress

The flow automatically progresses through three phases:
1. **Decommission Planning** (Automated)
2. **Data Migration** (May require approval)
3. **System Shutdown** (May require approval)

### Step 4: Review and Approve

- Monitor status in **Decommission Dashboard**
- Review dependency analysis and risk assessments
- Approve data archival jobs when prompted
- Approve system shutdown when ready

### Step 5: Verify Completion

- Check compliance score (target: ≥85%)
- Validate cost savings metrics
- Review decommission audit trail
- Download completion report

---

## Flow Phases

### Phase 1: Decommission Planning

**Purpose**: Analyze dependencies, assess risks, estimate savings

**Activities:**
- Dependency analysis (upstream/downstream systems)
- Risk assessment (data loss, service disruption)
- Cost estimation (savings from retirement)
- Compliance validation (retention policies, regulations)

**Duration**: 5-15 minutes (automated)

**Output:**
- Dependency map showing affected systems
- Risk score and mitigation recommendations
- Estimated annual cost savings
- Compliance checklist

**User Actions:**
- Review generated plan
- Approve or request modifications
- Pause for stakeholder review if needed

---

### Phase 2: Data Migration

**Purpose**: Preserve critical data before system shutdown

**Activities:**
- Apply data retention policies (legal, compliance)
- Execute archival jobs (databases, files, logs)
- Verify backup integrity
- Generate data preservation audit trail

**Duration**: 30 minutes - 4 hours (depends on data volume)

**Output:**
- Data archival job results
- Backup verification report
- Data retention compliance confirmation

**User Actions:**
- Approve archival job execution
- Verify backup locations
- Confirm data retention compliance

**Warning**: Do NOT skip this phase. Data cannot be recovered after shutdown.

---

### Phase 3: System Shutdown

**Purpose**: Safely decommission systems with validation

**Activities:**
- Pre-shutdown validation (dependencies, approvals)
- Graceful service shutdown
- Post-shutdown validation (no active connections)
- Resource cleanup (VMs, storage, licenses)

**Duration**: 15 minutes - 2 hours (depends on shutdown complexity)

**Output:**
- Shutdown execution log
- Resource cleanup confirmation
- Decommission completion certificate

**User Actions:**
- Approve final shutdown (irreversible)
- Monitor shutdown process
- Verify no active dependencies

**Warning**: System shutdown is IRREVERSIBLE. Ensure all data is backed up and stakeholders are notified.

---

## System Eligibility

### Pre-Migration (6R = "Retire")
Systems must meet:
- 6R Strategy marked as "Retire" in assessment
- No blocking dependencies (or dependencies approved for decommission)
- Data retention policies defined
- Stakeholder approval obtained

### Post-Migration
Systems must meet:
- Migration status = "Completed"
- Grace period elapsed (default: 30 days post-migration)
- Source system no longer in active use
- Data reconciliation passed

### Ineligible Systems
Cannot decommission if:
- Active production traffic detected
- Blocking dependencies exist
- Compliance hold applied
- Migration in progress or failed

---

## Decommission Strategies

### Priority Options

**Cost Savings** (Default)
- Focus: Maximize annual cost reduction
- Best for: Redundant systems with high operational costs
- Approach: Fast-track low-risk systems, defer complex dependencies

**Risk Reduction**
- Focus: Minimize service disruption risk
- Best for: Critical systems with many dependencies
- Approach: Extensive dependency analysis, phased rollout

**Compliance**
- Focus: Meet regulatory and audit requirements
- Best for: Systems with sensitive data or legal holds
- Approach: Strict data retention validation, comprehensive audit trails

### Execution Modes

**Immediate**
- Execute all phases without user approval
- Best for: Pre-approved systems with low risk
- Duration: 1-4 hours
- Risk: Low (if dependencies validated)

**Scheduled**
- Execute at specified date/time
- Best for: Planned maintenance windows
- Duration: Set by schedule
- Risk: Low (allows preparation)

**Phased** (Recommended)
- Pause after each phase for approval
- Best for: First-time decommissions, high-value systems
- Duration: 1-3 days (includes approval time)
- Risk: Lowest (maximum control)

### Rollback Support

**Enabled** (Recommended)
- Creates system snapshots before shutdown
- Allows reversal if issues detected
- Adds 20% to execution time
- Required for compliance-driven decommissions

**Disabled**
- No snapshots created
- Faster execution
- Use only for low-value, non-production systems

---

## Managing Flows

### Viewing Flow Status

Navigate to **Decommission Dashboard** to see:
- Active flows with current phase
- System count and progress
- Estimated savings
- Compliance score
- Warnings and approvals needed

### Pausing a Flow

To pause an active flow:
1. Click **"Pause Flow"** on dashboard
2. Flow stops at current phase
3. State preserved for later resume

**Use Cases:**
- Stakeholder review needed
- Unexpected dependency discovered
- Change freeze period
- Weekend/holiday hold

### Resuming a Flow

To resume a paused flow:
1. Click **"Resume Flow"** on dashboard
2. Optionally select specific phase to resume from
3. Provide approval notes (audit trail)
4. Flow continues from selected phase

**Options:**
- Continue from current phase (default)
- Restart from previous phase (if data changed)
- Jump to next phase (if current complete)

### Canceling a Flow

To cancel a flow:
1. Click **"Cancel Flow"** on dashboard
2. Confirm cancellation (irreversible)
3. Flow marked as failed
4. No further execution

**Warning**: Cancellation does NOT undo completed phases. If data was archived or systems shutdown, those changes persist.

---

## Metrics and Reporting

### Real-Time Metrics

**Decommission Dashboard** shows:
- **Systems Decommissioned**: Count of successfully retired systems
- **Estimated Savings**: Annual cost reduction ($)
- **Compliance Score**: % of compliance checks passed (target: ≥85%)
- **Risk Score**: Aggregated risk level (Low/Medium/High)

### Phase-Specific Metrics

**Decommission Planning:**
- Dependencies identified: Count
- Risk level: Score (0-100)
- Estimated savings: Annual $ amount

**Data Migration:**
- Data volume archived: GB
- Backup integrity: % verified
- Retention compliance: % policies met

**System Shutdown:**
- Systems shut down: Count
- Resources cleaned up: VMs, storage, licenses
- Shutdown duration: Minutes

### Exporting Reports

Available report formats:
- **PDF**: Executive summary with charts
- **Excel**: Detailed data for analysis
- **JSON**: Raw data for integration

To export:
1. Navigate to **Decommission Dashboard**
2. Select flow to export
3. Click **"Export Report"**
4. Choose format and download

---

## Best Practices

### Before Starting a Flow

1. **Validate System Eligibility**: Ensure systems meet pre/post-migration criteria
2. **Review Dependencies**: Check for blocking dependencies in advance
3. **Notify Stakeholders**: Inform affected teams of decommission plan
4. **Define Data Retention**: Set retention policies before starting
5. **Enable Rollback**: Always enable for first-time decommissions

### During Execution

1. **Monitor Actively**: Check dashboard every 30 minutes during active phases
2. **Respond to Approvals**: Don't leave flows paused longer than 24 hours
3. **Validate Backups**: Manually verify critical data archives
4. **Watch for Warnings**: Address warnings before proceeding to next phase
5. **Document Decisions**: Add approval notes for audit trail

### After Completion

1. **Verify Cost Savings**: Confirm expected savings in billing
2. **Archive Reports**: Download and store completion reports
3. **Update CMDB**: Mark systems as decommissioned
4. **Review Metrics**: Analyze what went well/poorly for next flow
5. **Notify Teams**: Inform stakeholders of completion

### Avoiding Common Mistakes

❌ **Don't**: Skip data migration phase to save time
✅ **Do**: Always archive data before shutdown

❌ **Don't**: Decommission systems with active dependencies
✅ **Do**: Validate dependency analysis before proceeding

❌ **Don't**: Ignore compliance warnings
✅ **Do**: Resolve all compliance issues before shutdown

❌ **Don't**: Batch too many systems (>50) in first flow
✅ **Do**: Start with 5-10 systems to learn the process

❌ **Don't**: Disable rollback for production systems
✅ **Do**: Keep rollback enabled until confident in process

---

## Troubleshooting

### Flow Stuck in "Decommission Planning"

**Symptoms**: Flow stays in planning phase for >30 minutes

**Causes**:
- Complex dependency graph taking time to analyze
- Agent execution paused/failed
- Database connection timeout

**Solutions**:
1. Check browser console for API errors
2. Refresh status page (may be UI polling issue)
3. Pause and resume flow to restart agent
4. Contact support if stuck >1 hour

---

### "Blocking Dependencies Detected" Error

**Symptoms**: Flow paused with dependency warning

**Causes**:
- System has active upstream/downstream dependencies
- Dependency not approved for decommission
- Circular dependency detected

**Solutions**:
1. Review dependency map in planning phase output
2. Add dependent systems to decommission flow OR
3. Update dependency configuration to remove link OR
4. Get stakeholder approval to proceed with warning

---

### Data Archival Job Failed

**Symptoms**: Data migration phase fails with archival error

**Causes**:
- Insufficient storage space
- Database connection timeout
- Retention policy conflict

**Solutions**:
1. Check archival job logs in flow details
2. Verify storage quota available
3. Retry archival job from flow controls
4. Adjust retention policy if conflicts found
5. Contact support if persists after 3 retries

---

### System Shutdown Failed

**Symptoms**: System shutdown phase reports failure

**Causes**:
- Active connections still present
- Graceful shutdown timeout
- Resource cleanup error

**Solutions**:
1. Review shutdown logs in flow details
2. Verify no active users/processes on system
3. Wait 15 minutes for connections to drain
4. Retry shutdown from flow controls
5. Use force shutdown option if safe to proceed

---

### Compliance Score Below 85%

**Symptoms**: Flow shows compliance warning

**Causes**:
- Missing data retention policies
- Incomplete audit trail
- Regulatory checks failed

**Solutions**:
1. Review compliance checklist in planning phase
2. Define missing retention policies
3. Ensure all approvals documented
4. Re-run compliance validation
5. Defer shutdown until score ≥85%

---

### Flow Canceled Accidentally

**Symptoms**: Flow marked as "failed" after cancel

**Recovery**:
1. **Cannot** undo cancellation
2. Check what phases completed before cancel
3. If data archived: Data is safe, shutdown did not occur
4. If shutdown started: System may be partially down
5. Create new flow for remaining systems
6. Contact support for state recovery assistance

---

## Getting Help

### In-App Support
- Click **"Help"** icon in Decommission Dashboard
- View contextual help for current phase
- Access troubleshooting guides

### Documentation
- API Reference: `/backend/docs/api/DECOMMISSION_FLOW_API.md`
- Architecture Docs: `/docs/planning/DECOMMISSION_FLOW_SOLUTION.md`
- ADR-006: Master Flow Orchestrator pattern

### Contact Support
- **Email**: support@example.com
- **Slack**: #decommission-flow-help
- **Include**: Flow ID, error messages, screenshots

---

**Document Version**: 1.0
**Last Updated**: November 5, 2025
**Related Features**: Assessment Flow, 6R Strategy, Asset Inventory
**Stability**: Beta (Issues #950-951)
