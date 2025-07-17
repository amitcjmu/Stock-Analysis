# AI Modernize Migration Platform - Security Hardening Action Plan

## Executive Summary

This document outlines a comprehensive security hardening plan to ensure the AI Modernize Migration Platform passes security assessment. The plan is organized into immediate fixes (1-2 days), short-term improvements (1 week), and medium-term enhancements (2-4 weeks).

## Security Assessment Gap Analysis

### Critical Gaps Identified
1. **Hardcoded Secrets** - SECRET_KEY and API keys in source code
2. **Weak Authentication** - No MFA, SSO, or proper JWT implementation
3. **API Security** - Missing rate limiting, API key management
4. **Network Security** - Incomplete documentation and implementation
5. **Data Protection** - No encryption at rest for sensitive data

## Phase 1: Immediate Security Fixes (1-2 days)

### 1.1 Remove Hardcoded Secrets

**Priority**: CRITICAL  
**Timeline**: Day 1  
**Owner**: Backend Team

#### Actions:
```python
# backend/app/core/config.py - BEFORE
SECRET_KEY: str = "your-secret-key-here"  # REMOVE THIS
DEEPINFRA_API_KEY: str = "hardcoded-key"  # REMOVE THIS

# backend/app/core/config.py - AFTER
SECRET_KEY: str = Field(default=None, env='SECRET_KEY')
DEEPINFRA_API_KEY: str = Field(default=None, env='DEEPINFRA_API_KEY')

# Add validation
@validator('SECRET_KEY')
def validate_secret_key(cls, v):
    if not v:
        raise ValueError("SECRET_KEY must be set in environment")
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

#### Environment Configuration:
```bash
# .env.example
SECRET_KEY=generate-with-openssl-rand-hex-32
DEEPINFRA_API_KEY=your-api-key-here
JWT_SECRET_KEY=another-secure-random-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
```

### 1.2 Implement Proper JWT Authentication

**Priority**: HIGH  
**Timeline**: Day 1-2  
**Owner**: Backend Team

#### Implementation:
```python
# backend/app/core/auth/jwt_handler.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for revocation
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### 1.3 Create Security Configuration Documentation

**Priority**: HIGH  
**Timeline**: Day 2  
**Owner**: DevOps Team

Create comprehensive security documentation:
- Network architecture diagram
- Port and service mapping
- Data flow diagrams with encryption points
- Authentication flow documentation

## Phase 2: Short-term Security Improvements (1 week)

### 2.1 Implement Rate Limiting

**Priority**: HIGH  
**Timeline**: Days 3-4  
**Owner**: Backend Team

#### Using slowapi:
```python
# backend/app/core/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"  # Use Redis for distributed rate limiting
)

# backend/main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Apply to endpoints
@router.post("/login")
@limiter.limit("5 per minute")
async def login(request: Request, ...):
    ...

@router.post("/api/v3/discovery-flow/flows")
@limiter.limit("20 per hour")
async def create_flow(request: Request, ...):
    ...
```

### 2.2 Add API Key Management

**Priority**: HIGH  
**Timeline**: Days 4-5  
**Owner**: Backend Team

#### Implementation:
```python
# backend/app/models/api_key.py
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    client_account_id = Column(Integer, ForeignKey("client_accounts.id"))
    permissions = Column(JSON)  # ["read", "write", "admin"]
    rate_limit = Column(Integer, default=1000)  # requests per hour
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

# backend/app/core/auth/api_key_auth.py
async def verify_api_key(
    api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
):
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
            or_(APIKey.expires_at == None, APIKey.expires_at > datetime.utcnow())
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Update last used
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()
    
    return api_key_obj
```

### 2.3 Implement CORS Security Headers

**Priority**: MEDIUM  
**Timeline**: Day 5  
**Owner**: Backend Team

```python
# backend/app/core/security_headers.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from secure import SecureHeaders

secure_headers = SecureHeaders(
    server="",  # Hide server info
    hsts={"max-age": 31536000, "includeSubDomains": True},
    xfo="DENY",
    xss="1; mode=block",
    content="nosniff",
    csp="default-src 'self'; script-src 'self' 'unsafe-inline'",
    referrer="strict-origin-when-cross-origin"
)

# Apply middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*.yourdomain.com", "localhost"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    secure_headers.apply(response)
    return response
```

### 2.4 Add Input Validation and Sanitization

**Priority**: HIGH  
**Timeline**: Days 6-7  
**Owner**: Backend Team

```python
# backend/app/core/validation/sanitizers.py
import bleach
from pydantic import validator

class SanitizedString(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        # Remove dangerous HTML/scripts
        cleaned = bleach.clean(v, tags=[], strip=True)
        # Prevent SQL injection patterns
        dangerous_patterns = ['--', '/*', '*/', 'xp_', 'sp_']
        for pattern in dangerous_patterns:
            if pattern in cleaned.lower():
                raise ValueError(f"Dangerous pattern detected: {pattern}")
        return cleaned

# Use in schemas
class FlowCreate(BaseModel):
    name: SanitizedString
    description: Optional[SanitizedString]
```

## Phase 3: Medium-term Security Enhancements (2-4 weeks)

### 3.1 Implement SSO/SAML Integration

**Priority**: HIGH  
**Timeline**: Week 2-3  
**Owner**: Backend Team

```python
# backend/app/core/auth/sso_handler.py
from python3_saml import OneLogin_Saml2_Auth
import xml.etree.ElementTree as ET

class SSOHandler:
    def __init__(self, settings):
        self.settings = settings
    
    def initiate_sso(self, request):
        auth = OneLogin_Saml2_Auth(request, self.settings)
        return auth.login()
    
    def handle_sso_callback(self, request):
        auth = OneLogin_Saml2_Auth(request, self.settings)
        auth.process_response()
        
        if not auth.is_authenticated():
            raise HTTPException(status_code=401, detail="SSO authentication failed")
        
        attributes = auth.get_attributes()
        return {
            'email': attributes.get('email')[0],
            'name': attributes.get('name')[0],
            'groups': attributes.get('groups', [])
        }
```

### 3.2 Implement Multi-Factor Authentication

**Priority**: HIGH  
**Timeline**: Week 3  
**Owner**: Backend Team

```python
# backend/app/core/auth/mfa_handler.py
import pyotp
import qrcode
from io import BytesIO

class MFAHandler:
    def generate_secret(self, user_email: str):
        secret = pyotp.random_base32()
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name='AI Modernize Migration Platform'
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        
        return {
            'secret': secret,
            'qr_code': base64.b64encode(buf.getvalue()).decode(),
            'provisioning_uri': provisioning_uri
        }
    
    def verify_token(self, secret: str, token: str):
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
```

### 3.3 Implement Data Encryption at Rest

**Priority**: HIGH  
**Timeline**: Week 3-4  
**Owner**: Backend/Database Team

```python
# backend/app/core/encryption/field_encryption.py
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String

class EncryptedType(TypeDecorator):
    impl = String
    cache_ok = True
    
    def __init__(self, key, *args, **kwargs):
        self.key = key
        self.fernet = Fernet(key)
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return value

# Use in models
class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    # Encrypt sensitive fields
    connection_string = Column(EncryptedType(settings.ENCRYPTION_KEY))
    api_credentials = Column(EncryptedType(settings.ENCRYPTION_KEY))
```

### 3.4 Implement Security Monitoring and Alerting

**Priority**: MEDIUM  
**Timeline**: Week 4  
**Owner**: DevOps Team

```python
# backend/app/core/monitoring/security_monitor.py
from prometheus_client import Counter, Histogram, Gauge
import asyncio

# Metrics
failed_login_attempts = Counter('failed_login_attempts', 'Failed login attempts', ['ip_address'])
successful_logins = Counter('successful_logins', 'Successful logins', ['user_role'])
api_errors = Counter('api_errors', 'API errors', ['endpoint', 'error_type'])
suspicious_activities = Counter('suspicious_activities', 'Suspicious activities detected', ['type'])

class SecurityMonitor:
    def __init__(self, alert_threshold=5):
        self.alert_threshold = alert_threshold
        self.failed_attempts = {}
    
    async def track_failed_login(self, ip_address: str, username: str):
        failed_login_attempts.labels(ip_address=ip_address).inc()
        
        # Track for alerting
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
        
        self.failed_attempts[ip_address].append({
            'username': username,
            'timestamp': datetime.utcnow()
        })
        
        # Check if threshold exceeded
        recent_attempts = [
            a for a in self.failed_attempts[ip_address] 
            if a['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
        ]
        
        if len(recent_attempts) >= self.alert_threshold:
            await self.send_security_alert(
                f"Multiple failed login attempts from {ip_address}",
                recent_attempts
            )
    
    async def send_security_alert(self, message: str, details: dict):
        # Send to monitoring system
        # Send email to security team
        # Log to security audit
        pass
```

## Phase 4: Security Scanning Tools Integration

### 4.1 Static Application Security Testing (SAST)

**Tool**: Bandit (Python Security)  
**Integration**: GitHub Actions / GitLab CI

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit Security Scan
        uses: gaurav-nelson/bandit-action@v1
        with:
          path: "backend/"
          level: "medium"
          confidence: "medium"
          exit_zero: false

  safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Safety Check
        run: |
          pip install safety
          safety check --json --file=backend/requirements.txt

  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: "p/security-audit p/python p/owasp-top-ten"
```

### 4.2 Dynamic Application Security Testing (DAST)

**Tool**: OWASP ZAP  
**Integration**: Docker-based scanning

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  zap:
    image: owasp/zap2docker-stable
    command: >
      zap-baseline.py 
      -t http://backend:8000 
      -g gen.conf 
      -r scan_report.html
    volumes:
      - ./security-reports:/zap/wrk
    depends_on:
      - backend

  nikto:
    image: sullo/nikto
    command: >
      -h http://backend:8000
      -o /tmp/nikto_report.html
      -Format html
    volumes:
      - ./security-reports:/tmp
```

### 4.3 Container Security Scanning

**Tool**: Trivy  
**Integration**: CI/CD Pipeline

```yaml
# Dockerfile.security
FROM python:3.11-slim as scanner

# Install Trivy
RUN apt-get update && \
    apt-get install -y wget apt-transport-https gnupg lsb-release && \
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - && \
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee -a /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy

# Scan the image
RUN trivy image --severity HIGH,CRITICAL python:3.11-slim

# .github/workflows/container-security.yml
name: Container Security Scan

on:
  push:
    paths:
      - 'Dockerfile'
      - 'backend/requirements*.txt'

jobs:
  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'migrate-platform:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### 4.4 Dependency Vulnerability Scanning

**Tool**: Snyk / pip-audit  
**Integration**: Pre-commit hooks and CI

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-ll', '-i', '-r', 'backend/']
        
  - repo: https://github.com/pyupio/safety
    rev: v2.3.5
    hooks:
      - id: safety
        args: ['--json']

# backend/requirements-dev.txt
pip-audit>=2.6.1
bandit>=1.7.5
safety>=2.3.5
semgrep>=1.45.0
```

### 4.5 Infrastructure as Code (IaC) Security

**Tool**: Checkov  
**Integration**: Terraform/Docker scanning

```bash
# scan_iac.sh
#!/bin/bash

# Scan Dockerfiles
checkov -f Dockerfile --framework dockerfile

# Scan Kubernetes manifests
checkov -d ./k8s --framework kubernetes

# Scan Terraform (if used)
checkov -d ./terraform --framework terraform

# Generate report
checkov -d . --output-file security-report.json --output json
```

## Security Compliance Dashboard

### Create Security Metrics Dashboard

```python
# backend/app/api/v1/endpoints/security_metrics.py
@router.get("/security/metrics")
async def get_security_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_platform_admin)
):
    return {
        "authentication": {
            "mfa_enabled_users": await count_mfa_users(db),
            "sso_enabled": settings.SSO_ENABLED,
            "password_policy_compliant": await check_password_compliance(db)
        },
        "api_security": {
            "rate_limiting_enabled": True,
            "api_keys_active": await count_active_api_keys(db),
            "endpoints_protected": await count_protected_endpoints()
        },
        "data_protection": {
            "encryption_at_rest": await check_encryption_status(db),
            "sensitive_fields_encrypted": await count_encrypted_fields(db),
            "backup_encryption": settings.BACKUP_ENCRYPTION_ENABLED
        },
        "compliance": {
            "last_security_scan": await get_last_scan_date(db),
            "vulnerabilities_found": await count_vulnerabilities(db),
            "compliance_score": await calculate_compliance_score(db)
        }
    }
```

## Implementation Timeline

### Week 1: Foundation
- Days 1-2: Remove hardcoded secrets, implement JWT
- Days 3-5: Add rate limiting and API key management
- Days 6-7: Security headers and input validation

### Week 2: Authentication Enhancement
- Days 8-10: SSO/SAML integration
- Days 11-12: MFA implementation
- Days 13-14: Security monitoring setup

### Week 3: Data Protection
- Days 15-17: Encryption at rest
- Days 18-19: Security scanning integration
- Days 20-21: Compliance dashboard

### Week 4: Testing and Documentation
- Days 22-23: Penetration testing
- Days 24-25: Security documentation
- Days 26-28: Security assessment preparation

## Security Checklist for Assessment

- [ ] All secrets removed from code and stored in environment variables
- [ ] JWT authentication with proper expiration
- [ ] Rate limiting on all API endpoints
- [ ] API key management system
- [ ] SSO/SAML integration
- [ ] Multi-factor authentication
- [ ] Data encryption at rest
- [ ] Security headers (HSTS, CSP, XSS protection)
- [ ] Input validation and sanitization
- [ ] Security monitoring and alerting
- [ ] Regular vulnerability scanning
- [ ] Penetration testing results
- [ ] Security documentation complete
- [ ] Incident response plan
- [ ] Backup and recovery procedures

## Conclusion

This comprehensive security hardening plan addresses all identified gaps and provides a clear path to passing the security assessment. The phased approach allows for progressive improvements while maintaining system functionality. Integration of automated security scanning tools ensures ongoing security compliance throughout the development lifecycle.