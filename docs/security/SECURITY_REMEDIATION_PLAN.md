# 🔒 Security Remediation Plan
**AI Force Migration Platform**  
**Plan Date:** July 8, 2025  
**Implementation Timeline:** 2-4 weeks  
**Priority:** CRITICAL  

## 📋 Executive Summary

This comprehensive security remediation plan addresses **11 confirmed critical and high-risk vulnerabilities** identified in the AI Force Migration Platform. Implementation must begin immediately to prevent potential security breaches.

**Key Objectives:**
- Eliminate all hardcoded credentials
- Implement secure authentication system
- Strengthen input validation and security headers
- Establish proper session management

## 🎯 Remediation Strategy

### Phase 1: Critical Security Fixes (Week 1)
**Priority:** CRITICAL - Must be completed first

### Phase 2: High-Risk Vulnerabilities (Week 2-3)
**Priority:** HIGH - Implement after critical fixes

### Phase 3: Security Hardening (Week 3-4)
**Priority:** MEDIUM - Complete security posture

---

## 🚨 Phase 1: Critical Security Fixes

### 1.1 Remove Hardcoded Credentials
**Files to modify:**
- `backend/app/core/config.py`

**Implementation:**
```python
# REMOVE THIS:
DEEPINFRA_API_KEY: str = Field(
    default="U8JskPYWXprQvw2PGbv4lyxfcJQggI48", 
    env="DEEPINFRA_API_KEY"
)

# REPLACE WITH:
DEEPINFRA_API_KEY: str = Field(
    default="", 
    env="DEEPINFRA_API_KEY"
)

# Add validation
@field_validator('DEEPINFRA_API_KEY')
def validate_api_key(cls, v):
    if not v:
        raise ValueError("DEEPINFRA_API_KEY environment variable is required")
    return v
```

**Environment Setup:**
```bash
# Add to .env file
DEEPINFRA_API_KEY=your_actual_api_key_here

# Update Railway deployment
railway variables set DEEPINFRA_API_KEY=your_actual_api_key_here
```

### 1.2 Implement Secure Secret Key
**Files to modify:**
- `backend/app/core/config.py`

**Implementation:**
```python
# REMOVE THIS:
SECRET_KEY: str = "your-secret-key-here"

# REPLACE WITH:
SECRET_KEY: str = Field(env="SECRET_KEY")

# Add validation
@field_validator('SECRET_KEY')
def validate_secret_key(cls, v):
    if not v or v == "your-secret-key-here":
        raise ValueError("SECRET_KEY environment variable is required")
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

**Secret Generation:**
```python
# Generate secure secret key
import secrets
secret_key = secrets.token_urlsafe(32)
```

### 1.3 Implement Secure JWT Authentication
**Files to create/modify:**
- `backend/app/services/auth_services/jwt_service.py` (new)
- `backend/app/services/auth_services/authentication_service.py`

**New JWT Service:**
```python
# backend/app/services/auth_services/jwt_service.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings

class JWTService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
```

**Update Authentication Service:**
```python
# In authentication_service.py
from .jwt_service import JWTService

class AuthenticationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_service = JWTService()

    async def authenticate_user(self, login_request: LoginRequest) -> LoginResponse:
        # ... existing user validation ...
        
        # REPLACE token creation:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "client_account_id": str(user.client_account_id) if user.client_account_id else None
        }
        
        access_token = self.jwt_service.create_access_token(token_data)
        
        token = Token(
            access_token=access_token,
            token_type="bearer"
        )
```

### 1.4 Remove Demo Mode Fallbacks
**Files to modify:**
- `backend/app/api/v1/auth/auth_utils.py`

**Implementation:**
```python
# REMOVE all fallback demo user creation:
# Lines 69-93 in auth_utils.py

# REPLACE with proper error handling:
async def get_current_user(token: str, db):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # JWT token validation only
        from app.services.auth_services.jwt_service import JWTService
        jwt_service = JWTService()
        payload = jwt_service.verify_token(token)
        
        if payload is None:
            raise credentials_exception
            
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        user = await db.get(User, user_id)
        if user is None:
            raise credentials_exception
            
        return user
        
    except Exception:
        raise credentials_exception
```

### 1.5 Secure Token Storage
**Files to modify:**
- `src/contexts/AuthContext/storage.ts`
- `backend/app/core/config.py` (add cookie settings)

**Backend Cookie Configuration:**
```python
# Add to config.py
COOKIE_SECURE: bool = Field(default=True, env="COOKIE_SECURE")  # True for HTTPS
COOKIE_SAMESITE: str = Field(default="lax", env="COOKIE_SAMESITE")
COOKIE_HTTPONLY: bool = Field(default=True, env="COOKIE_HTTPONLY")
```

**Frontend Storage Changes:**
```typescript
// Replace localStorage with secure cookie handling
// src/contexts/AuthContext/storage.ts

// REMOVE localStorage usage:
export const tokenStorage: TokenStorage = {
  getToken: () => null, // Tokens now handled via httpOnly cookies
  setToken: (token) => {
    // Token setting handled by backend via Set-Cookie header
    console.log("Token storage now managed by secure cookies");
  },
  removeToken: () => {
    // Token removal handled by backend
    fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });
  }
};
```

---

## ⚠️ Phase 2: High-Risk Vulnerabilities

### 2.1 Implement Rate Limiting
**Files to create/modify:**
- `backend/app/middleware/rate_limiter.py` (new)
- `backend/main.py`

**Rate Limiting Implementation:**
```python
# backend/app/middleware/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Add to main.py
from app.middleware.rate_limiter import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add to auth endpoints
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
```

### 2.2 Add Security Headers
**Files to modify:**
- `backend/app/middleware/security_headers.py` (new)
- `backend/main.py`

**Security Headers Middleware:**
```python
# backend/app/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

# Add to main.py
app.add_middleware(SecurityHeadersMiddleware)
```

### 2.3 Strengthen Input Validation
**Files to modify:**
- `backend/app/api/v1/endpoints/data_import/field_mapping/validators/mapping_validators.py`

**Enhanced Validation:**
```python
def _validate_transformation_rule(self, rule: str) -> bool:
    """Enhanced transformation rule validation."""
    if not rule:
        return True
    
    # Strict whitelist approach
    import ast
    
    try:
        # Parse as AST to check for dangerous constructs
        tree = ast.parse(rule, mode='eval')
        
        # Check for dangerous node types
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Exec, ast.Eval)):
                return False
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in [
                    'exec', 'eval', 'compile', '__import__', 'getattr', 'setattr'
                ]:
                    return False
        
        return True
    except SyntaxError:
        return False
```

### 2.4 Fix CORS Configuration
**Files to modify:**
- `backend/main.py`

**Secure CORS Setup:**
```python
# Replace overly permissive CORS configuration
cors_origins = []

# Only add specific origins based on environment
if settings.ENVIRONMENT == "development":
    cors_origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8081"
    ])
else:
    # Production: Only specific domains
    cors_origins.extend([
        "https://aiforce-assess.vercel.app",
        "https://migrate-ui-orchestrator-production.up.railway.app"
    ])

# Add environment-specific origins
if settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Authorization", "Content-Type", "X-Client-Account-ID", "X-Engagement-ID"],
)
```

---

## 🔐 Phase 3: Security Hardening

## DO NOT IMPLEMENT 3.1 and 3.2 for now

### 3.1 Implement Session Management
**Files to create/modify:**
- `backend/app/services/auth_services/session_service.py` (new)
- `backend/app/models/user_session.py` (new)

**Session Management:**
```python
# backend/app/models/user_session.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)
```

### 3.2 Add Security Logging
**Files to create/modify:**
- `backend/app/services/security_logger.py` (new)

**Security Event Logging:**
```python
# backend/app/services/security_logger.py
import logging
from typing import Dict, Any
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
        
    def log_auth_attempt(self, email: str, success: bool, ip_address: str):
        self.logger.info(
            "Authentication attempt",
            extra={
                "event_type": "auth_attempt",
                "email": email,
                "success": success,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        self.logger.warning(
            f"Suspicious activity: {activity_type}",
            extra={
                "event_type": "suspicious_activity",
                "activity_type": activity_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

### 3.3 Implement Input Sanitization
**Files to create/modify:**
- `backend/app/utils/security_utils.py` (new)

**Input Sanitization:**
```python
# backend/app/utils/security_utils.py
import re
import html
from typing import Any, Dict

class InputSanitizer:
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input to prevent XSS."""
        if not value:
            return value
        
        # HTML escape
        value = html.escape(value)
        
        # Remove potentially dangerous patterns
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'vbscript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputSanitizer.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
```

### 3.4 Database Security Hardening
**Files to modify:**
- `backend/app/core/database.py`

**Database Security:**
```python
# Add connection pool security
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=False,  # Disable SQL echo in production
    connect_args={
        "server_settings": {
            "application_name": "aiforce-migration-platform",
            "client_encoding": "utf8",
        }
    }
)
```

---

## 🧪 Testing & Validation

### Security Testing Implementation
**Files to create:**
- `backend/tests/security/test_authentication.py`
- `backend/tests/security/test_authorization.py`
- `backend/tests/security/test_input_validation.py`

**Example Security Test:**
```python
# backend/tests/security/test_authentication.py
import pytest
from app.services.auth_services.jwt_service import JWTService

def test_jwt_token_expiration():
    jwt_service = JWTService()
    
    # Test token creation and validation
    token = jwt_service.create_access_token({"sub": "test_user"})
    assert token is not None
    
    # Test token validation
    payload = jwt_service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test_user"
    
    # Test invalid token
    invalid_payload = jwt_service.verify_token("invalid_token")
    assert invalid_payload is None
```

### Security Checklist
- [ ] All hardcoded credentials removed
- [ ] JWT authentication implemented
- [ ] Rate limiting active
- [ ] Security headers configured
- [ ] Input validation strengthened
- [ ] CORS properly configured
- [ ] Session management implemented
- [ ] Security logging active
- [ ] Database connections secured
- [ ] All tests passing

---

## 🚀 Deployment Considerations

### Environment Variables Required
```bash
# Critical security variables
SECRET_KEY=your_32_character_secret_key_here
DEEPINFRA_API_KEY=your_deepinfra_api_key
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_HTTPONLY=true

# Database security
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require

# CORS configuration
FRONTEND_URL=https://your-frontend-domain.com
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### Railway Deployment
```bash
# Set all environment variables
railway variables set SECRET_KEY=your_secret_key
railway variables set DEEPINFRA_API_KEY=your_api_key
railway variables set COOKIE_SECURE=true
railway variables set ENVIRONMENT=production
```

### Monitoring & Alerts
- Set up log monitoring for security events
- Configure alerts for failed authentication attempts
- Monitor for suspicious API usage patterns
- Regular security scanning

---

## 📅 Implementation Timeline

### Week 1: Critical Fixes
- **Day 1-2:** Remove hardcoded credentials, implement JWT
- **Day 3-4:** Remove demo mode fallbacks, secure token storage
- **Day 5-7:** Testing and validation

### Week 2: High-Risk Fixes
- **Day 1-2:** Implement rate limiting and security headers
- **Day 3-4:** Strengthen input validation, fix CORS
- **Day 5-7:** Testing and integration

### Week 3-4: Security Hardening
- **Day 1-5:** Session management, security logging
- **Day 6-10:** Input sanitization, database security
- **Day 11-14:** Comprehensive testing and deployment

---

## 🔍 Success Metrics

### Security Improvements
- **Zero hardcoded credentials** in codebase
- **JWT-based authentication** with proper expiration
- **Rate limiting** preventing abuse
- **Security headers** protecting against common attacks
- **Input validation** preventing injection attacks

### Monitoring KPIs
- Authentication failure rate < 5%
- Zero successful brute force attempts
- All security headers present in responses
- Input validation blocking 100% of malicious inputs

---

## 📝 Conclusion

This comprehensive security remediation plan addresses all critical vulnerabilities identified in the security assessment. Implementation must follow the phased approach to ensure system stability while dramatically improving security posture.

**Next Steps:**
1. Begin Phase 1 implementation immediately
2. Set up monitoring and alerting
3. Conduct security testing after each phase
4. Perform final security audit before production deployment

---

**Plan Created By:** Security Assessment Team  
**Implementation Owner:** Development Team  
**Review Date:** After completion of each phase  
**Status:** READY FOR IMPLEMENTATION