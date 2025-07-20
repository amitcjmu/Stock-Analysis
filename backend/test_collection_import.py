"""Test collection module import"""
try:
    from app.api.v1.endpoints.collection import router as collection_router
    print("✅ Collection router imported successfully")
except Exception as e:
    print(f"❌ Error importing collection router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()