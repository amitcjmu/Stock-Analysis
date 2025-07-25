# Deployment Flexibility Infrastructure

This module provides abstractions for supporting multiple deployment modes (Development, On-Premises, SaaS, Hybrid) with graceful fallbacks and zero-dependency local development.

## Architecture Overview

```
infrastructure/
├── credentials/          # Credential management abstraction
│   ├── interface.py     # CredentialManager interface
│   └── implementations.py # Cloud KMS and Local implementations
├── telemetry/           # Telemetry abstraction
│   ├── interface.py     # TelemetryService interface
│   └── implementations.py # Cloud and NoOp implementations
├── authentication/      # Authentication abstraction
│   ├── interface.py     # AuthenticationBackend interface
│   └── implementations.py # Database and SSO implementations
└── deployment/          # Deployment configuration
    ├── config.py        # Deployment modes and configuration
    ├── detector.py      # Service availability detection
    ├── factory.py       # Service factory with fallbacks
    └── noop_services.py # No-operation service implementations
```

## Deployment Modes

### Development Mode
- Uses local credential storage
- No telemetry collection (NoOp)
- Database-based authentication
- Mock external services
- Zero external dependencies

### On-Premises Mode
- Local credential storage with encryption
- Optional telemetry (disabled by default)
- Database authentication
- No external API calls
- Fully isolated deployment

### SaaS Mode
- Cloud KMS for credentials
- Full telemetry to cloud service
- SSO authentication support
- External API integrations enabled
- Cloud-native features

### Hybrid Mode
- Configurable mix of cloud and local services
- Selective feature enablement
- Fallback support for all services
- Environment-based configuration

## Usage

### Basic Usage

```python
from app.infrastructure import get_service_factory

# Get service factory
factory = get_service_factory()

# Get services based on deployment configuration
credential_manager = await factory.get_credential_manager()
telemetry_service = await factory.get_telemetry_service()
auth_backend = await factory.get_auth_backend()
```

### Storing and Retrieving Credentials

```python
# Store a credential
await credential_manager.set_credential(
    key="api_key",
    value="secret_value",
    namespace="external_service"
)

# Retrieve a credential
api_key = await credential_manager.get_credential(
    key="api_key",
    namespace="external_service"
)
```

### Recording Telemetry

```python
# Record a metric
await telemetry_service.record_metric(
    name="api_calls",
    value=1.0,
    metric_type=MetricType.COUNTER,
    tags={"service": "external_api"}
)

# Record an event
await telemetry_service.record_event(
    event_name="user_action",
    properties={"action": "create_asset", "user_id": "123"}
)

# Record an error
try:
    # Some operation
    pass
except Exception as e:
    await telemetry_service.record_error(
        error=e,
        context={"operation": "asset_processing"}
    )
```

### Authentication

```python
# Authenticate a user
user = await auth_backend.authenticate(
    username="user@example.com",
    password="password"  # For database auth
    # OR
    token="sso_token"    # For SSO auth
)

# Create a session
session_token = await auth_backend.create_session(
    user_id=user["id"],
    metadata={"ip": "192.168.1.1"}
)
```

## Configuration

### Environment Variables

```bash
# Deployment mode
DEPLOYMENT_MODE=development  # development, on_premises, saas, hybrid

# Service overrides
CREDENTIAL_SERVICE=local     # cloud_kms, local
TELEMETRY_SERVICE=noop       # cloud, noop
AUTH_SERVICE=database        # database, sso

# Feature flags
ENABLE_CLOUD_KMS=false
ENABLE_SSO=false
ENABLE_TELEMETRY=false
ENABLE_EXTERNAL_API=false

# Service endpoints (for SaaS/Hybrid)
KMS_ENDPOINT=https://kms.example.com
KMS_API_KEY=your_api_key
TELEMETRY_ENDPOINT=https://telemetry.example.com
TELEMETRY_API_KEY=your_api_key
SSO_CLIENT_ID=your_client_id
SSO_CLIENT_SECRET=your_client_secret
```

### Docker Compose Profiles

```bash
# Development mode
docker-compose --profile development up

# On-premises mode
docker-compose --profile on-premises up

# SaaS mode
docker-compose --profile saas up

# Hybrid mode
docker-compose --profile hybrid up
```

## Service Fallbacks

All services support automatic fallback when the primary implementation is unavailable:

1. **Credentials**: Cloud KMS → Local Storage → Environment Variables
2. **Telemetry**: Cloud Service → NoOp (local logging only)
3. **Authentication**: SSO → Database → Local Cache
4. **External APIs**: Production → Mock → NoOp

## Health Checks

```python
# Check individual service health
is_healthy = await credential_manager.health_check()

# Check all services
factory = get_service_factory()
health_status = await factory.health_check()
# Returns: {"credentials": True, "telemetry": True, ...}
```

## Adding New Services

1. Create an interface in the appropriate module
2. Implement concrete classes (Cloud, Local, NoOp)
3. Register in the service factory
4. Add configuration options
5. Update Docker Compose profiles

Example:

```python
# 1. Create interface
class MyService(ABC):
    @abstractmethod
    async def do_something(self) -> str:
        pass

# 2. Implement variations
class CloudMyService(MyService):
    async def do_something(self) -> str:
        return "cloud implementation"

class NoOpMyService(MyService):
    async def do_something(self) -> str:
        return "noop implementation"

# 3. Register in factory
self._service_registry["my_service"] = {
    "cloud": CloudMyService,
    "noop": NoOpMyService
}
```

## Best Practices

1. **Always use the factory**: Don't instantiate services directly
2. **Handle failures gracefully**: Services may not be available
3. **Log important operations**: Especially in NoOp implementations
4. **Test all deployment modes**: Ensure fallbacks work correctly
5. **Keep NoOp implementations simple**: They should not depend on external resources
6. **Use appropriate fallbacks**: Choose fallbacks that maintain functionality

## Testing

```python
# Test with different deployment modes
import os

# Test development mode
os.environ["DEPLOYMENT_MODE"] = "development"
factory = get_service_factory()
# ... run tests

# Test SaaS mode with fallbacks
os.environ["DEPLOYMENT_MODE"] = "saas"
os.environ["KMS_ENDPOINT"] = ""  # Force fallback
factory = get_service_factory()
# ... run tests
```
