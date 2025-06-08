import traceback

print("Attempting to import API routes for debugging...")

try:
    from app.api.v1.api import api_router
    print("✅ Successfully imported api_router.")
except Exception as e:
    print("\n❌ FAILED to import api_router.")
    print("\n📋 Traceback:")
    traceback.print_exc() 