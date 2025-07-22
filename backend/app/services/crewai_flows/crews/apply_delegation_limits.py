#!/usr/bin/env python3
"""
Script to apply delegation limits to all crew files
"""

import os
import re


def apply_delegation_limits(file_path):
    """Apply delegation limits to a crew file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if crew_config is already imported
    if 'from .crew_config import' not in content:
        # Add import after crewai imports
        import_pattern = r'(from crewai import[^\n]+)'
        import_replacement = r'\1\nfrom .crew_config import get_optimized_agent_config, MAX_DELEGATIONS'
        content = re.sub(import_pattern, import_replacement, content, count=1)
    
    # Pattern to find Agent creation with allow_delegation=True
    agent_pattern = r'(Agent\([^)]*?allow_delegation=True[^)]*?\))'
    
    # Find all agent creations
    agents = re.findall(agent_pattern, content, re.DOTALL)
    
    # For each agent, check if it already has max_delegation
    for agent in agents:
        if 'max_delegation' not in agent:
            # Add max_delegation after allow_delegation
            new_agent = agent.replace(
                'allow_delegation=True',
                f'allow_delegation=True,\n            max_delegation={MAX_DELEGATIONS}'
            )
            content = content.replace(agent, new_agent)
    
    # Pattern to find Crew creation
    crew_pattern = r'(Crew\([^)]*?\))'
    crews = re.findall(crew_pattern, content, re.DOTALL)
    
    for crew in crews:
        if 'max_iterations' not in crew:
            # Add max_iterations to crew config
            if 'verbose=True' in crew:
                new_crew = crew.replace(
                    'verbose=True',
                    'verbose=True,\n            max_iterations=10'
                )
            else:
                # Add before the closing parenthesis
                new_crew = crew.rstrip(')')
                new_crew += ',\n            max_iterations=10)'
            
            content = content.replace(crew, new_crew)
    
    return content

# Get all crew files
crew_dir = os.path.dirname(os.path.abspath(__file__))
crew_files = [f for f in os.listdir(crew_dir) if f.endswith('_crew.py') and f != 'crew_config.py']

print(f"Found {len(crew_files)} crew files to process")

for crew_file in crew_files:
    file_path = os.path.join(crew_dir, crew_file)
    print(f"Processing {crew_file}...")
    
    try:
        updated_content = apply_delegation_limits(file_path)
        
        # Write back only if changes were made
        with open(file_path, 'r') as f:
            original = f.read()
        
        if original != updated_content:
            with open(file_path, 'w') as f:
                f.write(updated_content)
            print(f"  ✅ Updated {crew_file}")
        else:
            print(f"  ⏭️  No changes needed for {crew_file}")
            
    except Exception as e:
        print(f"  ❌ Error processing {crew_file}: {e}")

print("\nDone!")