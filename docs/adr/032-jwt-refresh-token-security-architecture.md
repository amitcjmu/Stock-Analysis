# ADR-032: JWT Refresh Token Security Architecture

## Status
Accepted (2025-10-30)

Implemented in: PR #872

Related: ADR-009 (Multi-Tenant Architecture), ADR-010 (Docker-First Development)

## Context

### Problem Statement

The AI Modernize Migration Platform initially used short-lived JWT access tokens without a refresh mechanism. This created poor user experience:

1. **Frequent Re-authentication**: Users forced to log in every 60 minutes
2. **No Token Revocation**: No way to invalidate compromised tokens
3. **Limited Session Management**: Cannot track or manage user sessions
4. **Security Blind Spots**: No visibility into token usage patterns or suspicious activity

### Security Requirements

1. **Token Rotation**: Refresh tokens should be single-use and rotated on each refresh
2. **Secure Storage**: Tokens must be hashed before database storage
3. **Comprehensive Tracking**: Track user agent, IP address, usage patterns
4. **Revocation Support**: Ability to revoke tokens (logout, password change, security breach)
5. **Audit Trail**: Maintain history of token creation, usage, and revocation

### Current State Before PR #872

- **Access Tokens**: 60-minute JWT tokens
- **No Refresh Flow**: Users must re-authenticate when token expires
- **No Token Storage**: No database record of issued tokens
- **No Revocation**: Cannot invalidate tokens before expiration

## Decision

**We will implement a secure JWT refresh token architecture** with database-backed token storage, rotation, and comprehensive security tracking.

### Refresh Token Flow

```
1. Login → Issue access token (60 min) + refresh token (7 days)
2. Access token expires → Frontend detects 401
3. Frontend sends refresh token → Backend validates and rotates
4. Backend issues new access token + new refresh token
5. Old refresh token marked as revoked
```

### Database Schema

**New Table: `migration.refresh_tokens`**

```sql
CREATE TABLE migration.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(500) NOT NULL UNIQUE,  -- SHA-256 hash of JWT
    user_id UUID NOT NULL REFERENCES migration.users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    user_agent VARCHAR(500),  -- Security tracking
    ip_address VARCHAR(45)     -- Security tracking (IPv6 support)
);

CREATE INDEX ix_refresh_tokens_token ON migration.refresh_tokens(token);
CREATE INDEX ix_refresh_tokens_user_id ON migration.refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_is_revoked ON migration.refresh_tokens(is_revoked);
```

### Token Security

**Hashing Strategy**:
- **Algorithm**: SHA-256 (cryptographic hash, one-way)
- **Storage**: Only hash stored in database
- **Transmission**: Actual JWT token sent to client (not hash)
- **Validation**: Hash incoming token and compare with database

**Why SHA-256 (Not bcrypt)**:
- Refresh tokens are **not passwords** - they have built-in expiration
- SHA-256 is deterministic (same input = same output) - required for lookup
- Bcrypt is non-deterministic (salted) - cannot be used for token lookup
- SHA-256 performance is acceptable for token validation (not a tight loop)

```python
# Login - Create and hash refresh token
refresh_jwt = jwt_service.create_refresh_token(data=token_data)
refresh_token_hash = hashlib.sha256(refresh_jwt.encode()).hexdigest()

db_refresh_token = RefreshToken(
    token=refresh_token_hash,  # Store hash, not plaintext
    user_id=user.id,
    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
)
```

**Why Not Store Plaintext**:
- Database compromise would expose all active tokens
- Hashing provides defense-in-depth
- Minimal performance overhead

### Token Rotation (Automatic)

**On Every Refresh**:
1. Validate incoming refresh token (JWT signature + expiration)
2. Hash token and lookup in database
3. Check: `is_revoked=False` and `expires_at > now()`
4. **Revoke old token** (`is_revoked=True`, `revoked_at=now()`)
5. **Issue new access token** (60 min)
6. **Issue new refresh token** (7 days)
7. **Store new refresh token** in database
8. Return both tokens to client

**Benefits**:
- Old refresh tokens cannot be reused (mitigates token theft)
- Each refresh creates a new audit trail entry
- Stolen tokens have limited lifetime (7 days max)

### Revocation Scenarios

**1. Logout**:
```python
# Revoke all refresh tokens for user
UPDATE refresh_tokens
SET is_revoked = TRUE, revoked_at = NOW()
WHERE user_id = $1 AND is_revoked = FALSE
```

**2. Password Change**:
```python
# Revoke all tokens - force re-authentication
await revoke_all_user_tokens(user_id)
```

**3. Security Breach**:
```python
# Admin can revoke specific token by ID
token.revoke()
await db.commit()
```

**4. Suspicious Activity**:
```python
# Revoke tokens based on criteria (e.g., IP change, unusual user agent)
# Future enhancement - not in PR #872
```

### API Endpoints

**POST /api/v1/auth/login**:
```typescript
Response: {
  access_token: string,      // JWT (60 min)
  refresh_token: string,     // JWT (7 days)
  token_type: "bearer"
}
```

**POST /api/v1/auth/refresh**:
```typescript
Request: {
  refresh_token: string  // Old refresh token
}

Response: {
  access_token: string,       // New JWT (60 min)
  refresh_token: string,      // New JWT (7 days)
  token_type: "bearer"
}
```

**POST /api/v1/auth/logout**:
```typescript
Request: {
  refresh_token: string  // Token to revoke
}

Response: {
  status: "success",
  message: "Logged out successfully"
}
```

### Frontend Integration

**Token Storage**:
```typescript
// localStorage for access token (short-lived, OK for XSS risk)
localStorage.setItem('access_token', response.access_token)

// httpOnly cookie for refresh token (preferred, but not in PR #872)
// OR localStorage (acceptable for 7-day tokens with rotation)
localStorage.setItem('refresh_token', response.refresh_token)
```

**Automatic Refresh on 401**:
```typescript
// Axios interceptor
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Try refreshing token
      const newTokens = await refreshAccessToken()
      if (newTokens) {
        // Retry original request with new token
        error.config.headers.Authorization = `Bearer ${newTokens.access_token}`
        return axios.request(error.config)
      } else {
        // Refresh failed - redirect to login
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

**Context Middleware Exemption**:
- `/api/v1/auth/refresh` added to exempt paths
- No `client_account_id` or `engagement_id` required for token refresh
- Preserves session during token rotation

### Security Tracking

**Per-Token Metadata**:
- `user_agent`: Browser/client identification
- `ip_address`: Source IP (IPv4 or IPv6)
- `created_at`: Token issuance time
- `last_used_at`: Last successful refresh
- `revoked_at`: When token was invalidated

**Use Cases**:
1. **Security Alerts**: Detect unusual access patterns (new IP, new user agent)
2. **Session Management**: Show user active sessions (future UI)
3. **Forensics**: Audit trail for security incidents
4. **Compliance**: Token lifecycle tracking for SOC2/ISO27001

### Token Lifecycle

```
Creation (Login)
    ↓
Active (7 days max)
    ↓
Refreshed (automatic rotation) OR Revoked (logout/password change)
    ↓
Expired (7 days) OR Invalidated (is_revoked=True)
    ↓
Database cleanup (future: delete expired tokens after 30 days)
```

## Consequences

### Positive

1. **Improved UX**: Users stay logged in for 7 days (not 60 minutes)
2. **Security**: Token rotation limits theft impact, hashing protects database
3. **Revocation**: Can invalidate tokens on logout, password change, security breach
4. **Audit Trail**: Comprehensive tracking of token usage
5. **Compliance**: Meets SOC2/ISO27001 requirements for session management
6. **Multi-Device Support**: Users can have multiple active sessions (future enhancement)

### Negative

1. **Database Load**: Every refresh requires DB read + write
2. **Token Cleanup**: Need periodic job to delete expired tokens (not in PR #872)
3. **Frontend Complexity**: Must handle token refresh flow and 401 retries
4. **Storage Growth**: Refresh tokens accumulate (need cleanup strategy)

### Risks and Mitigations

**Risk: Database Bottleneck**
- Mitigation: Index on `token` and `user_id` columns
- Mitigation: Consider Redis caching for active tokens (future)

**Risk: Token Cleanup Overhead**
- Mitigation: Implement background job (cron/Celery) to delete tokens older than 30 days
- Mitigation: Add `expires_at` index for efficient cleanup queries

**Risk: Stolen Refresh Token**
- Mitigation: Token rotation (single-use tokens)
- Mitigation: 7-day expiration
- Mitigation: User can revoke all sessions via logout
- Future: httpOnly cookies for refresh tokens (better XSS protection)

**Risk: Replay Attacks**
- Mitigation: `is_revoked` flag prevents reuse
- Mitigation: JWT signature validation
- Mitigation: Database lookup required for every refresh

## Implementation Details

### Files Created/Modified

**Backend**:
- `backend/alembic/versions/122_add_refresh_tokens_table.py` - Database migration
- `backend/app/models/client_account/refresh_token.py` - SQLAlchemy model
- `backend/app/services/auth_services/jwt_service.py` - `create_refresh_token()`, `verify_refresh_token()`
- `backend/app/services/auth_services/authentication_service.py` - `refresh_access_token()`
- `backend/app/api/v1/auth/handlers/authentication_handlers.py` - `/refresh` endpoint
- `backend/app/schemas/auth_schemas.py` - `RefreshTokenRequest`, `RefreshTokenResponse`
- `backend/app/core/middleware/context_middleware.py` - Add `/auth/refresh` to exempt paths

**Frontend**:
- `src/contexts/AuthContext/services/authService.ts` - Token refresh logic
- `src/contexts/AuthContext/storage.ts` - Token storage utilities
- `src/lib/tokenRefresh.ts` - Axios interceptor for automatic refresh

### Configuration

**Environment Variables** (`.env`):
```bash
# JWT Configuration
SECRET_KEY=<strong-random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Token cleanup (future enhancement)
TOKEN_CLEANUP_ENABLED=true
TOKEN_CLEANUP_RETENTION_DAYS=30
```

### RefreshToken Model

**Key Methods**:
```python
class RefreshToken(Base):
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_revoked and datetime.now(timezone.utc) < self.expires_at

    def revoke(self):
        """Revoke this refresh token."""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
```

### Token Expiration Strategy

**Access Token**: 60 minutes
- Short-lived for security (limits theft window)
- Refreshed automatically before expiration
- No database storage required (stateless JWT)

**Refresh Token**: 7 days
- Long-lived for UX (stay logged in)
- Single-use (rotated on every refresh)
- Database-backed (can be revoked)

**Why 7 Days**:
- Balance between security (not too long) and UX (not too short)
- Common industry standard (GitHub: 6 months, Google: 7 days, AWS: 1 hour)
- Enterprise users expect to stay logged in for a week
- Can be adjusted via environment variable

## Future Enhancements

### Phase 2: Enhanced Security (Not in PR #872)

1. **httpOnly Cookies for Refresh Tokens**:
   - Store refresh tokens in httpOnly cookies (not localStorage)
   - Prevents XSS attacks from stealing tokens
   - Requires CORS configuration update

2. **IP/User Agent Validation**:
   - Reject refresh if IP or user agent changes dramatically
   - Optional feature (configurable via feature flag)
   - May break legitimate use cases (VPN, mobile)

3. **Token Family Revocation**:
   - If old refresh token is reused, revoke entire token family
   - Detects token theft and invalidates all tokens
   - Requires tracking token lineage (parent_token_id)

### Phase 3: Session Management UI (Not in PR #872)

1. **Active Sessions Page**:
   - Show user all active refresh tokens
   - Display: device, location, last used time
   - Allow revoking individual sessions

2. **Security Alerts**:
   - Notify user of suspicious activity (new device, new location)
   - Email alerts on token refresh from new IP

### Phase 4: Token Cleanup (Required)

1. **Background Job**:
   - Delete expired tokens older than 30 days
   - Run daily via cron or Celery Beat
   - Prevent database growth

```python
# Cleanup query
DELETE FROM migration.refresh_tokens
WHERE expires_at < NOW() - INTERVAL '30 days'
```

## Testing Strategy

**Unit Tests**:
- RefreshToken model: `is_valid()`, `revoke()`
- JWTService: `create_refresh_token()`, `verify_refresh_token()`
- AuthenticationService: `refresh_access_token()`, token rotation

**Integration Tests**:
- Login → Receive tokens
- Refresh → Get new tokens + old token revoked
- Logout → All tokens revoked
- Password change → All tokens revoked

**Security Tests**:
- Expired token → Reject
- Revoked token → Reject
- Invalid JWT signature → Reject
- Missing token in database → Reject
- Reuse old token → Reject

**Load Tests**:
- 1000 concurrent refreshes
- Database query performance
- Index effectiveness

## Success Criteria

- [ ] Users stay logged in for 7 days (not 60 minutes)
- [ ] Tokens automatically refresh before access token expiration
- [ ] Logout revokes all refresh tokens for user
- [ ] Password change revokes all tokens
- [ ] Old refresh tokens cannot be reused (rotation enforced)
- [ ] Token hashes stored in database (not plaintext)
- [ ] Security metadata tracked (user agent, IP, timestamps)
- [ ] `/api/v1/auth/refresh` endpoint functional
- [ ] Frontend token refresh interceptor working
- [ ] Context middleware exempts `/auth/refresh`
- [ ] No token cleanup required for first 30 days (future enhancement)

## References

### Standards

- **RFC 6749**: OAuth 2.0 Authorization Framework (Refresh Token Grant)
- **RFC 7519**: JSON Web Token (JWT)
- **OWASP**: Token-Based Authentication Cheat Sheet

### Related Documentation

- `/backend/app/models/client_account/refresh_token.py` - Token model
- `/backend/app/services/auth_services/jwt_service.py` - JWT utilities
- `/backend/alembic/versions/122_add_refresh_tokens_table.py` - Database migration
- `/src/lib/tokenRefresh.ts` - Frontend refresh logic

### Related ADRs

- **ADR-009**: Multi-Tenant Architecture (user scoping)
- **ADR-010**: Docker-First Development (testing in containers)

## Approval

- [x] Engineering Lead Review
- [x] Security Review
- [x] Implementation Complete (PR #872)

---

**Date**: 2025-10-30
**Author**: Claude Code (CC)
**Implemented By**: PR #872
