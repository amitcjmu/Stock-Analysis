import asyncio
import json
import os
import sys

from sqlalchemy import inspect, text

# Add the backend directory to the Python path
sys.path.append('backend')

async def analyze_schema():
    try:
        from app.core.database import AsyncSessionLocal
        
        print("🔍 Database Schema Analysis")
        print("=" * 50)
        
        async with AsyncSessionLocal() as session:
            # Get all table names
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📊 Available Tables ({len(tables)}):")
            for table in tables:
                print(f"  - {table}")
            print()
            
            # Analyze key asset-related tables
            asset_tables = [t for t in tables if 'asset' in t.lower()]
            print(f"🎯 Asset-Related Tables ({len(asset_tables)}):")
            for table in asset_tables:
                print(f"  - {table}")
            print()
            
            # Detailed analysis of assets vs cmdb_assets
            for table_name in ['assets', 'cmdb_assets']:
                if table_name in tables:
                    print(f"📋 {table_name.upper()} TABLE ANALYSIS")
                    print("-" * 30)
                    
                    # Get row count
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"Row count: {count}")
                    
                    # Get column info
                    result = await session.execute(text(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """))
                    columns = result.fetchall()
                    
                    print(f"Columns ({len(columns)}):")
                    for col in columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col[3]}" if col[3] else ""
                        print(f"  - {col[0]} ({col[1]}) {nullable}{default}")
                    
                    # Get sample data if exists
                    if count > 0:
                        result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT 2"))
                        rows = result.fetchall()
                        column_names = [col[0] for col in columns]
                        
                        print("Sample data (first 2 rows):")
                        for i, row in enumerate(rows):
                            print(f"  Row {i+1}:")
                            for j, value in enumerate(row):
                                if j < len(column_names):
                                    # Truncate long values
                                    display_value = str(value)[:100] + "..." if str(value) and len(str(value)) > 100 else value
                                    print(f"    {column_names[j]}: {display_value}")
                    print()
            
            # Check for mapping/learning tables
            learning_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['mapping', 'learning', 'pattern'])]
            print(f"🧠 Learning/Mapping Tables ({len(learning_tables)}):")
            for table in learning_tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  - {table}: {count} records")
            print()
            
            # Check for import/session tables
            import_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['import', 'session', 'raw'])]
            print(f"📥 Import/Session Tables ({len(import_tables)}):")
            for table in import_tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  - {table}: {count} records")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_schema()) 