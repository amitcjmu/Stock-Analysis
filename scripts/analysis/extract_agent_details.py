#!/opt/homebrew/bin/python3.11
import os
import re
import json

def extract_detailed_agent_info():
    """Extract detailed CrewAI agent information."""
    agents = []

    # Search specifically in crew directories
    crew_dirs = [
        'backend/app/services/crews',
        'backend/app/services/crewai_flows/crews'
    ]

    for crew_dir in crew_dirs:
        if os.path.exists(crew_dir):
            for root, dirs, files in os.walk(crew_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        agents.extend(extract_agents_from_file(file_path))

    # Remove duplicates based on role
    unique_agents = {}
    for agent in agents:
        role = agent['role']
        if role not in unique_agents:
            unique_agents[role] = agent

    return list(unique_agents.values())

def extract_agents_from_file(file_path):
    """Extract agent definitions from a single file."""
    agents = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern to match Agent( with role= parameter
        agent_pattern = r'Agent\s*\(\s*[^)]*role\s*=\s*["\']([^"\']+)["\'][^)]*\)'
        matches = re.findall(agent_pattern, content, re.DOTALL)

        for role in matches:
            agents.append({
                'role': role.strip(),
                'file': file_path,
                'crew_type': os.path.basename(file_path).replace('.py', '')
            })

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return agents

def main():
    agents = extract_detailed_agent_info()

    print(f"Found {len(agents)} unique CrewAI agents:")
    print("\nAgent Roles by Crew:")

    # Group by crew type
    by_crew = {}
    for agent in agents:
        crew_type = agent['crew_type']
        if crew_type not in by_crew:
            by_crew[crew_type] = []
        by_crew[crew_type].append(agent['role'])

    for crew_type, roles in sorted(by_crew.items()):
        print(f"\n{crew_type}:")
        for role in sorted(roles):
            print(f"  • {role}")

    # Save detailed agent info
    with open('detailed_agent_info.json', 'w') as f:
        json.dump({
            'total_agents': len(agents),
            'agents_by_crew': by_crew,
            'all_agents': agents
        }, f, indent=2)

    print(f"\n✅ Detailed agent information saved to detailed_agent_info.json")
    print(f"Total unique CrewAI agents: {len(agents)}")

if __name__ == "__main__":
    main()
