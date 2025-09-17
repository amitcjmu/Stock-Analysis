# Modularization Patterns and Critical Fixes

## Pattern 1: Enterprise File Modularization (>400 lines)
**Problem**: Files exceeding 400-line limit block pre-commit hooks
**Solution**: Create directory structure with domain-specific modules
**Code Structure**:
```python
# Transform: original_file.py → original_file/
original_file/
├── __init__.py       # Backward compatibility imports
├── base.py          # Base classes/shared utilities  
├── config.py        # Configuration
├── service.py       # Main service logic
└── domain_modules/  # Domain-specific logic
```
**Key**: Always delete original monolithic file after modularization

## Fix 1: O(n) to O(1) Performance Optimization
**Problem**: InMemoryFallbackCache using deque for access tracking
**Solution**: Replace with dict-based tracking
```python
# Before: O(n) lookup
self.access_order = deque()
self.cache[key] = value
self.access_order.remove(key)  # O(n)
self.access_order.append(key)

# After: O(1) lookup
self.access_order: Dict[str, None] = {}
self.access_counter = 0
self.cache[key] = (value, self.access_counter)
self.access_order[key] = None
```

## Fix 2: Proper IP Validation in Dependencies
**Problem**: Regex matching invalid IPs like 999.999.999.999
**Solution**: Use ipaddress library
```python
import ipaddress

potential_ips = re.findall(ip_pattern, config_text)
for ip in potential_ips:
    try:
        ipaddress.ip_address(ip)  # Validates IP
        connections.append({...})
    except ValueError:
        continue  # Skip invalid
```

## Fix 3: Question Generation Loop Break
**Problem**: Only generating first matching question per gap
**Solution**: Remove break, track used templates
```python
added_templates_for_gap = set()
for template_key, template in question_templates.items():
    if template_key not in added_templates_for_gap and (...):
        questions.append(question)
        added_templates_for_gap.add(template_key)
        # No break - generates all relevant questions
```

## Fix 4: Missing SQLAlchemy Imports
**Problem**: PostgresUUID import missing after modularization
**Solution**: Add proper imports to base.py
```python
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid
```

## Critical Docker Commands
```bash
# Rebuild with proper timeout (10 min)
docker-compose -f docker-compose.dev.yml build --no-cache
timeout: 600000

# Free disk space when build fails
docker system prune -a
```