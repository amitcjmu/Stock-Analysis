#!/opt/homebrew/bin/python3.11
import subprocess
import json
from collections import defaultdict
from datetime import datetime

def run_git_command(command):
    """Execute a git command and return the output."""
    # Convert string command to list for security
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command
    result = subprocess.run(command_list, capture_output=True, text=True, check=False)
    return result.stdout.strip()

def get_detailed_line_changes():
    """Get detailed line changes over time using git log --numstat."""
    # Get commit history with line statistics
    log_output = run_git_command(
        ["git", "log", "--all", "--numstat", "--format=%H|%ad|%an", "--date=short"]
    )

    daily_stats = defaultdict(lambda: {'added': 0, 'deleted': 0, 'files_changed': 0})
    current_commit = None
    current_date = None
    current_author = None

    for line in log_output.split('\n'):
        if '|' in line and not '\t' in line:
            # This is a commit header
            parts = line.split('|')
            if len(parts) >= 3:
                current_commit = parts[0]
                current_date = parts[1]
                current_author = parts[2]
        elif '\t' in line and current_date:
            # This is a file change line
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                added = parts[0]
                deleted = parts[1]

                # Skip binary files
                if added != '-' and deleted != '-':
                    try:
                        daily_stats[current_date]['added'] += int(added)
                        daily_stats[current_date]['deleted'] += int(deleted)
                        daily_stats[current_date]['files_changed'] += 1
                    except ValueError:
                        pass

    # Sort by date and calculate cumulative totals
    sorted_dates = sorted(daily_stats.keys())
    cumulative_added = 0
    cumulative_deleted = 0

    result = []
    for date in sorted_dates:
        stats = daily_stats[date]
        cumulative_added += stats['added']
        cumulative_deleted += stats['deleted']

        result.append({
            'date': date,
            'daily_added': stats['added'],
            'daily_deleted': stats['deleted'],
            'daily_files_changed': stats['files_changed'],
            'cumulative_added': cumulative_added,
            'cumulative_deleted': cumulative_deleted,
            'net_lines': cumulative_added - cumulative_deleted
        })

    return result

def main():
    print("Extracting detailed line statistics...")

    line_stats = get_detailed_line_changes()

    # Show last 30 days of data
    print("\nLINE CHANGES OVER TIME (Last 30 entries):")
    print("Date       | Added | Deleted | Files | Cumulative Added | Cumulative Deleted | Net Lines")
    print("-" * 90)

    for entry in line_stats[-30:]:
        print(f"{entry['date']} | {entry['daily_added']:>5} | {entry['daily_deleted']:>7} | {entry['daily_files_changed']:>5} | "
              f"{entry['cumulative_added']:>16} | {entry['cumulative_deleted']:>18} | {entry['net_lines']:>9}")

    # Save to JSON
    with open('detailed_line_stats.json', 'w') as f:
        json.dump(line_stats, f, indent=2)

    print(f"\n✅ Detailed statistics saved to detailed_line_stats.json")
    print(f"Total days with commits: {len(line_stats)}")
    print(f"Total lines added: {line_stats[-1]['cumulative_added'] if line_stats else 0}")
    print(f"Total lines deleted: {line_stats[-1]['cumulative_deleted'] if line_stats else 0}")
    print(f"Net lines of code: {line_stats[-1]['net_lines'] if line_stats else 0}")

if __name__ == "__main__":
    main()
