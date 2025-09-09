# Dependency Security Management Patterns

## GitHub Dependabot Integration
**WORKFLOW**: Systematic approach to handling security vulnerability alerts

### Alert Prioritization
- **HIGH/CRITICAL**: Fix immediately, block deployments
- **MODERATE**: Fix in next development cycle  
- **LOW**: Monitor and fix when convenient

### Investigation Pattern
```bash
# 1. Check current versions
grep "package_name" requirements.txt requirements-docker.txt

# 2. Research vulnerability details
# Check GitHub security advisory or CVE database

# 3. Verify fix availability
pip index versions package_name
```

## Specific Vulnerability Fixes (2025-09)

### h2 HTTP/2 Request Splitting (GHSA-847f-9342-265h)
**VULNERABILITY**: h2 4.2.0 vulnerable to HTTP/2 request splitting
**CVE**: CVE-2024-XXXXX (moderate severity)
**FIX**: Update to h2 4.3.0

```python
# requirements.txt & requirements-docker.txt
# BEFORE
h2==4.2.0

# AFTER  
h2==4.3.0  # Updated from 4.2.0 - fixes GHSA-847f-9342-265h HTTP/2 request splitting vulnerability
```

### Verification Pattern
```bash
# 1. Update both requirement files
sed -i 's/h2==4.2.0/h2==4.3.0/g' requirements.txt requirements-docker.txt

# 2. Add security comment explaining the fix
echo "# Updated from 4.2.0 - fixes GHSA-847f-9342-265h HTTP/2 request splitting vulnerability" >> requirements.txt

# 3. Test in Docker environment
docker-compose build backend
docker-compose up backend

# 4. Commit with security context
git commit -m "security: Update h2 to 4.3.0 to fix HTTP/2 request splitting vulnerability"
```

## False Positive Handling
**PATTERN**: Verify package versions before updating

### Common False Positives
- **Jinja2**: Dependabot alerts on old versions, but project already using secure version
- **urllib3**: Similar version confusion between docker and main requirements

### Verification Commands
```bash
# Check actual installed versions
pip list | grep -E "(jinja2|urllib3|h2)"

# Cross-reference with requirements
grep -E "(Jinja2|urllib3|h2)" requirements*.txt

# Verify security advisory applies to current version
```

## Security Update Workflow
1. **Assess Impact**: Check if vulnerability affects current usage
2. **Test Locally**: Verify update doesn't break functionality  
3. **Update Both Files**: requirements.txt AND requirements-docker.txt
4. **Add Context**: Include CVE/GHSA reference in comments
5. **Docker Test**: Verify in containerized environment
6. **Security Commit**: Use "security:" prefix in commit message

## Prevention Patterns
- Keep requirements files synchronized
- Use exact version pinning for security-critical packages
- Set up automated Dependabot checks
- Regular security audit schedule (monthly)
- Document known false positives to avoid repeated work