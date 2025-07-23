import json
from pathlib import Path


def add_client_context():
    marathon_client_id = '73dee5f1-6a01-43e3-b1b8-dbe6c66f2990'
    data_dir = Path('data')
    
    # Update agent insights
    insights_file = data_dir / 'agent_insights.json'
    if insights_file.exists():
        with open(insights_file, 'r') as f:
            insights = json.load(f)
        
        updated = 0
        for insight_id, insight in insights.items():
            if not insight.get('client_account_id'):
                insight['client_account_id'] = marathon_client_id
                updated += 1
        
        with open(insights_file, 'w') as f:
            json.dump(insights, f, indent=2)
        print(f'Updated {updated} insights with Marathon Petroleum client context')
    
    # Update agent questions
    questions_file = data_dir / 'agent_questions.json'
    if questions_file.exists():
        with open(questions_file, 'r') as f:
            questions = json.load(f)
        
        updated = 0
        for question_id, question in questions.items():
            if not question.get('client_account_id'):
                question['client_account_id'] = marathon_client_id
                updated += 1
        
        with open(questions_file, 'w') as f:
            json.dump(questions, f, indent=2)
        print(f'Updated {updated} questions with Marathon Petroleum client context')
    
    # Update agent classifications if they exist
    classifications_file = data_dir / 'agent_classifications.json'
    if classifications_file.exists():
        with open(classifications_file, 'r') as f:
            classifications = json.load(f)
        
        updated = 0
        for classification_id, classification in classifications.items():
            if not classification.get('client_account_id'):
                classification['client_account_id'] = marathon_client_id
                updated += 1
        
        with open(classifications_file, 'w') as f:
            json.dump(classifications, f, indent=2)
        print(f'Updated {updated} classifications with Marathon Petroleum client context')

if __name__ == "__main__":
    add_client_context() 