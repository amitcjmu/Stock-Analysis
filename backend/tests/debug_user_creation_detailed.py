import asyncio
import traceback
from app.core.database import AsyncSessionLocal
from app.services.rbac_service import create_rbac_service
from app.schemas.auth_schemas import UserRegistrationResponse

async def debug_user_creation():
    print('=== Debugging User Creation with Detailed Error Tracking ===')
    
    async with AsyncSessionLocal() as db:
        rbac = create_rbac_service(db)
        
        print('\n1. Testing RBAC service creation...')
        status = rbac.get_service_status()
        print(f'Service Status: {status}')
        
        print('\n2. Testing raw admin_create_user...')
        user_data = {
            'email': 'test.debug@example.com',
            'full_name': 'Test Debug User',
            'organization': 'Debug Organization',
            'role_description': 'Debug Role',
            'access_level': 'analyst'
        }
        
        try:
            result = await rbac.admin_create_user(user_data, 'admin_user')
            print(f'RBAC Result: {result}')
            print(f'Result Type: {type(result)}')
            print(f'Result Keys: {list(result.keys()) if isinstance(result, dict) else "Not a dict"}')
            
            print('\n3. Testing UserRegistrationResponse construction...')
            try:
                response = UserRegistrationResponse(**result)
                print(f'Schema validation SUCCESS: {response}')
            except Exception as schema_error:
                print(f'Schema validation ERROR: {schema_error}')
                print(f'Schema error type: {type(schema_error)}')
                print('\n4. Checking required fields for UserRegistrationResponse...')
                
                # Check what fields are required
                from app.schemas.auth_schemas import UserRegistrationResponse
                schema_fields = UserRegistrationResponse.__fields__
                print(f'Required schema fields: {schema_fields}')
                
                # Try to create with minimal fields
                minimal_result = {
                    "status": result.get("status", "success"),
                    "message": result.get("message", "User created"),
                    "user_profile_id": result.get("user_profile_id"),
                    "approval_status": result.get("approval_status", "active")
                }
                print(f'Trying minimal result: {minimal_result}')
                
                try:
                    minimal_response = UserRegistrationResponse(**minimal_result)
                    print(f'Minimal schema validation SUCCESS: {minimal_response}')
                except Exception as minimal_error:
                    print(f'Minimal schema validation ERROR: {minimal_error}')
                    print(f'Traceback: {traceback.format_exc()}')
                
        except Exception as e:
            print(f'RBAC Error: {e}')
            print(f'Error Type: {type(e)}')
            print(f'Traceback: {traceback.format_exc()}')

if __name__ == "__main__":
    asyncio.run(debug_user_creation()) 