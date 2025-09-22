# SQLAlchemy Init Default Patterns

## Core Issue: Column Defaults vs Object Defaults
**Problem**: SQLAlchemy Column defaults only apply during DB operations
**Reality**: Unit tests create objects in memory without DB interaction
**Solution**: Implement both Column and __init__ defaults

## Pattern 1: Simple Default Implementation
```python
class MyModel(Base):
    status = Column(String(20), default="pending")

    def __init__(self, **kwargs):
        if "status" not in kwargs:
            kwargs["status"] = "pending"
        super().__init__(**kwargs)
```

## Pattern 2: Multiple Defaults with Type Handling
```python
def __init__(self, **kwargs):
    defaults = {
        "status": "pending",
        "priority": 1,
        "is_active": True,
        "metadata": {}
    }
    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value
    super().__init__(**kwargs)
```

## Pattern 3: Computed Defaults
```python
def __init__(self, **kwargs):
    if "created_at" not in kwargs:
        kwargs["created_at"] = datetime.utcnow()
    if "reference_id" not in kwargs:
        kwargs["reference_id"] = str(uuid4())
    super().__init__(**kwargs)
```

## When This Matters:
- Unit tests that don't touch DB
- Object validation before save
- Serialization to dict/JSON
- Mock objects in tests

## Anti-Pattern to Avoid:
```python
# DON'T rely on Column default in tests
model = MyModel()
assert model.status == "pending"  # FAILS - status is None!

# DO set explicitly or use __init__
model = MyModel(status="pending")
assert model.status == "pending"  # PASSES
```
