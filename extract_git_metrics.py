#!/opt/homebrew/bin/python3.11
import subprocess
import json
import re
from datetime import datetime
from collections import defaultdict, Counter

def run_git_command(command):
    """Execute a git command and return the output."""
    # Convert string command to list for security
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command
    result = subprocess.run(command_list, capture_output=True, text=True, check=False)
    return result.stdout.strip()

def extract_commit_data():
    """Extract comprehensive commit data from Git history."""
    # Get all commits with full information
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
        # Check if it's a feature
        elif any(keyword in message_lower for keyword in ['feat:', 'feature', 'add', 'implement']):
            categories['features'].append(commit)
        # Check if it's related to agents
        elif 'agent' in message_lower:
            categories['agents'].append(commit)
        else:
            categories['other'].append(commit)

    return categories

def get_commits_by_author(commits):
    """Group commits by author."""
    author_commits = defaultdict(int)
    for commit in commits:
        author_commits[commit['author']] += 1

    return dict(sorted(author_commits.items(), key=lambda x: x[1], reverse=True))

def get_code_changes_over_time(commits):
    """Get added/deleted lines over time."""
    changes_by_date = defaultdict(lambda: {'added': 0, 'deleted': 0})

    for commit in commits[:100]:  # Limit to last 100 commits for performance
        stats = run_git_command(["git", "show", "--stat", commit['hash'], "--format="])

        # Extract date without time for daily aggregation
        date = commit['date'].split(' ')[0]

        # Parse the stats
        for line in stats.split('\n'):
            if '|' in line and ('+' in line or '-' in line):
                # Extract additions and deletions
                changes = line.split('|')[1].strip()
                added = changes.count('+')
                deleted = changes.count('-')
                changes_by_date[date]['added'] += added
                changes_by_date[date]['deleted'] += deleted

    return dict(sorted(changes_by_date.items()))

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

def count_agents_over_time(commits):
    """Track agent-related commits over time to show growth."""
    agent_timeline = defaultdict(int)
    cumulative_count = 0

    # Sort commits by date
    sorted_commits = sorted(commits, key=lambda x: x['date'])

    for commit in sorted_commits:
        if 'agent' in commit['message'].lower():
            date = commit['date'].split(' ')[0]
            cumulative_count += 1
            agent_timeline[date] = cumulative_count

    return dict(agent_timeline)

def main():
    print("Extracting Git metrics...")

    # Extract all commit data
    commits = extract_commit_data()
    print(f"Total commits analyzed: {len(commits)}")

    # 1. Pie chart data for outputs
    categories = categorize_commits(commits)
    pie_data = {
        'releases': len(categories['releases']),
        'features': len(categories['features']),
        'agents': len(categories['agents']),
        'other': len(categories['other'])
    }

    print("\n1. PIE CHART DATA (Outputs):")
    print(json.dumps(pie_data, indent=2))

    # 2. Bar chart data for commits by author
    author_commits = get_commits_by_author(commits)
    print("\n2. BAR CHART DATA (Commits by Author):")
    print(json.dumps(author_commits, indent=2))

    # 3. Line graph data for added/deleted lines
    code_changes = get_code_changes_over_time(commits)
    print("\n3. LINE GRAPH DATA (Added/Deleted Lines Over Time):")
    print("Date format: YYYY-MM-DD")
    for date, changes in list(code_changes.items())[:10]:  # Show first 10 entries
        print(f"{date}: +{changes['added']} -{changes['deleted']}")

    # 4. Agent count growth
    agent_growth = count_agents_over_time(commits)
    print("\n4. AGENT COUNT GROWTH:")
    print(json.dumps(agent_growth, indent=2))

    # 5. Bot commits timeline
    bot_commits = find_bot_commits(commits)
    print("\n5. BOT COMMITS TIMELINE:")
    print(f"Total bot commits found: {len(bot_commits)}")
    for commit in bot_commits[:5]:  # Show first 5 bot commits
        print(f"- {commit['date']}: {commit['author']} - {commit['message'][:60]}...")

    # Save all data to JSON file
    output_data = {
        'pie_chart_data': pie_data,
        'commits_by_author': author_commits,
        'code_changes_timeline': code_changes,
        'agent_growth': agent_growth,
        'bot_commits': [
            {
                'date': c['date'],
                'author': c['author'],
                'message': c['message'],
                'hash': c['hash'][:7]
            } for c in bot_commits
        ]
    }

    with open('git_metrics_output.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print("\n✅ All data has been saved to git_metrics_output.json")

if __name__ == "__main__":
    main()
