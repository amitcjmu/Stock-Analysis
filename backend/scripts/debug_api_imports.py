import traceback

print("Attempting to import API routes for debugging...")

try:
    print("✅ Successfully imported api_router.")
except Exception:
    print("\n❌ FAILED to import api_router.")
    print("\n📋 Traceback:")
    traceback.print_exc() 