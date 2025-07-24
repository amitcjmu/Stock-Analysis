import asyncio
import os

import asyncpg


async def check_raw_data():
    try:
        # Database connection
        database_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:password@localhost:5432/migration_db"
        )
        conn = await asyncpg.connect(database_url)

        # Query raw import records
        query = """
            SELECT raw_data 
            FROM raw_import_records 
            WHERE client_account_id = '73dee5f1-6a01-43e3-b1b8-dbe6c66f2990' 
            ORDER BY id LIMIT 3
        """
        rows = await conn.fetch(query)

        if rows:
            print("Raw Import Data Analysis:")
            print("=" * 50)
            for i, row in enumerate(rows):
                raw_data = row["raw_data"]
                print(f"\nRecord {i+1}:")
                print(f"Column names: {list(raw_data.keys())}")
                print("Sample values:")
                for col, val in list(raw_data.items())[:6]:
                    print(f"  {col}: {val}")
        else:
            print("No raw import records found for Marathon Petroleum")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_raw_data())
