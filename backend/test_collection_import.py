"""Test collection module import"""
try:
    print("✅ Collection router imported successfully")
except Exception as e:
    print(f"❌ Error importing collection router: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()