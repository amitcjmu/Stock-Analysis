import asyncio
import sys
sys.path.append('/app')

from app.services.discovery_agents.data_source_intelligence_agent import DataSourceIntelligenceAgent
from app.services.agent_ui_bridge import agent_ui_bridge

async def test_page_context():
    agent = DataSourceIntelligenceAgent()
    
    # Test with attribute-mapping context
    data_source = {
        'file_data': [{'CPU (Cores)': '8', 'RAM (GB)': '16', 'Hostname': 'server-01'}],
        'metadata': {'file_name': 'test.csv'},
        'upload_context': {'page': 'attribute-mapping'}
    }
    
    print("Testing page context handling...")
    result = await agent.analyze_data_source(data_source, 'attribute-mapping')
    
    # Check what questions were stored
    attribute_questions = agent_ui_bridge.get_questions_for_page('attribute-mapping')
    print(f'Questions for attribute-mapping: {len(attribute_questions)}')
    
    data_import_questions = agent_ui_bridge.get_questions_for_page('data-import')
    print(f'Questions for data-import: {len(data_import_questions)}')
    
    # Print the recent questions to see which page they were stored with
    all_questions = agent_ui_bridge.get_all_questions()
    print(f'Total questions: {len(all_questions)}')
    
    if all_questions:
        for q in all_questions[-3:]:  # Last 3 questions
            print(f'Question page: {q.get("page")}, type: {q.get("question_type")}')

if __name__ == "__main__":
    asyncio.run(test_page_context()) 