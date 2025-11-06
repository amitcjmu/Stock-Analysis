# Decommission Flow - Phase 3: System Shutdown

**Last Updated:** 2025-11-06
**Phase Name**: `system_shutdown` (per ADR-027 FlowTypeConfig)
**Estimated Duration**: 60 minutes
**⚠️ CRITICAL**: This phase is IRREVERSIBLE - rollback not available after execution begins

> **⚠️ IMPLEMENTATION STATUS**: This phase is **NOT FULLY IMPLEMENTED**. Core database models exist for execution logs and validation checks. Basic API endpoints for phase initiation are present. However, **CRITICAL safety features are NOT implemented**: pre-execution validation gates, automated safety checks, rollback mechanisms, and infrastructure cleanup automation are all **PLANNED but not yet coded**. **DO NOT ATTEMPT TO USE THIS IN PRODUCTION** until all safety features are complete. See [Milestone #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952) for status.
>
> **⚠️ HUMAN-IN-THE-LOOP WORKFLOW**: This phase is the MOST CRITICAL and requires extensive user coordination. The current implementation provides database structure and API endpoints, but does NOT include:
> - User input forms for manual data entry
> - Approval workflow UI
> - Artifact upload/storage
> - Progress tracking UI
>
> See [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md) for required additions.

## 📋 Phase Overview

The System Shutdown phase performs the final decommission execution with pre-validation, graceful service shutdown, post-validation, and complete cleanup. This is the **point of no return** in the decommission process.

**Phase Objectives:**
1. Execute pre-shutdown validation checks
2. Perform graceful service shutdown
3. Remove infrastructure resources
4. Execute post-shutdown validation
5. Clean up access controls and monitoring
6. Generate final audit trail
7. Mark flow as completed

**Phase Output:**
- Shutdown execution log with timestamps
- Validation check results (pre and post)
- Infrastructure cleanup confirmation
- Final audit report
- Cost savings achieved

## 👤 Manual Input Requirements

This phase is the MOST CRITICAL and requires extensive user coordination:

### User Must Provide:
1. **Pre-Execution Checklist**: Manual verification of all safety checks
2. **Execution Coordination**: Work with infrastructure teams for shutdown
3. **Progress Updates**: Real-time updates as shutdown progresses
4. **Issue Reporting**: Document any problems encountered
5. **Post-Execution Verification**: Confirm systems are fully shut down
6. **Stakeholder Approvals**:
   - **FINAL APPROVAL**: Management/executive sign-off (IRREVERSIBLE)
   - Infrastructure team readiness confirmation
   - Application team sign-off (testing complete)

### Artifacts to Collect:
- Pre-execution checklist (completed)
- Shutdown execution logs (from infrastructure team)
- Post-shutdown verification reports
- Issue/incident reports (if any)
- Final sign-off documents
- Compliance attestation (audit trail)

### Current Implementation Status:
- ⚠️ **CRITICAL**: This phase is NOT production-ready
- ❌ Pre-execution validation UI NOT implemented
- ❌ Real-time progress tracking NOT implemented
- ❌ Issue reporting workflow NOT implemented
- ❌ Post-execution verification UI NOT implemented
- ❌ Artifact collection for audit trail NOT implemented
- ❌ Final approval workflow NOT implemented

**DO NOT USE THIS PHASE IN PRODUCTION UNTIL THESE FEATURES ARE COMPLETE**

## 🏗️ Architecture

### Agent-Based Execution

```python
# backend/app/services/child_flow_services/decommission.py
async def _execute_system_shutdown(
    self,
    child_flow,
    phase_input: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute system shutdown phase using TenantScopedAgentPool.

    Agents Used (PLANNED - Critical safety features not yet implemented):
    1. Shutdown Coordinator (PLANNED): Orchestrates shutdown sequence
    2. Validation Specialist (PLANNED): Pre and post-shutdown validation
    3. Cleanup Specialist (PLANNED): Infrastructure and access cleanup
    4. Audit Logger (STUB): Creates comprehensive audit trail

    ⚠️ CRITICAL: This phase is IRREVERSIBLE.
    Per ADR-025: Uses DecommissionAgentPool (NOT per-call Crew instantiation)
    """
    # Update phase status to running
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="system_shutdown",
        phase_status="running"
    )

    # Record shutdown start time
    await self.repository.update(
        flow_id=child_flow.flow_id,
        system_shutdown_started_at=datetime.utcnow()
    )

    # Get agent pool (persistent, tenant-scoped)
    agent_pool = TenantScopedAgentPool(
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id
    )

    # Execute system shutdown crew
    shutdown_crew = agent_pool.get_system_shutdown_crew()
    result = await shutdown_crew.execute(
        flow_id=child_flow.flow_id,
        system_ids=child_flow.selected_system_ids,
        decommission_plans=await self._get_decommission_plans(child_flow.flow_id)
    )

    # Store results in database
    await self._store_shutdown_results(child_flow, result)

    # Update phase status to completed
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="system_shutdown",
        phase_status="completed"
    )

    # Update flow status to completed
    await self.repository.update_status(
        flow_id=child_flow.flow_id,
        status="completed",
        current_phase="completed"
    )

    # Record shutdown completion time
    await self.repository.update(
        flow_id=child_flow.flow_id,
        system_shutdown_completed_at=datetime.utcnow()
    )

    return {
        "status": "success",
        "phase": "system_shutdown",
        "next_phase": "completed",
        "systems_decommissioned": len(child_flow.selected_system_ids),
        "validation_checks_passed": result.validation_checks_passed,
        "actual_annual_savings": result.actual_annual_savings
    }
```

### CrewAI Agent Configuration

**Shutdown Coordinator Agent**:
```python
{
    "role": "Shutdown Coordinator",
    "goal": "Execute safe, sequenced system shutdown with zero data loss",
    "backstory": "Infrastructure architect with 15 years experience in system decommissioning",
    "tools": [
        "stop_services",
        "drain_load_balancers",
        "disconnect_databases",
        "power_down_instances"
    ],
    "memory": False,  # Per ADR-024
    "verbose": False
}
```

**Validation Specialist Agent**:
```python
{
    "role": "Validation Specialist",
    "goal": "Verify system is safe to shutdown and confirm successful decommission",
    "backstory": "Quality assurance expert specializing in decommission validation",
    "tools": [
        "check_active_connections",
        "verify_data_archived",
        "test_service_unavailability",
        "validate_cleanup_complete"
    ],
    "memory": False,
    "verbose": False
}
```

**Cleanup Specialist Agent**:
```python
{
    "role": "Cleanup Specialist",
    "goal": "Remove all infrastructure resources and access controls",
    "backstory": "Cloud infrastructure specialist focused on resource optimization",
    "tools": [
        "delete_instances",
        "remove_load_balancers",
        "delete_storage",
        "revoke_access_credentials",
        "remove_monitoring_alerts"
    ],
    "memory": False,
    "verbose": False
}
```

**Audit Logger Agent**:
```python
{
    "role": "Audit Logger",
    "goal": "Create comprehensive audit trail for compliance",
    "backstory": "Compliance auditor specializing in infrastructure changes",
    "tools": [
        "log_shutdown_event",
        "capture_final_state",
        "generate_audit_report",
        "store_compliance_attestation"
    ],
    "memory": False,
    "verbose": False
}
```

## 🔄 Shutdown Sequence

### 1. Pre-Validation Checks

**CRITICAL**: All checks must pass before shutdown proceeds.

```python
pre_validation_checks = [
    {
        "check_name": "Data Archive Verification",
        "category": "Data Protection",
        "is_critical": True,
        "validation_logic": verify_all_archive_jobs_completed,
        "description": "Verify all data has been archived successfully"
    },
    {
        "check_name": "Dependency Clearance",
        "category": "System Dependencies",
        "is_critical": True,
        "validation_logic": verify_no_active_dependencies,
        "description": "Ensure no active systems depend on this system"
    },
    {
        "check_name": "Active Connection Check",
        "category": "System Activity",
        "is_critical": True,
        "validation_logic": verify_no_active_connections,
        "description": "Confirm no active user connections or transactions"
    },
    {
        "check_name": "Approval Verification",
        "category": "Governance",
        "is_critical": True,
        "validation_logic": verify_all_approvals_received,
        "description": "Confirm all stakeholder approvals received"
    },
    {
        "check_name": "Backup Verification",
        "category": "Data Protection",
        "is_critical": False,  # Non-blocking warning
        "validation_logic": verify_recent_backup_exists,
        "description": "Verify recent backup exists (last 24 hours)"
    }
]

# Execute validation checks
validation_results = []
for check in pre_validation_checks:
    result = await check["validation_logic"](system_id)

    validation_results.append({
        "check_name": check["check_name"],
        "status": "passed" if result.passed else "failed",
        "is_critical": check["is_critical"],
        "result_details": result.details,
        "issues_found": result.issues_count
    })

    # Store in database
    validation_check = DecommissionValidationCheck(
        flow_id=flow_id,
        system_id=system_id,
        validation_category=check["category"],
        check_name=check["check_name"],
        check_description=check["description"],
        is_critical=check["is_critical"],
        status="passed" if result.passed else "failed",
        result_details=result.details,
        issues_found=result.issues_count,
        validated_by="system",
        validated_at=datetime.utcnow()
    )
    db.add(validation_check)

# Fail if any critical check failed
critical_failures = [r for r in validation_results if r["is_critical"] and r["status"] == "failed"]
if critical_failures:
    raise PreValidationError(
        f"Cannot proceed with shutdown. {len(critical_failures)} critical validation checks failed.",
        failed_checks=critical_failures
    )
```

### 2. Graceful Service Shutdown

**Ordered Shutdown Sequence**:

```python
shutdown_sequence = [
    {
        "step": 1,
        "action": "Drain Load Balancers",
        "description": "Remove instances from load balancer pools",
        "timeout_seconds": 300,
        "handler": drain_load_balancers
    },
    {
        "step": 2,
        "action": "Stop New Connections",
        "description": "Disable new connection acceptance",
        "timeout_seconds": 60,
        "handler": stop_new_connections
    },
    {
        "step": 3,
        "action": "Wait for Connection Drain",
        "description": "Allow active connections to complete (max 10 minutes)",
        "timeout_seconds": 600,
        "handler": wait_for_connection_drain
    },
    {
        "step": 4,
        "action": "Stop Application Services",
        "description": "Gracefully stop application processes",
        "timeout_seconds": 300,
        "handler": stop_application_services
    },
    {
        "step": 5,
        "action": "Disconnect Database",
        "description": "Close database connections",
        "timeout_seconds": 120,
        "handler": disconnect_database
    },
    {
        "step": 6,
        "action": "Stop Background Jobs",
        "description": "Stop scheduled tasks and background workers",
        "timeout_seconds": 180,
        "handler": stop_background_jobs
    },
    {
        "step": 7,
        "action": "Power Down Instances",
        "description": "Shutdown compute instances",
        "timeout_seconds": 300,
        "handler": power_down_instances
    }
]

# Execute shutdown sequence
execution_log = []
for step in shutdown_sequence:
    logger.info(f"Step {step['step']}: {step['action']}")

    try:
        step_result = await step["handler"](
            system_id=system_id,
            timeout=step["timeout_seconds"]
        )

        execution_log.append({
            "step": step["step"],
            "action": step["action"],
            "status": "success",
            "started_at": step_result.started_at,
            "completed_at": step_result.completed_at,
            "duration_seconds": step_result.duration_seconds
        })

    except TimeoutError as e:
        # Force shutdown after timeout
        logger.warning(f"Step {step['step']} timed out, forcing shutdown")

        force_result = await force_shutdown(system_id, step["action"])

        execution_log.append({
            "step": step["step"],
            "action": step["action"],
            "status": "forced",
            "error": "Timeout - forced shutdown",
            "duration_seconds": step["timeout_seconds"]
        })

    except Exception as e:
        logger.error(f"Step {step['step']} failed: {e}", exc_info=True)

        execution_log.append({
            "step": step["step"],
            "action": step["action"],
            "status": "failed",
            "error": str(e)
        })

        # Decide whether to continue or abort
        if step.get("critical", True):
            raise ShutdownExecutionError(
                f"Critical shutdown step failed: {step['action']}",
                execution_log=execution_log
            )
```

### 3. Infrastructure Cleanup

```python
cleanup_tasks = [
    {
        "task": "Delete Compute Instances",
        "handler": delete_compute_instances,
        "resource_type": "EC2/VM",
        "cost_impact_monthly": compute_cost
    },
    {
        "task": "Remove Load Balancers",
        "handler": delete_load_balancers,
        "resource_type": "LoadBalancer",
        "cost_impact_monthly": lb_cost
    },
    {
        "task": "Delete Storage Volumes",
        "handler": delete_storage_volumes,
        "resource_type": "EBS/Disk",
        "cost_impact_monthly": storage_cost
    },
    {
        "task": "Remove Network Configuration",
        "handler": delete_network_config,
        "resource_type": "VPC/Subnet/SecurityGroup",
        "cost_impact_monthly": 0  # No cost for config
    },
    {
        "task": "Revoke Access Credentials",
        "handler": revoke_access_credentials,
        "resource_type": "IAM/ServiceAccount",
        "cost_impact_monthly": 0
    },
    {
        "task": "Remove Monitoring Alerts",
        "handler": delete_monitoring_alerts,
        "resource_type": "CloudWatch/Alert",
        "cost_impact_monthly": monitoring_cost
    },
    {
        "task": "Delete DNS Records",
        "handler": delete_dns_records,
        "resource_type": "Route53/DNS",
        "cost_impact_monthly": dns_cost
    }
]

# Execute cleanup tasks
cleanup_results = []
total_monthly_savings = 0

for task in cleanup_tasks:
    logger.info(f"Cleanup: {task['task']}")

    try:
        result = await task["handler"](system_id)

        cleanup_results.append({
            "task": task["task"],
            "resource_type": task["resource_type"],
            "status": "success",
            "resources_deleted": result.resources_deleted,
            "monthly_savings": task["cost_impact_monthly"]
        })

        total_monthly_savings += task["cost_impact_monthly"]

    except Exception as e:
        logger.error(f"Cleanup task failed: {task['task']}: {e}")

        cleanup_results.append({
            "task": task["task"],
            "resource_type": task["resource_type"],
            "status": "failed",
            "error": str(e)
        })
```

### 4. Post-Validation Checks

```python
post_validation_checks = [
    {
        "check_name": "Service Unavailability",
        "category": "Shutdown Verification",
        "validation_logic": verify_service_unavailable,
        "description": "Confirm service is no longer accessible"
    },
    {
        "check_name": "Resource Deletion",
        "category": "Cleanup Verification",
        "validation_logic": verify_resources_deleted,
        "description": "Verify all infrastructure resources deleted"
    },
    {
        "check_name": "Access Revocation",
        "category": "Security",
        "validation_logic": verify_access_revoked,
        "description": "Confirm all access credentials revoked"
    },
    {
        "check_name": "Monitoring Removal",
        "category": "Operations",
        "validation_logic": verify_monitoring_removed,
        "description": "Verify monitoring alerts and dashboards removed"
    },
    {
        "check_name": "Audit Trail Completeness",
        "category": "Compliance",
        "validation_logic": verify_audit_trail_complete,
        "description": "Confirm complete audit trail generated"
    }
]

# Execute post-validation
post_validation_results = []
for check in post_validation_checks:
    result = await check["validation_logic"](system_id)

    post_validation_results.append({
        "check_name": check["check_name"],
        "status": "passed" if result.passed else "warning",
        "result_details": result.details
    })
```

## 📊 Execution Logs

### Decommission Execution Log

```python
# backend/app/models/decommission_flow/audit_models.py
class DecommissionExecutionLog(Base):
    __tablename__ = "decommission_execution_logs"
    __table_args__ = {"schema": "migration"}

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), ForeignKey("migration.decommission_flows.flow_id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("migration.decommission_plans.plan_id"), nullable=False)
    system_id = Column(UUID(as_uuid=True), ForeignKey("migration.assets.id"), nullable=False)

    # Execution details
    execution_phase = Column(String(100), nullable=False)  # pre_validation, shutdown, cleanup, post_validation
    status = Column(String(50), nullable=False)  # success, failed, forced

    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    executed_by = Column(String(255))  # User or "system"

    # Safety checks
    safety_checks_passed = Column(JSONB, nullable=False, default=[])
    safety_checks_failed = Column(JSONB, nullable=False, default=[])
    rollback_available = Column(Boolean, default=False)  # False for system_shutdown phase

    # Detailed logging
    execution_log = Column(JSONB, nullable=False, default=[])  # Ordered list of actions
    error_details = Column(Text)
```

### Example Execution Log Entry

```json
{
  "log_id": "uuid",
  "flow_id": "decommission-flow-uuid",
  "plan_id": "plan-uuid",
  "system_id": "asset-uuid",
  "execution_phase": "shutdown",
  "status": "success",
  "started_at": "2025-11-06T10:00:00Z",
  "completed_at": "2025-11-06T10:15:00Z",
  "executed_by": "system",
  "safety_checks_passed": [
    "data_archived",
    "no_active_connections",
    "approvals_received"
  ],
  "safety_checks_failed": [],
  "rollback_available": false,
  "execution_log": [
    {
      "step": 1,
      "action": "Drain Load Balancers",
      "status": "success",
      "started_at": "2025-11-06T10:00:00Z",
      "completed_at": "2025-11-06T10:02:00Z",
      "duration_seconds": 120
    },
    {
      "step": 2,
      "action": "Stop New Connections",
      "status": "success",
      "started_at": "2025-11-06T10:02:00Z",
      "completed_at": "2025-11-06T10:02:30Z",
      "duration_seconds": 30
    }
    // ... more steps
  ]
}
```

## 🎨 Frontend UI

### System Shutdown Execution Page

**URL**: `/decommission/flow/{flow_id}/shutdown`

```typescript
<SystemShutdownView>
  <WarningBanner>
    ⚠️ CRITICAL: System shutdown is IRREVERSIBLE. Rollback is not available after execution begins.
    <ConfirmCheckbox>
      I understand this action cannot be undone
    </ConfirmCheckbox>
  </WarningBanner>

  <PreValidationSection>
    <SectionTitle>Pre-Shutdown Validation</SectionTitle>
    <ValidationChecksList>
      {pre_validation_checks.map(check => (
        <ValidationCheckCard key={check.check_name}>
          <CheckName>{check.check_name}</CheckName>
          <CheckStatus status={check.status}>
            {check.status === 'passed' ? '✓ Passed' : '✗ Failed'}
          </CheckStatus>
          {check.is_critical && <CriticalBadge>Critical</CriticalBadge>}
          {check.issues_found > 0 && (
            <IssuesFound>{check.issues_found} issues found</IssuesFound>
          )}
        </ValidationCheckCard>
      ))}
    </ValidationChecksList>

    {critical_failures.length > 0 && (
      <ErrorMessage>
        Cannot proceed: {critical_failures.length} critical validation checks failed
      </ErrorMessage>
    )}
  </PreValidationSection>

  <ShutdownExecutionSection>
    <SectionTitle>Shutdown Execution</SectionTitle>
    <ShutdownProgress>
      <ProgressBar value={overall_progress} />
      <CurrentStep>{current_step.action}</CurrentStep>
    </ShutdownProgress>

    <ExecutionTimeline>
      {execution_log.map(step => (
        <TimelineStep key={step.step} status={step.status}>
          <StepNumber>{step.step}</StepNumber>
          <StepAction>{step.action}</StepAction>
          <StepStatus status={step.status}>
            {step.status === 'success' && '✓'}
            {step.status === 'failed' && '✗'}
            {step.status === 'forced' && '⚠'}
          </StepStatus>
          <StepDuration>{step.duration_seconds}s</StepDuration>
          {step.error && <StepError>{step.error}</StepError>}
        </TimelineStep>
      ))}
    </ExecutionTimeline>
  </ShutdownExecutionSection>

  <CleanupSection>
    <SectionTitle>Infrastructure Cleanup</SectionTitle>
    <CleanupTasksList>
      {cleanup_results.map(task => (
        <CleanupTaskCard key={task.task}>
          <TaskName>{task.task}</TaskName>
          <ResourceType>{task.resource_type}</ResourceType>
          <TaskStatus status={task.status} />
          <MonthlySavings>${task.monthly_savings}/month</MonthlySavings>
        </CleanupTaskCard>
      ))}
    </CleanupTasksList>
    <TotalSavings>
      Total Monthly Savings: ${total_monthly_savings}/month
    </TotalSavings>
  </CleanupSection>

  <PostValidationSection>
    <SectionTitle>Post-Shutdown Validation</SectionTitle>
    <ValidationChecksList>
      {post_validation_checks.map(check => (
        <ValidationCheckCard key={check.check_name}>
          <CheckName>{check.check_name}</CheckName>
          <CheckStatus status={check.status}>
            {check.status === 'passed' ? '✓ Verified' : '⚠ Warning'}
          </CheckStatus>
        </ValidationCheckCard>
      ))}
    </ValidationChecksList>
  </PostValidationSection>

  {shutdown_complete && (
    <CompletionSection>
      <SuccessMessage>
        ✓ System decommission completed successfully
      </SuccessMessage>
      <FinalMetrics>
        <Metric>
          <Label>Systems Decommissioned</Label>
          <Value>{systems_decommissioned}</Value>
        </Metric>
        <Metric>
          <Label>Annual Savings</Label>
          <Value>${actual_annual_savings}/year</Value>
        </Metric>
        <Metric>
          <Label>Execution Time</Label>
          <Value>{execution_duration} minutes</Value>
        </Metric>
      </FinalMetrics>

      <ActionButtons>
        <ViewAuditReportButton onClick={downloadAuditReport}>
          Download Audit Report
        </ViewAuditReportButton>
        <ReturnToDashboardButton onClick={() => navigate('/decommission')}>
          Return to Dashboard
        </ReturnToDashboardButton>
      </ActionButtons>
    </CompletionSection>
  )}
</SystemShutdownView>
```

## 🔐 Audit Trail

### Final Audit Report

```json
{
  "flow_id": "uuid",
  "report_type": "decommission_audit",
  "generated_at": "2025-11-06T11:00:00Z",
  "generated_by": "system",

  "summary": {
    "total_systems_decommissioned": 5,
    "total_execution_time_minutes": 180,
    "annual_cost_savings": 250000,
    "data_archived_gb": 1200,
    "compliance_attestation": "All regulatory requirements met"
  },

  "systems_decommissioned": [
    {
      "system_id": "uuid",
      "system_name": "Legacy CRM",
      "decommission_date": "2025-11-06T10:00:00Z",
      "risk_level": "High",
      "data_archived": true,
      "archive_location": "s3://archive/...",
      "annual_savings": 45000,
      "approvals_received": ["CIO", "Compliance Officer"]
    }
    // ... more systems
  ],

  "validation_results": {
    "pre_validation": {
      "total_checks": 5,
      "passed": 5,
      "failed": 0,
      "critical_failures": 0
    },
    "post_validation": {
      "total_checks": 5,
      "passed": 5,
      "warnings": 0
    }
  },

  "execution_timeline": [
    // Ordered list of all shutdown steps
  ],

  "compliance_attestation": {
    "data_retention_compliance": "GDPR, SOX, HIPAA",
    "retention_periods_applied": true,
    "encryption_verified": true,
    "access_revocation_complete": true,
    "audit_trail_complete": true,
    "attestation_signed_by": "Compliance Officer",
    "attestation_date": "2025-11-06T11:00:00Z"
  }
}
```

## ⚠️ Error Handling

### Critical Failure Recovery

```python
if critical_failure_occurred:
    # System shutdown is IRREVERSIBLE - cannot rollback
    # Best effort recovery:

    logger.critical(
        f"Critical failure during system shutdown: {error}",
        extra={"flow_id": flow_id, "system_id": system_id}
    )

    # Alert operations team immediately
    await send_critical_alert(
        severity="critical",
        message=f"Decommission failure - manual intervention required",
        details={
            "flow_id": flow_id,
            "system_id": system_id,
            "error": str(error),
            "execution_phase": current_phase
        }
    )

    # Mark flow as failed (but keep execution log)
    await repository.update_status(
        flow_id=flow_id,
        status="failed",
        current_phase="system_shutdown"
    )

    # Create incident ticket
    await create_incident(
        title=f"Decommission Failure: {system_name}",
        severity="critical",
        description=f"Manual cleanup required for {system_name}",
        execution_log=execution_log
    )
```

## 📝 Testing Checklist

- [ ] Pre-validation prevents shutdown when critical checks fail
- [ ] Graceful shutdown sequence executes in correct order
- [ ] Timeout handling forces shutdown when needed
- [ ] Infrastructure cleanup deletes all resources
- [ ] Access revocation completes successfully
- [ ] Post-validation verifies complete shutdown
- [ ] Audit trail captures all actions
- [ ] Cost savings calculated accurately
- [ ] Failed shutdowns create incident tickets
- [ ] Multi-tenant scoping enforced
- [ ] Phase marks flow as completed
- [ ] UI displays execution progress in real-time

---

**Flow Complete**: After system shutdown completes, the decommission flow is marked as completed. Users return to the [Decommission Dashboard](./01_Overview.md) to view final metrics and reports.
