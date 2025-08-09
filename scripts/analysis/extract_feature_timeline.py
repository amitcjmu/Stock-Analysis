#!/opt/homebrew/bin/python3.11
import subprocess
import json
import re
from datetime import datetime
from collections import defaultdict, OrderedDict

def run_git_command(command):
    """Execute a git command and return the output."""
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command
    result = subprocess.run(command_list, capture_output=True, text=True, check=False)
    return result.stdout.strip()

def extract_all_commits():
    """Extract all commits with detailed information."""
    commits_raw = run_git_command([
        "git", "log", "--all",
        "--format=%H|%an|%ad|%s",
        "--date=short"
    ])

    commits = []
    for line in commits_raw.split('\n'):
        if line and '|' in line:
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                })

    return sorted(commits, key=lambda x: x['date'])

def identify_feature_commits(commits):
    """Identify commits that represent significant features."""
    feature_patterns = {
        'major_features': [
            r'feat(?:ure)?(?:\([^)]+\))?!?:\s*(.+)',  # Conventional commits
            r'^(?:add|implement|introduce)\s+(.+)',
            r'^feat:\s*(.+)',
            r'(?:^|\s)(?:add|implement|create)\s+(?:new\s+)?(.+(?:feature|system|component|module|flow|page|ui|dashboard|analysis|integration|service))',
        ],
        'ui_features': [
            r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:page|ui|component|dashboard|interface|frontend))',
            r'(?:enhance|update|improve)\s+(.+(?:ui|interface|page|component))',
        ],
        'backend_features': [
            r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:api|endpoint|service|flow|orchestrator|engine|system))',
            r'(?:enhance|update|improve)\s+(.+(?:backend|api|service|engine))',
        ],
        'infrastructure': [
            r'(?:add|implement|setup|configure)\s+(.+(?:docker|deployment|ci|cd|pipeline|database|migration))',
        ],
        'agent_features': [
            r'(?:add|implement|create)\s+(.+(?:agent|crew|ai|intelligence|agentic))',
        ]
    }

    features = []

    for commit in commits:
        message = commit['message']
        message_lower = message.lower()

        # Skip certain types of commits
        skip_patterns = [
            r'^(?:fix|bug|hotfix|patch)',
            r'^(?:refactor|cleanup|style|docs?)',
            r'^(?:test|spec)',
            r'^(?:chore|maintenance)',
            r'^(?:merge|revert)',
            r'(?:linting|formatting|typo)'
        ]

        if any(re.search(pattern, message_lower) for pattern in skip_patterns):
            continue

        # Check for feature patterns
        for category, patterns in feature_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    feature_description = match.group(1) if match.groups() else message

                    # Clean up the description
                    feature_description = feature_description.strip()
                    feature_description = re.sub(r'^(?:new\s+|the\s+)', '', feature_description)

                    features.append({
                        'date': commit['date'],
                        'hash': commit['hash'][:7],
                        'author': commit['author'],
                        'category': category,
                        'title': feature_description.title(),
                        'original_message': message,
                        'significance': calculate_significance(message, category)
                    })
                    break
            else:
                continue
            break

    return features

def calculate_significance(message, category):
    """Calculate the significance of a feature based on message content."""
    significance_score = 1

    # Category weights
    category_weights = {
        'major_features': 3,
        'ui_features': 2,
        'backend_features': 2,
        'agent_features': 3,
        'infrastructure': 1
    }

    significance_score *= category_weights.get(category, 1)

    # Keywords that increase significance
    high_impact_keywords = [
        'orchestrator', 'framework', 'system', 'architecture', 'platform',
        'engine', 'core', 'fundamental', 'major', 'comprehensive', 'complete',
        'end-to-end', 'full', 'enterprise', 'production', 'advanced'
    ]

    message_lower = message.lower()
    for keyword in high_impact_keywords:
        if keyword in message_lower:
            significance_score += 1

    # Emoji or special markers
    if any(emoji in message for emoji in ['🚀', '✨', '🎉', '💫', '⭐']):
        significance_score += 1

    return min(significance_score, 5)  # Cap at 5

def group_features_by_month(features):
    """Group features by month for timeline visualization."""
    monthly_features = defaultdict(list)

    for feature in features:
        try:
            date_obj = datetime.strptime(feature['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            monthly_features[month_key].append(feature)
        except ValueError:
            continue

    return dict(sorted(monthly_features.items()))

def extract_major_milestones(features):
    """Extract major milestones and releases."""
    milestones = []

    # Look for version tags
    tags_output = run_git_command(["git", "tag", "-l", "--sort=-version:refname"])
    tags = [tag for tag in tags_output.split('\n') if tag]

    for tag in tags:
        try:
            commit_info = run_git_command([
                "git", "log", "-1", "--format=%ad|%s", "--date=short", tag
            ])
            if '|' in commit_info:
                date, message = commit_info.split('|', 1)
                milestones.append({
                    'date': date,
                    'type': 'release',
                    'version': tag,
                    'title': f"Release {tag}",
                    'description': message,
                    'significance': 5
                })
        except:
            continue

    # Look for major feature launches based on high-significance features
    high_sig_features = [f for f in features if f['significance'] >= 4]

    # Group consecutive high-significance features as potential milestones
    current_milestone = []
    milestone_threshold_days = 7

    for feature in sorted(high_sig_features, key=lambda x: x['date']):
        if not current_milestone:
            current_milestone = [feature]
        else:
            last_date = datetime.strptime(current_milestone[-1]['date'], '%Y-%m-%d')
            current_date = datetime.strptime(feature['date'], '%Y-%m-%d')

            if (current_date - last_date).days <= milestone_threshold_days:
                current_milestone.append(feature)
            else:
                # Create milestone from accumulated features
                if len(current_milestone) >= 2:
                    milestone_date = current_milestone[0]['date']
                    feature_titles = [f['title'] for f in current_milestone]

                    milestones.append({
                        'date': milestone_date,
                        'type': 'feature_milestone',
                        'title': f"Major Feature Release - {milestone_date}",
                        'description': f"Released: {', '.join(feature_titles[:3])}{'...' if len(feature_titles) > 3 else ''}",
                        'features': current_milestone,
                        'significance': 4
                    })

                current_milestone = [feature]

    # Handle last milestone
    if len(current_milestone) >= 2:
        milestone_date = current_milestone[0]['date']
        feature_titles = [f['title'] for f in current_milestone]

        milestones.append({
            'date': milestone_date,
            'type': 'feature_milestone',
            'title': f"Major Feature Release - {milestone_date}",
            'description': f"Released: {', '.join(feature_titles[:3])}{'...' if len(feature_titles) > 3 else ''}",
            'features': current_milestone,
            'significance': 4
        })

    return sorted(milestones, key=lambda x: x['date'])

def create_timeline_summary(features, milestones):
    """Create a comprehensive timeline summary."""
    # Combine features and milestones
    all_events = []

    for feature in features:
        if feature['significance'] >= 3:  # Only include significant features
            all_events.append({
                'date': feature['date'],
                'type': 'feature',
                'title': feature['title'],
                'category': feature['category'],
                'significance': feature['significance'],
                'hash': feature['hash']
            })

    for milestone in milestones:
        all_events.append({
            'date': milestone['date'],
            'type': milestone['type'],
            'title': milestone['title'],
            'description': milestone['description'],
            'significance': milestone['significance']
        })

    return sorted(all_events, key=lambda x: x['date'])

def main():
    print("🔍 Extracting feature timeline from Git history...")

    # Extract all commits
    commits = extract_all_commits()
    print(f"Analyzed {len(commits)} commits")

    # Identify feature commits
    features = identify_feature_commits(commits)
    print(f"Identified {len(features)} feature commits")

    # Group by month
    monthly_features = group_features_by_month(features)

    # Extract milestones
    milestones = extract_major_milestones(features)
    print(f"Identified {len(milestones)} major milestones")

    # Create timeline
    timeline = create_timeline_summary(features, milestones)

    # Display results
    print("\n📅 FEATURE RELEASE TIMELINE:")
    print("=" * 80)

    current_month = ""
    for event in timeline[-30:]:  # Show last 30 significant events
        event_date = event['date']
        month = event_date[:7]

        if month != current_month:
            print(f"\n🗓️  {month}")
            print("-" * 40)
            current_month = month

        significance_stars = "⭐" * event['significance']
        event_type = event['type'].replace('_', ' ').title()

        print(f"{event_date} | {significance_stars} {event_type}")
        print(f"           {event['title']}")
        if 'description' in event:
            print(f"           {event['description']}")
        print()

    # Category breakdown
    print("\n📊 FEATURE CATEGORIES:")
    category_counts = defaultdict(int)
    for feature in features:
        category_counts[feature['category']] += 1

    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"• {category.replace('_', ' ').title()}: {count} features")

    # Save comprehensive data
    output_data = {
        'summary': {
            'total_features': len(features),
            'total_milestones': len(milestones),
            'date_range': {
                'start': commits[0]['date'] if commits else None,
                'end': commits[-1]['date'] if commits else None
            }
        },
        'timeline': timeline,
        'features_by_month': monthly_features,
        'milestones': milestones,
        'all_features': features,
        'category_breakdown': dict(category_counts)
    }

    with open('feature_timeline.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Feature timeline saved to feature_timeline.json")
    print(f"📈 Total features tracked: {len(features)}")
    print(f"🎯 Major milestones: {len(milestones)}")
    print(f"📆 Development period: {commits[0]['date']} to {commits[-1]['date']}")

if __name__ == "__main__":
    main()
