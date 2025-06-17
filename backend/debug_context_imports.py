import asyncio
from app.core.database import AsyncSessionLocal
from app.models.data_import.core import DataImport
from sqlalchemy import select, func
import logging

logging.basicConfig(level=logging.INFO)

async def check_imports_by_context():
    async with AsyncSessionLocal() as session:
        # Get all data imports with their context
        query = select(
            DataImport.id,
            DataImport.client_account_id,
            DataImport.engagement_id,
            DataImport.status,
            DataImport.source_filename,
            DataImport.import_name,
            DataImport.created_at
        ).order_by(DataImport.created_at.desc())
        
        result = await session.execute(query)
        imports = result.fetchall()
        
        print(f'📊 Found {len(imports)} total data imports:')
        print()
        
        context_counts = {}
        for imp in imports:
            context_key = f'{imp.client_account_id}|{imp.engagement_id}'
            if context_key not in context_counts:
                context_counts[context_key] = 0
            context_counts[context_key] += 1
            
            print(f'Import ID: {imp.id}')
            print(f'  Client: {imp.client_account_id}')
            print(f'  Engagement: {imp.engagement_id}')
            print(f'  Status: {imp.status}')
            print(f'  Filename: {imp.source_filename}')
            print(f'  Import Name: {imp.import_name}')
            print(f'  Created: {imp.created_at}')
            print()
        
        print('📈 Context Summary:')
        for context, count in context_counts.items():
            client_id, engagement_id = context.split('|')
            print(f'  Client {client_id[:8]}... | Engagement {engagement_id[:8]}... : {count} imports')
        
        # Check specific contexts
        demo_client = "bafd5b46-aaaf-4c95-8142-573699d93171"
        marathon_client = "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"
        
        print()
        print('🔍 Specific Context Analysis:')
        print(f'Demo context (bafd5b46...): {sum(1 for imp in imports if str(imp.client_account_id) == demo_client)} imports')
        print(f'Marathon context (73dee5f1...): {sum(1 for imp in imports if str(imp.client_account_id) == marathon_client)} imports')

if __name__ == "__main__":
    asyncio.run(check_imports_by_context()) 