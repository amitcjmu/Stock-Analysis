#!/opt/homebrew/bin/python3.11
import subprocess
import json
import re
from datetime import datetime
from collections import defaultdict

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

def identify_key_features(commits):
    """Identify major features and functionality releases."""

    # Define patterns for different types of features
    feature_patterns = [
        # Core system features
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:orchestrator|engine|system|framework|architecture))', 'Core System', 5),
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:flow|workflow|pipeline))', 'Workflow', 4),

        # UI/Frontend features
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:page|ui|component|dashboard|interface))', 'UI/Frontend', 3),
        (r'(?:enhance|improve|update)\s+(.+(?:ui|interface|dashboard))', 'UI Enhancement', 2),

        # Backend/API features
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:api|endpoint|service|integration))', 'Backend/API', 3),
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:database|schema|migration))', 'Database', 3),

        # Agent/AI features
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:agent|crew|ai|intelligence|agentic))', 'AI/Agent', 4),

        # Analysis and processing
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:analysis|analytics|processing|assessment))', 'Analysis', 3),

        # Security and infrastructure
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:security|auth|permission|deployment))', 'Infrastructure', 3),

        # Major feature launches (using conventional commits)
        (r'feat(?:\([^)]+\))?!:\s*(.+)', 'Feature', 4),
        (r'feat:\s*(.+)', 'Feature', 3),

        # Specific application features
        (r'(?:add|implement|create)\s+(?:new\s+)?(.+(?:discovery|collection|assessment|migration|sixr))', 'App Feature', 4),
    ]

    # Skip patterns
    skip_patterns = [
        r'^(?:fix|bug|hotfix|patch)',
        r'^(?:refactor|cleanup|style|docs?|documentation)',
        r'^(?:test|spec|testing)',
        r'^(?:chore|maintenance|update dependencies)',
        r'^(?:merge|revert)',
        r'(?:linting|formatting|typo|minor)',
        r'(?:remove|delete)',
        r'(?:config|configuration|setup)',
        r'(?:debug|logging)'
    ]

    features = []

    for commit in commits:
        message = commit['message']
        message_lower = message.lower().strip()

        # Skip non-feature commits
        if any(re.search(pattern, message_lower) for pattern in skip_patterns):
            continue

        # Skip very short or unclear messages
        if len(message_lower) < 10:
            continue

        # Look for feature patterns
        for pattern, category, base_score in feature_patterns:
            match = re.search(pattern, message_lower)
            if match:
                feature_description = match.group(1) if match.groups() else message

                # Clean up description
                feature_description = feature_description.strip()
                feature_description = re.sub(r'^(?:new\s+|the\s+)', '', feature_description)
                feature_description = re.sub(r'\s+', ' ', feature_description)

                # Calculate final score based on keywords
                final_score = base_score

                # Boost score for important keywords
                high_value_keywords = [
                    'comprehensive', 'complete', 'full', 'end-to-end', 'enterprise',
                    'production', 'advanced', 'intelligent', 'automated', 'orchestration',
                    'framework', 'platform', 'system-wide', 'multi-tenant', 'scalable'
                ]

                for keyword in high_value_keywords:
                    if keyword in message_lower:
                        final_score += 1

                # Boost for emojis indicating major features
                if any(emoji in message for emoji in ['🚀', '✨', '🎉', '💫', '⭐', '🔥']):
                    final_score += 1

                # Cap the score
                final_score = min(final_score, 5)

                features.append({
                    'date': commit['date'],
                    'hash': commit['hash'][:7],
                    'author': commit['author'],
                    'category': category,
                    'title': feature_description.title(),
                    'original_message': message,
                    'score': final_score
                })
                break

    # Remove duplicates and sort by significance
    unique_features = []
    seen_titles = set()

    for feature in sorted(features, key=lambda x: x['score'], reverse=True):
        # Simple deduplication based on similar titles
        title_key = re.sub(r'[^a-z0-9]', '', feature['title'].lower())
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_features.append(feature)

    return sorted(unique_features, key=lambda x: x['date'])

def create_monthly_timeline(features):
    """Create a monthly timeline of features."""
    monthly_timeline = defaultdict(list)

    for feature in features:
        if feature['score'] >= 3:  # Only include significant features
            try:
                date_obj = datetime.strptime(feature['date'], '%Y-%m-%d')
                month_key = date_obj.strftime('%Y-%m')
                monthly_timeline[month_key].append(feature)
            except ValueError:
                continue

    return dict(sorted(monthly_timeline.items()))

def extract_version_releases():
    """Extract version releases from tags."""
    releases = []

    # Get all tags with their dates
    tags_output = run_git_command(["git", "tag", "-l", "--sort=-version:refname"])
    tags = [tag for tag in tags_output.split('\n') if tag]

    for tag in tags:
        try:
            # Get tag date and message
            tag_info = run_git_command([
                "git", "log", "-1", "--format=%ad|%s|%H", "--date=short", tag
            ])

            if '|' in tag_info:
                parts = tag_info.split('|', 2)
                date, message, commit_hash = parts

                releases.append({
                    'date': date,
                    'version': tag,
                    'title': f"Release {tag}",
                    'message': message,
                    'hash': commit_hash[:7],
                    'category': 'Release',
                    'score': 5
                })
        except:
            continue

    return releases

def main():
    print("🔍 Analyzing Git history for key features...")

    # Extract commits and features
    commits = extract_all_commits()
    features = identify_key_features(commits)
    releases = extract_version_releases()

    # Combine features and releases
    all_items = features + releases
    all_items = sorted(all_items, key=lambda x: x['date'])

    print(f"Found {len(features)} key features and {len(releases)} releases")

    # Create monthly timeline
    monthly_timeline = create_monthly_timeline(all_items)

    # Display key features timeline
    print(f"\n📅 KEY FEATURES TIMELINE")
    print("=" * 80)

    # Show significant features (score >= 4) and all releases
    significant_items = [item for item in all_items if item['score'] >= 4]

    current_month = ""
    for item in significant_items:
        item_date = item['date']
        month = item_date[:7]

        if month != current_month:
            print(f"\n🗓️  {month}")
            print("-" * 40)
            current_month = month

        score_stars = "⭐" * item['score']
        category_icon = {
            'Release': '🏷️',
            'Core System': '🏗️',
            'Workflow': '🔄',
            'UI/Frontend': '🎨',
            'Backend/API': '⚙️',
            'AI/Agent': '🤖',
            'App Feature': '📦',
            'Analysis': '📊',
            'Infrastructure': '🔧'
        }.get(item['category'], '📌')

        print(f"{item_date} | {score_stars} {category_icon} {item['category']}")
        print(f"         {item['title']}")
        print()

    # Category summary
    print("\n📊 FEATURE CATEGORIES SUMMARY:")
    category_counts = defaultdict(int)
    category_scores = defaultdict(int)

    for item in all_items:
        category_counts[item['category']] += 1
        category_scores[item['category']] += item['score']

    for category in sorted(category_counts.keys()):
        count = category_counts[category]
        avg_score = category_scores[category] / count if count > 0 else 0
        print(f"• {category}: {count} items (avg score: {avg_score:.1f})")

    # Save comprehensive data
    output_data = {
        'summary': {
            'total_features': len(features),
            'total_releases': len(releases),
            'total_significant_items': len(significant_items),
            'development_period': {
                'start': commits[0]['date'] if commits else None,
                'end': commits[-1]['date'] if commits else None
            }
        },
        'key_features_timeline': significant_items,
        'monthly_timeline': monthly_timeline,
        'all_features': all_items,
        'category_breakdown': dict(category_counts)
    }

    with open('key_features_timeline.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Key features timeline saved to key_features_timeline.json")
    print(f"📈 Total features: {len(features)}")
    print(f"🏷️ Releases: {len(releases)}")
    print(f"⭐ Significant items (4+ stars): {len(significant_items)}")

if __name__ == "__main__":
    main()
