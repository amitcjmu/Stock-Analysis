# RBAC Microsoft Entra Integration Guide

## Overview

The AI Force Migration Platform's Role-Based Access Control (RBAC) system is designed with enterprise SSO integration in mind, particularly Microsoft Entra (formerly Azure AD). This document outlines the current architecture and the path to Entra integration.

## Current RBAC Architecture

### Core Components

1. **User Profile System** (`UserProfile` model)
   - Extended user information with approval workflow
   - Status tracking (pending, active, suspended)
   - Contact and verification details
   - Notification preferences

2. **Role Management** (`UserRole` model)
   - Multiple roles per user across different contexts
   - Permission-based access control
   - Scope-based roles (global, client, engagement)
   - Role expiration and lifecycle management

3. **Access Control** (`ClientAccess`, `EngagementAccess` models)
   - Granular permissions at client and engagement levels
   - Usage tracking and access restrictions
   - Time-based access expiration

4. **Audit Trail** (`AccessAuditLog` model)
   - Complete audit logging for compliance
   - IP tracking and user agent logging
   - Action and result tracking

## Microsoft Entra Integration Path

### Phase 1: Authentication Layer (Immediate)

#### Current Demo Authentication
```typescript
// Current login function in AuthContext
const login = async (email: string, password: string) => {
  // Demo authentication logic
}
```

#### Entra Integration
```typescript
// Updated login function for Entra
const login = async () => {
  try {
    // Use MSAL (Microsoft Authentication Library)
    const loginRequest = {
      scopes: ["openid", "profile", "email", "User.Read"],
      redirectUri: "http://localhost:3000/auth/callback"
    };
    
    const response = await msalInstance.loginPopup(loginRequest);
    
    // Extract user information from Entra
    const userInfo = {
      id: response.account.homeAccountId,
      email: response.account.username,
      full_name: response.account.name,
      roles: response.account.idTokenClaims?.roles || []
    };
    
    // Register/update user in our system
    await registerEntraUser(userInfo);
    
  } catch (error) {
    console.error("Entra login failed:", error);
  }
};
```

### Phase 2: User Provisioning (Short-term)

#### Automatic User Registration
```python
# Backend endpoint for Entra user registration
@router.post("/auth/entra/provision")
async def provision_entra_user(user_data: EntraUserData):
    """
    Automatically provision users from Microsoft Entra.
    Maps Entra roles to platform roles.
    """
    # Extract user information from Entra token
    user_profile = {
        "user_id": user_data.oid,  # Entra Object ID
        "email": user_data.email,
        "full_name": user_data.name,
        "organization": user_data.organization_name,
        "role_description": map_entra_role(user_data.roles),
        "status": "active",  # Auto-approve Entra users
        "registration_reason": "Microsoft Entra SSO Integration"
    }
    
    return await rbac_service.register_entra_user(user_profile)
```

#### Role Mapping Configuration
```python
# Role mapping from Entra groups to platform roles
ENTRA_ROLE_MAPPING = {
    "Migration_Administrators": {
        "platform_role": "admin",
        "access_level": "admin",
        "permissions": {
            "can_access_admin_console": True,
            "can_manage_users": True,
            "can_manage_engagements": True
        }
    },
    "Migration_Analysts": {
        "platform_role": "analyst",
        "access_level": "read_write",
        "permissions": {
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True
        }
    },
    "Migration_Viewers": {
        "platform_role": "viewer",
        "access_level": "read_only",
        "permissions": {
            "can_view_data": True,
            "can_view_analytics": True
        }
    }
}
```

### Phase 3: Advanced Integration (Medium-term)

#### Group-Based Access Control
```python
# Automatically sync Entra groups to client access
@router.post("/auth/entra/sync-groups")
async def sync_entra_groups():
    """
    Sync Microsoft Entra groups to client access permissions.
    E.g., "TechCorp_Migration_Team" → Access to TechCorp client
    """
    for group in entra_groups:
        if group.name.endswith("_Migration_Team"):
            client_name = group.name.replace("_Migration_Team", "")
            await grant_client_access_by_group(group.members, client_name)
```

#### Conditional Access Integration
```python
# Support for Entra Conditional Access policies
class EntraConditionalAccess:
    def validate_access(self, user: EntraUser, resource: str, context: dict):
        """
        Validate access based on Entra Conditional Access policies.
        - Device compliance
        - Location-based access
        - Risk-based authentication
        """
        if not user.device_compliant:
            return {"access": False, "reason": "Device not compliant"}
            
        if resource == "admin_console" and user.risk_level == "high":
            return {"access": False, "reason": "High risk user"}
            
        return {"access": True}
```

## Implementation Steps

### Step 1: Install MSAL Dependencies
```bash
# Frontend
npm install @azure/msal-browser @azure/msal-react

# Backend
pip install msal fastapi-azure-auth
```

### Step 2: Configure Entra Application
1. Register application in Azure Portal
2. Configure redirect URIs
3. Set API permissions (User.Read, Group.Read.All)
4. Create app roles for migration platform

### Step 3: Update Authentication Context
```typescript
// src/contexts/AuthContext.tsx
import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: process.env.REACT_APP_ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_TENANT_ID}`,
    redirectUri: window.location.origin
  }
};

const msalInstance = new PublicClientApplication(msalConfig);
```

### Step 4: Update Backend Authentication
```python
# backend/app/core/auth.py
from fastapi_azure_auth import SingleTenantAzureAuth

azure_auth = SingleTenantAzureAuth(
    tenant_id=os.getenv("AZURE_TENANT_ID"),
    client_id=os.getenv("AZURE_CLIENT_ID"),
    scopes=["User.Read"]
)

@app.middleware("http")
async def azure_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        try:
            user = await azure_auth.authenticate(request)
            request.state.user = user
        except Exception as e:
            # Handle authentication failure
            pass
    
    return await call_next(request)
```

## Security Considerations

### Token Management
- Store tokens securely in HTTP-only cookies
- Implement token refresh logic
- Handle token expiration gracefully

### Permission Sync
- Regular sync of Entra groups to platform permissions
- Handle permission changes in real-time
- Audit permission changes

### Data Protection
- Ensure GDPR compliance with Entra user data
- Implement data retention policies
- Handle user deletion from Entra

## Testing Strategy

### Development Environment
```yaml
# docker-compose.yml
services:
  mock-entra:
    image: microsoft/mock-azure-ad
    environment:
      - TENANT_ID=dev-tenant
      - CLIENT_ID=dev-client-id
```

### Test Scenarios
1. **User Provisioning**: Test automatic user creation from Entra
2. **Role Mapping**: Verify Entra groups map to correct platform roles
3. **Permission Sync**: Test real-time permission updates
4. **Token Refresh**: Verify seamless token renewal
5. **Fallback**: Test behavior when Entra is unavailable

## Migration from Demo to Production

### Phase 1: Dual Authentication
- Support both demo credentials and Entra
- Gradual migration of admin users
- Maintain backward compatibility

### Phase 2: Entra-Only
- Disable demo authentication
- Enforce Entra authentication for all users
- Update documentation and training

### Phase 3: Enterprise Features
- Advanced group management
- Conditional access policies
- Advanced audit and compliance

## Monitoring and Metrics

### Key Metrics
- Authentication success/failure rates
- Token refresh frequency
- Permission sync latency
- User provisioning time

### Alerts
- Failed authentication spikes
- Permission sync failures
- Token expiration issues
- Unauthorized access attempts

## Compliance and Audit

### Audit Requirements
- Log all authentication events
- Track permission changes
- Monitor privileged access
- Generate compliance reports

### RBAC Audit Trail
The existing `AccessAuditLog` model already supports enterprise audit requirements:
- User identification (Entra Object ID)
- Action tracking with timestamps
- IP address and user agent logging
- Resource access tracking
- Permission change auditing

## Conclusion

The current RBAC system provides a solid foundation for Microsoft Entra integration. The modular design allows for gradual migration from demo authentication to full enterprise SSO while maintaining security and audit requirements.

Key benefits of the integration:
1. **Seamless SSO**: Users authenticate once with corporate credentials
2. **Automated Provisioning**: Reduce manual user management overhead
3. **Enhanced Security**: Leverage Entra's advanced security features
4. **Compliance**: Meet enterprise audit and compliance requirements
5. **Scalability**: Support large enterprise user bases

The implementation can be done incrementally, allowing for testing and validation at each phase while maintaining system availability and user experience. 