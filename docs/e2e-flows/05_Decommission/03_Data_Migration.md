# Decommission Flow - Phase 2: Data Migration

**Last Updated:** 2025-11-06
**Phase Name**: `data_migration` (per ADR-027 FlowTypeConfig)
**Estimated Duration**: 120 minutes

> **⚠️ IMPLEMENTATION STATUS**: This phase is **PARTIALLY IMPLEMENTED**. Database models for data retention policies and archive jobs exist. API endpoints for policy management are implemented. However, actual archive job execution, S3 integration, and integrity verification are **STUB implementations** marked with TODO comments. Full data archival automation pending. See [Milestone #952](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/952) for status.
>
> **⚠️ HUMAN-IN-THE-LOOP WORKFLOW**: This phase REQUIRES manual user input, approvals, and artifact collection. The current implementation provides database structure and API endpoints, but does NOT include:
> - User input forms for manual data entry
> - Approval workflow UI
> - Artifact upload/storage
> - Progress tracking UI
>
> See [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md) for required additions.

## 📋 Phase Overview

The Data Migration phase creates and executes data retention policies and archive jobs before system decommission. This phase ensures regulatory compliance, preserves critical business data, and verifies data integrity.

**Phase Objectives:**
1. Apply data retention policies per compliance requirements
2. Create archive jobs for each system
3. Execute data migration to secure archive storage
4. Verify data integrity with checksums
5. Generate archival reports for audit trail
6. Ensure accessibility of archived data

**Phase Output:**
- Data retention policies applied to each system
- Archive jobs completed with integrity verification
- Archive location and access instructions
- Compliance attestation reports
- Data recovery procedures

## 👤 Manual Input Requirements

This phase REQUIRES significant user coordination and cannot be automated:

### User Must Provide:
1. **Data Retention Policies**: Review AI suggestions, apply company-specific policies
2. **Compliance Requirements**: Confirm regulatory requirements (GDPR, SOX, HIPAA)
3. **Archive Destinations**: S3 buckets, retention periods, access controls
4. **Data Classification**: Sensitive vs. non-sensitive, encryption requirements
5. **Migration Progress**: Manual updates as data is archived/migrated
6. **Stakeholder Approvals**:
   - Legal approval for data retention/destruction
   - Compliance approval for archival methods
   - Data owner approval for migration

### Artifacts to Collect:
- Data retention policy documents
- Compliance attestations
- Archive verification reports (checksums, integrity checks)
- Legal approvals for data destruction
- Migration completion certificates

### Current Implementation Status:
- ✅ Database models for policies and archive jobs
- ❌ Archive job execution NOT fully implemented (S3 integration pending)
- ❌ User input forms for policies NOT implemented
- ❌ Artifact upload for compliance docs NOT implemented
- ❌ Manual progress tracking UI NOT implemented

## 🏗️ Architecture

### Agent-Based Execution

```python
# backend/app/services/child_flow_services/decommission.py
async def _execute_data_migration(
    self,
    child_flow,
    phase_input: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute data migration phase using TenantScopedAgentPool.

    Agents Used (STUB - Models exist, execution logic pending):
    1. Compliance Officer (STUB): Determines retention requirements
    2. Data Migration Specialist (PLANNED): Executes archive jobs
    3. Data Integrity Validator (PLANNED): Verifies migration success

    Per ADR-025: Uses DecommissionAgentPool (NOT per-call Crew instantiation)
    """
    # Update phase status to running
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="data_migration",
        phase_status="running"
    )

    # Get agent pool (persistent, tenant-scoped)
    agent_pool = TenantScopedAgentPool(
        client_account_id=self.context.client_account_id,
        engagement_id=self.context.engagement_id
    )

    # Execute data migration crew
    migration_crew = agent_pool.get_data_migration_crew()
    result = await migration_crew.execute(
        flow_id=child_flow.flow_id,
        system_ids=child_flow.selected_system_ids,
        retention_policies=await self._get_retention_policies()
    )

    # Store results in database
    await self._store_migration_results(child_flow, result)

    # Update phase status to completed
    await self.repository.update_phase_status(
        flow_id=child_flow.flow_id,
        phase_name="data_migration",
        phase_status="completed"
    )

    # Auto-progress to system_shutdown phase
    await self.repository.update_status(
        flow_id=child_flow.flow_id,
        status="system_shutdown",
        current_phase="system_shutdown"
    )

    return {
        "status": "success",
        "phase": "data_migration",
        "next_phase": "system_shutdown",
        "archive_jobs_completed": result.archive_jobs_completed,
        "data_integrity_verified": result.data_integrity_verified,
        "total_data_archived_gb": result.total_data_archived_gb
    }
```

### CrewAI Agent Configuration

**Compliance Officer Agent**:
```python
{
    "role": "Compliance Officer",
    "goal": "Ensure data retention meets all regulatory and legal requirements",
    "backstory": "Legal compliance expert with 20 years experience in data governance",
    "tools": [
        "get_compliance_requirements",  # GDPR, SOX, HIPAA, etc.
        "classify_data_sensitivity",
        "determine_retention_period"
    ],
    "memory": False,  # Per ADR-024
    "verbose": False
}
```

**Data Migration Specialist Agent**:
```python
{
    "role": "Data Migration Specialist",
    "goal": "Execute secure data archival with zero data loss",
    "backstory": "Database architect specializing in data migration and archival",
    "tools": [
        "create_archive_job",
        "execute_data_export",
        "upload_to_archive_storage",
        "generate_archive_manifest"
    ],
    "memory": False,
    "verbose": False
}
```

**Data Integrity Validator Agent**:
```python
{
    "role": "Data Integrity Validator",
    "goal": "Verify data integrity and accessibility post-migration",
    "backstory": "Quality assurance specialist for data migration projects",
    "tools": [
        "calculate_checksum",
        "verify_archive_completeness",
        "test_data_retrieval",
        "generate_validation_report"
    ],
    "memory": False,
    "verbose": False
}
```

## 📊 Data Retention Policies

### Policy Structure

```python
# backend/app/models/decommission_flow/policy_models.py
class DataRetentionPolicy(Base):
    __tablename__ = "data_retention_policies"
    __table_args__ = {"schema": "migration"}

    policy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False)
    engagement_id = Column(UUID(as_uuid=True), nullable=False)

    # Policy identification
    policy_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Retention requirements
    retention_period_days = Column(Integer, nullable=False)
    compliance_requirements = Column(ARRAY(String), nullable=False)

    # Data classification
    data_types = Column(ARRAY(String), nullable=False)
    storage_location = Column(String(255), nullable=False)
    encryption_required = Column(Boolean, default=True)

    # Status
    status = Column(String(50), default="active")
```

### Standard Retention Policies

```json
[
  {
    "policy_name": "Business Critical Data",
    "description": "Financial records, audit trails, and compliance data",
    "retention_period_days": 2555,  // 7 years
    "compliance_requirements": ["GDPR", "SOX", "HIPAA"],
    "data_types": ["Financial Records", "Audit Trails", "Compliance Data"],
    "storage_location": "s3://archive-bucket/business-critical/",
    "encryption_required": true
  },
  {
    "policy_name": "Application Data",
    "description": "User data, application logs, and configuration files",
    "retention_period_days": 1095,  // 3 years
    "compliance_requirements": ["GDPR", "CCPA"],
    "data_types": ["User Data", "Application Logs", "Configuration Files"],
    "storage_location": "s3://archive-bucket/application-data/",
    "encryption_required": true
  },
  {
    "policy_name": "System Logs",
    "description": "Security logs, system events, and monitoring data",
    "retention_period_days": 365,  // 1 year
    "compliance_requirements": ["SOX", "PCI-DSS"],
    "data_types": ["Security Logs", "System Events", "Monitoring Data"],
    "storage_location": "s3://archive-bucket/system-logs/",
    "encryption_required": true
  }
]
```

### Policy Assignment Logic

```python
async def assign_retention_policy(
    system: Asset,
    compliance_requirements: List[str]
) -> DataRetentionPolicy:
    """
    Assign retention policy based on system data classification.

    Priority:
    1. Explicit policy assignment (if exists)
    2. Data sensitivity classification (from Discovery flow)
    3. Compliance requirements (from Assessment flow)
    4. Default policy (minimum 1 year retention)
    """
    # Check for explicit policy
    if system.retention_policy_id:
        return await get_policy(system.retention_policy_id)

    # Determine from data classification
    if "PII" in system.data_classification or "PHI" in system.data_classification:
        # High sensitivity → 7 year retention
        return await get_policy_by_name("Business Critical Data")

    elif "Financial" in system.data_classification:
        # Financial data → 7 year retention (SOX)
        return await get_policy_by_name("Business Critical Data")

    elif "User Data" in system.data_classification:
        # User data → 3 year retention (GDPR)
        return await get_policy_by_name("Application Data")

    else:
        # Default → 1 year retention
        return await get_policy_by_name("System Logs")
```

## 🗃️ Archive Jobs

### Archive Job Structure

```python
# backend/app/models/decommission_flow/audit_models.py
class ArchiveJob(Base):
    __tablename__ = "archive_jobs"
    __table_args__ = {"schema": "migration"}

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), ForeignKey("migration.decommission_flows.flow_id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("migration.data_retention_policies.policy_id"), nullable=False)

    # System details
    system_id = Column(UUID(as_uuid=True), ForeignKey("migration.assets.id"), nullable=False)
    system_name = Column(String(255), nullable=False)

    # Job details
    data_size_gb = Column(Numeric(15, 2))
    archive_location = Column(String(500))

    status = Column(String(50), nullable=False, default="queued")
    progress_percentage = Column(Integer, default=0)

    # Timing
    scheduled_start = Column(TIMESTAMP(timezone=True))
    actual_start = Column(TIMESTAMP(timezone=True))
    estimated_completion = Column(TIMESTAMP(timezone=True))
    actual_completion = Column(TIMESTAMP(timezone=True))

    # Verification
    integrity_verified = Column(Boolean, default=False)
    verification_checksum = Column(String(255))
```

### Archive Job Execution

```python
async def execute_archive_job(
    job: ArchiveJob,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Execute archive job with progress tracking and integrity verification.

    Steps:
    1. Export data from source system
    2. Compress and encrypt data
    3. Upload to archive storage
    4. Calculate checksum
    5. Verify data integrity
    6. Generate archive manifest
    """
    try:
        # Update job status
        job.status = "in_progress"
        job.actual_start = datetime.utcnow()
        await db.flush()

        # Step 1: Export data
        logger.info(f"Exporting data for system {job.system_name}")
        export_result = await export_system_data(
            system_id=job.system_id,
            progress_callback=lambda p: update_progress(job, p, db)
        )
        job.data_size_gb = export_result.size_gb
        job.progress_percentage = 40

        # Step 2: Compress and encrypt
        logger.info(f"Compressing and encrypting data")
        encrypted_file = await compress_and_encrypt(
            data_path=export_result.file_path,
            encryption_key=get_encryption_key()
        )
        job.progress_percentage = 60

        # Step 3: Upload to archive storage
        logger.info(f"Uploading to archive storage")
        upload_result = await upload_to_s3(
            file_path=encrypted_file,
            bucket=get_archive_bucket(),
            prefix=f"{job.flow_id}/{job.system_id}/"
        )
        job.archive_location = upload_result.s3_url
        job.progress_percentage = 80

        # Step 4: Calculate checksum
        logger.info(f"Calculating checksum")
        checksum = await calculate_sha256(encrypted_file)
        job.verification_checksum = checksum
        job.progress_percentage = 90

        # Step 5: Verify integrity
        logger.info(f"Verifying data integrity")
        verification_result = await verify_archive_integrity(
            archive_location=job.archive_location,
            expected_checksum=checksum,
            expected_size_gb=job.data_size_gb
        )
        job.integrity_verified = verification_result.passed
        job.progress_percentage = 100

        # Step 6: Generate manifest
        manifest = await generate_archive_manifest(job)

        # Complete job
        job.status = "completed"
        job.actual_completion = datetime.utcnow()
        await db.commit()

        return {
            "status": "success",
            "job_id": str(job.job_id),
            "archive_location": job.archive_location,
            "data_size_gb": float(job.data_size_gb),
            "checksum": job.verification_checksum,
            "integrity_verified": job.integrity_verified,
            "manifest": manifest
        }

    except Exception as e:
        logger.error(f"Archive job failed: {e}", exc_info=True)

        job.status = "failed"
        job.error_message = str(e)
        await db.commit()

        return {
            "status": "failed",
            "job_id": str(job.job_id),
            "error": str(e)
        }
```

## 🎨 Frontend UI

### Data Migration Progress Page

**URL**: `/decommission/flow/{flow_id}/data-migration`

```typescript
<DataMigrationView>
  <MigrationSummary>
    <TotalJobs>{archive_jobs.length} systems</TotalJobs>
    <CompletedJobs>{completed_count} completed</CompletedJobs>
    <TotalDataSize>{total_gb} GB archived</TotalDataSize>
    <OverallProgress>
      <ProgressBar value={overall_progress} />
    </OverallProgress>
  </MigrationSummary>

  <PolicyAssignmentTable>
    <TableHeader>
      <Column>System</Column>
      <Column>Data Classification</Column>
      <Column>Retention Policy</Column>
      <Column>Retention Period</Column>
      <Column>Compliance</Column>
    </TableHeader>
    {policy_assignments.map(assignment => (
      <TableRow key={assignment.system_id}>
        <Cell>{assignment.system_name}</Cell>
        <Cell><DataClassificationBadge types={assignment.data_types} /></Cell>
        <Cell>{assignment.policy_name}</Cell>
        <Cell>{assignment.retention_period_days} days</Cell>
        <Cell><ComplianceBadges requirements={assignment.compliance_requirements} /></Cell>
      </TableRow>
    ))}
  </PolicyAssignmentTable>

  <ArchiveJobsList>
    {archive_jobs.map(job => (
      <ArchiveJobCard key={job.job_id}>
        <JobHeader>
          <SystemName>{job.system_name}</SystemName>
          <StatusBadge status={job.status} />
          <DataSize>{job.data_size_gb} GB</DataSize>
        </JobHeader>

        <ProgressSection>
          <ProgressBar value={job.progress_percentage} />
          <ProgressText>{job.progress_percentage}% complete</ProgressText>

          {job.status === 'in_progress' && (
            <EstimatedCompletion>
              ETA: {formatDate(job.estimated_completion)}
            </EstimatedCompletion>
          )}
        </ProgressSection>

        {job.status === 'completed' && (
          <VerificationSection>
            <IntegrityCheck verified={job.integrity_verified} />
            <Checksum>{job.verification_checksum.substring(0, 16)}...</Checksum>
            <ArchiveLocation>{job.archive_location}</ArchiveLocation>
          </VerificationSection>
        )}

        {job.status === 'failed' && (
          <ErrorSection>
            <ErrorMessage>{job.error_message}</ErrorMessage>
            <RetryButton onClick={() => retryJob(job.job_id)}>
              Retry Archive
            </RetryButton>
          </ErrorSection>
        )}
      </ArchiveJobCard>
    ))}
  </ArchiveJobsList>

  <ActionButtons>
    <ViewManifestButton onClick={downloadManifest}>
      Download Archive Manifest
    </ViewManifestButton>

    {all_jobs_completed && (
      <ContinueButton onClick={proceedToShutdown}>
        Continue to System Shutdown
      </ContinueButton>
    )}
  </ActionButtons>
</DataMigrationView>
```

### API Calls

```typescript
// Poll archive job status
const { data: jobs } = useQuery({
  queryKey: ['archive-jobs', flowId],
  queryFn: () => apiCall(`/decommission-flow/${flowId}/archive-jobs`),
  enabled: !!flowId,
  refetchInterval: (data) => {
    // Aggressive polling during active jobs
    const hasActiveJobs = data?.some(j => j.status === 'in_progress');
    return hasActiveJobs ? 5000 : 15000;
  }
});

// Retry failed job
const retryJob = useMutation({
  mutationFn: (jobId: string) =>
    apiCall(`/decommission-flow/archive-jobs/${jobId}/retry`, {
      method: 'POST'
    }),
  onSuccess: () => {
    queryClient.invalidateQueries(['archive-jobs', flowId]);
    toast.success('Archive job restarted');
  }
});

// Download archive manifest
const downloadManifest = async () => {
  const response = await apiCall(
    `/decommission-flow/${flowId}/archive-manifest`,
    { method: 'GET', responseType: 'blob' }
  );

  const url = window.URL.createObjectURL(response);
  const a = document.createElement('a');
  a.href = url;
  a.download = `archive-manifest-${flowId}.json`;
  a.click();
};
```

## 🔐 Data Security

### Encryption

All archived data is encrypted at rest using AES-256:

```python
def compress_and_encrypt(
    data_path: str,
    encryption_key: bytes
) -> str:
    """
    Compress and encrypt data before archival.

    Steps:
    1. Compress with gzip (reduces storage costs)
    2. Encrypt with AES-256-GCM
    3. Add HMAC for integrity verification
    """
    # Compress
    compressed_path = f"{data_path}.gz"
    with open(data_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Encrypt
    cipher = AES.new(encryption_key, AES.MODE_GCM)
    with open(compressed_path, 'rb') as f_in:
        plaintext = f_in.read()
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # Write encrypted data
    encrypted_path = f"{compressed_path}.enc"
    with open(encrypted_path, 'wb') as f_out:
        f_out.write(cipher.nonce)
        f_out.write(tag)
        f_out.write(ciphertext)

    return encrypted_path
```

### Access Control

Archive storage uses IAM policies for access control:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/ArchiveAccessRole"
      },
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::archive-bucket/*",
        "arn:aws:s3:::archive-bucket"
      ],
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

## ⚠️ Error Handling

### Archive Job Failures

```python
# Automatic retry with exponential backoff
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = [60, 300, 900]  # 1 min, 5 min, 15 min

if job.status == "failed" and job.retry_count < MAX_RETRIES:
    retry_delay = RETRY_DELAY_SECONDS[job.retry_count]

    await schedule_job_retry(
        job_id=job.job_id,
        delay_seconds=retry_delay
    )

    job.retry_count += 1
    job.status = "queued"
    await db.commit()
```

### Integrity Verification Failures

```python
if not verification_result.passed:
    logger.error(
        f"Integrity verification failed for job {job.job_id}: "
        f"expected checksum {expected_checksum}, got {actual_checksum}"
    )

    # Mark job as failed
    job.status = "failed"
    job.error_message = "Data integrity verification failed"
    job.integrity_verified = False

    # Alert operations team
    await send_alert(
        severity="high",
        message=f"Archive integrity verification failed for {job.system_name}",
        details={"job_id": str(job.job_id), "flow_id": str(job.flow_id)}
    )

    await db.commit()
```

## 📝 Testing Checklist

- [ ] Retention policies assigned correctly based on data classification
- [ ] Archive jobs created for all selected systems
- [ ] Data export executes without data loss
- [ ] Encryption applied before upload
- [ ] Archive upload succeeds to correct location
- [ ] Checksum calculation accurate
- [ ] Integrity verification detects corruption
- [ ] Progress tracking updates in real-time
- [ ] Failed jobs retry automatically
- [ ] Archive manifest generated correctly
- [ ] Multi-tenant scoping enforced
- [ ] Phase transitions to system_shutdown after completion

---

**Next Phase**: After data migration completes, the flow proceeds to [System Shutdown](./04_System_Shutdown.md) for the final decommission execution.
