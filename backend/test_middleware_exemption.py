#!/usr/bin/env python3
"""Test script to debug middleware exemption logic"""

from app.core.middleware import ContextMiddleware

# Test context middleware exemption logic
middleware = ContextMiddleware(None, require_client=True, require_engagement=True, additional_exempt_paths=[
    '/api/v1/context/clients',
    '/api/v1/context/engagements',
    '/api/v1/context-establishment/clients',
    '/api/v1/context-establishment/engagements'
])

print('Middleware exempt paths:')
for path in middleware.exempt_paths:
    print(f'  {path}')

# Test various paths
test_paths = [
    '/api/v1/context/clients',
    '/api/v1/context/engagements', 
    '/api/v1/context-establishment/clients',
    '/api/v1/context-establishment/engagements',
    '/api/v1/health',
    '/api/v1/auth/login',
    '/api/v1/data-import/status'
]

print()
print('Path exemption test:')
for path in test_paths:
    # Check if path is exempt
    is_exempt = False
    for exempt_path in middleware.exempt_paths:
        if exempt_path == '/' and path == '/':
            is_exempt = True
            break
        elif exempt_path != '/' and path.startswith(exempt_path):
            is_exempt = True
            break
    
    print(f'{path}: exempt={is_exempt}')

# Test specific case from logs
problem_path = '/api/v1/context/clients'
print(f'\nSpecific test for {problem_path}:')
for i, exempt_path in enumerate(middleware.exempt_paths):
    if exempt_path == '/' and problem_path == '/':
        print(f'  Rule {i}: Root path match - {exempt_path} == {problem_path} -> True')
    elif exempt_path != '/' and problem_path.startswith(exempt_path):
        print(f'  Rule {i}: Prefix match - {problem_path}.startswith({exempt_path}) -> True')
    else:
        print(f'  Rule {i}: No match - {exempt_path} vs {problem_path}')