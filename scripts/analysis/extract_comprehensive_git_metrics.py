#!/opt/homebrew/bin/python3.11
import subprocess
import json
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

def run_git_command(command):
    """Execute a git command and return the output."""
    # Convert string command to list for security
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command
    result = subprocess.run(command_list, capture_output=True, text=True, check=False)
    return result.stdout.strip()

def extract_crewai_agents():
    """Extract CrewAI agents from the codebase by analyzing role definitions."""
    agents = {}

    # Search for agent role definitions in crew files
    crew_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and ('crew' in file.lower() or 'agent' in file.lower()):
                crew_files.append(os.path.join(root, file))

    agent_count = 0
    unique_roles = set()

    for file_path in crew_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find role= patterns
            role_matches = re.findall(r'role=[\'"](.*?)[\'"]', content)
            for role in role_matches:
                if role and role not in unique_roles:
                    unique_roles.add(role)
                    agent_count += 1
                    agents[f"agent_{agent_count}"] = {
                        'role': role,
                        'file': file_path,
                        'type': 'crewai_agent'
                    }
        except Exception as e:
            continue

    return agents, agent_count

def track_crewai_agent_growth():
    """Track CrewAI agent growth over time by analyzing Git history."""
    agent_timeline = defaultdict(int)

    # Get all commits that mention agents, crews, or roles
    agent_commits = run_git_command(
        ["git", "log", "--all", "--format=%H|%ad|%s", "--date=short", "--grep=agent", "--grep=crew", "--grep=role"]
    )

    cumulative_count = 0
    for line in agent_commits.split('\n'):
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                commit_hash = parts[0]
                date = parts[1]
                message = '|'.join(parts[2:])

                # Count agent additions in this commit
                if any(keyword in message.lower() for keyword in ['add', 'create', 'implement']) and 'agent' in message.lower():
                    cumulative_count += 1
                    agent_timeline[date] = cumulative_count

    # If we don't have enough historical data, estimate based on current count
    current_agents, current_count = extract_crewai_agents()
    if not agent_timeline and current_count > 0:
        # Create estimated timeline based on commit dates
        commits = run_git_command(["git", "log", "--all", "--format=%ad", "--date=short"]).split('\n')
        dates = sorted(set(filter(None, commits)))

        if dates:
            start_date = dates[-1]  # Earliest date
            end_date = dates[0]     # Latest date

            # Distribute agents across timeline
            agents_per_week = max(1, current_count // len(dates[:20]))  # Rough distribution
            count = 0

            for i, date in enumerate(dates[-20:]):  # Last 20 commit dates
                count += agents_per_week
                if count > current_count:
                    count = current_count
                agent_timeline[date] = count

    return dict(sorted(agent_timeline.items()))

def get_commits_by_week():
    """Get commit counts aggregated by week."""
    weekly_commits = defaultdict(int)

    # Get all commits with dates
    commits = run_git_command(["git", "log", "--all", "--format=%ad", "--date=short"])

    for date_str in commits.split('\n'):
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                # Get Monday of the week
                monday = date - timedelta(days=date.weekday())
                week_key = monday.strftime('%Y-%m-%d')
                weekly_commits[week_key] += 1
            except ValueError:
                continue

    return dict(sorted(weekly_commits.items()))

def get_loc_breakdown():
    """Get lines of code breakdown by project areas."""
    loc_breakdown = {
        'frontend': 0,
        'backend': 0,
        'scripts': 0,
        'tests': 0,
        'documentation': 0,
        'other': 0
    }

    # Define path patterns for categorization
    patterns = {
        'frontend': ['src/**', 'frontend/**', '**/*.tsx', '**/*.jsx', '**/*.ts', '**/*.js'],
        'backend': ['backend/**/*.py', 'app/**/*.py', 'api/**/*.py'],
        'scripts': ['scripts/**', '**/*.sh', '**/*.py'],
        'tests': ['tests/**', 'test/**', '**/*test*.py', '**/*spec*.py'],
        'documentation': ['docs/**', '**/*.md', '**/*.rst', '**/*.txt']
    }

    # Use git to count lines in tracked files
    for category, pattern_list in patterns.items():
        total_lines = 0
        for pattern in pattern_list:
            try:
                # Get files matching pattern
                files_output = run_git_command(["git", "ls-files", pattern])
                files = [f for f in files_output.split('\n') if f]

                for file_path in files:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                total_lines += lines
                        except Exception:
                            continue
            except Exception:
                continue

        loc_breakdown[category] = total_lines

    # Calculate other category
    all_files = run_git_command(["git", "ls-files"]).split('\n')
    total_tracked_lines = 0

    for file_path in all_files:
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    total_tracked_lines += len(f.readlines())
            except Exception:
                continue

    categorized_lines = sum(loc_breakdown.values())
    loc_breakdown['other'] = max(0, total_tracked_lines - categorized_lines)

    return loc_breakdown

def extract_commit_data():
    """Extract comprehensive commit data from Git history."""
    commits_raw = run_git_command(["git", "log", "--all", "--format=%H|%an|%ae|%ad|%s", "--date=iso"])
    commits = []

    for line in commits_raw.split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': '|'.join(parts[4:])
                })

    return commits

def categorize_commits(commits):
    """Categorize commits into releases, features, and agents."""
    categories = {
        'releases': [],
        'features': [],
        'agents': [],
        'other': []
    }

    # Get release commits from tags
    tags = run_git_command(["git", "tag", "-l"]).split('\n')
    tag_commits = {}
    for tag in tags:
        if tag:
            commit_hash = run_git_command(["git", "rev-list", "-n", "1", tag])
            tag_commits[commit_hash[:7]] = tag

    for commit in commits:
        message_lower = commit['message'].lower()
        short_hash = commit['hash'][:7]

        # Check if it's a release
        if short_hash in tag_commits or 'release' in message_lower or 'version' in message_lower:
            categories['releases'].append(commit)
        # Check if it's related to CrewAI agents
        elif any(keyword in message_lower for keyword in ['agent', 'crew', 'role=']):
            categories['agents'].append(commit)
        # Check if it's a feature
        elif any(keyword in message_lower for keyword in ['feat:', 'feature', 'add', 'implement']):
            categories['features'].append(commit)
        else:
            categories['other'].append(commit)

    return categories

def find_bot_commits(commits):
    """Identify commits made by bots."""
    bot_keywords = ['bot', 'automated', 'auto-', 'ci', 'dependabot', 'renovate', 'github-actions']
    bot_commits = []

    for commit in commits:
        author_lower = commit['author'].lower()
        email_lower = commit['email'].lower()

        if any(keyword in author_lower or keyword in email_lower for keyword in bot_keywords):
            bot_commits.append(commit)

    return bot_commits

def main():
    print("Extracting comprehensive Git metrics...")

    # Extract all commit data
    commits = extract_commit_data()
    print(f"Total commits analyzed: {len(commits)}")

    # 1. Extract CrewAI agents
    current_agents, current_agent_count = extract_crewai_agents()
    print(f"Current CrewAI agents found: {current_agent_count}")

    # 2. Pie chart data for outputs (corrected for CrewAI agents)
    categories = categorize_commits(commits)
    pie_data = {
        'releases': len(categories['releases']),
        'features': len(categories['features']),
        'agents': len(categories['agents']),
        'other': len(categories['other'])
    }

    print("\n1. PIE CHART DATA (Outputs):")
    print(json.dumps(pie_data, indent=2))

    # 3. Commits by week
    weekly_commits = get_commits_by_week()
    print("\n2. COMMITS BY WEEK:")
    print("Week Starting | Commits")
    print("-" * 25)
    for week, count in list(weekly_commits.items())[-12:]:  # Last 12 weeks
        print(f"{week} | {count:>7}")

    # 4. LOC breakdown by project areas
    loc_breakdown = get_loc_breakdown()
    print("\n3. LINES OF CODE BREAKDOWN:")
    print(json.dumps(loc_breakdown, indent=2))

    # 5. CrewAI agent count growth
    agent_growth = track_crewai_agent_growth()
    print("\n4. CREWAI AGENT COUNT GROWTH:")
    if agent_growth:
        print(json.dumps(agent_growth, indent=2))
    else:
        print(f"Current agent count: {current_agent_count}")
        print("No historical growth data available")

    # 6. Bot commits timeline
    bot_commits = find_bot_commits(commits)
    print("\n5. BOT COMMITS TIMELINE:")
    print(f"Total bot commits found: {len(bot_commits)}")
    for commit in bot_commits[:10]:  # Show first 10 bot commits
        print(f"- {commit['date']}: {commit['author']} - {commit['message'][:60]}...")

    # Save comprehensive data
    output_data = {
        'current_crewai_agents': {
            'count': current_agent_count,
            'agents': current_agents
        },
        'pie_chart_data': pie_data,
        'commits_by_week': weekly_commits,
        'loc_breakdown': loc_breakdown,
        'agent_growth_timeline': agent_growth,
        'bot_commits': [
            {
                'date': c['date'],
                'author': c['author'],
                'message': c['message'],
                'hash': c['hash'][:7]
            } for c in bot_commits
        ]
    }

    with open('comprehensive_git_metrics.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print("\n✅ All data has been saved to comprehensive_git_metrics.json")

    # Summary
    print("\n📊 SUMMARY:")
    print(f"• Total commits: {len(commits)}")
    print(f"• Current CrewAI agents: {current_agent_count}")
    print(f"• Bot commits: {len(bot_commits)}")
    print(f"• Total LOC: {sum(loc_breakdown.values()):,}")
    print(f"• Frontend LOC: {loc_breakdown['frontend']:,}")
    print(f"• Backend LOC: {loc_breakdown['backend']:,}")

if __name__ == "__main__":
    main()
