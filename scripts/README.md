# Scripts Directory

This directory contains utility scripts for maintaining and analyzing the AI Modernize Migration Platform codebase.

## Available Scripts

### 🎯 Modularization Testing Script

**File**: `modularization_test.py`

**Purpose**: Analyzes all code files in the repository to identify those that exceed the 300-400 lines of code (LOC) standard, providing detailed categorization and refactoring recommendations.

#### Features

- **Comprehensive Analysis**: Scans all code files (Python, TypeScript, JavaScript, React, etc.)
- **Smart Categorization**: Automatically categorizes files by type and location
- **Detailed Metrics**: Provides LOC count, function count, class count, and complexity scoring
- **Actionable Recommendations**: Gives specific refactoring suggestions based on file characteristics
- **Priority Classification**: Marks files as Critical (>500 LOC), High Priority (400-500 LOC), or Medium Priority (threshold-400 LOC)
- **Export Capabilities**: Can export results to JSON for further analysis or tracking

#### Usage

```bash
# Basic analysis with default 350 LOC threshold
python scripts/modularization_test.py

# Custom threshold
python scripts/modularization_test.py --threshold 400

# Detailed breakdown of all files
python scripts/modularization_test.py --detailed

# Export results to JSON
python scripts/modularization_test.py --export-json results.json

# Full analysis with custom settings
python scripts/modularization_test.py --threshold 300 --detailed --export-json modularization_report.json
```

#### CC Integration

The script is available as CC commands:
- `/modularization-test` - Full command with all options
- `/modtest` - Quick alias for common usage

#### Sample Output

```
🎯 MODULARIZATION ANALYSIS REPORT
============================================================
📊 Total files analyzed: 1244
⚠️  Files exceeding 350 LOC: 318
📈 Compliance rate: 74.4%

📋 SUMMARY BY CATEGORY
----------------------------------------
Backend Python:
  Total files: 389
  Exceeding threshold: 87
  Average LOC: 229

Frontend React:
  Total files: 245
  Exceeding threshold: 68
  Average LOC: 246

🚨 FILES EXCEEDING THRESHOLD
----------------------------------------

📁 BACKEND PYTHON
──────────────────────────────
📄 backend/app/api/v1/endpoints/data_import/field_mapping.py
   Lines: 1295 LOC
   Functions: 26
   Classes: 0
   Complexity: 1.8
   Recommendations:
     • 🚨 CRITICAL: File exceeds 500 LOC - requires immediate refactoring
     • 📦 Consider splitting into multiple modules (>20 functions)
     • 🔧 Moderate complexity - review for optimization opportunities
     • 🐍 Python: Split into services, repositories, and models
```

#### Categories Analyzed

- **Backend Python** (.py files in backend/)
- **Frontend React** (.tsx, .jsx files)
- **Frontend TypeScript** (.ts files)
- **Frontend JavaScript** (.js files)
- **Frontend Styles** (.css, .scss files)
- **Configuration** (.json, .yaml, .yml files)
- **Database Migration** (.sql files, alembic versions)
- **Documentation** (.md files)
- **Scripts** (.sh, .bash files)
- **Tests** (files in test directories)

#### Recommendations Generated

The script provides specific recommendations based on:

1. **Line Count**:
   - 🚨 CRITICAL: >500 LOC - immediate refactoring required
   - ⚠️ WARNING: Exceeds threshold - consider refactoring

2. **Function/Class Count**:
   - 📦 Split into multiple modules (>20 functions)
   - 🔄 Group related functions into classes
   - 🏗️ Split classes into separate files (>5 classes)

3. **Complexity Score**:
   - 🧠 High complexity - simplify logic
   - 🔧 Moderate complexity - review optimization opportunities

4. **Framework-Specific**:
   - 🐍 Python: Split into services, repositories, and models
   - ⚛️ React: Break into smaller components and custom hooks
   - 📘 TypeScript: Extract types, interfaces, and utilities

#### Integration with Development Workflow

Use this script to:

1. **Pre-commit Analysis**: Check if new changes introduce oversized files
2. **Refactoring Planning**: Identify which files need attention first
3. **Code Review**: Validate that refactored code meets standards
4. **Progress Tracking**: Monitor improvement in modularization over time
5. **Team Communication**: Share standardized reports on code quality

#### Configuration

The script can be customized by modifying:

- `threshold`: Default LOC limit (currently 350)
- `skip_dirs`: Directories to ignore during scanning
- `skip_files`: Specific files to exclude
- `code_extensions`: File types to analyze

## Adding New Scripts

When adding new scripts to this directory:

1. **Make executable**: `chmod +x script_name.py`
2. **Add documentation**: Update this README with usage instructions
3. **Create Claude command**: Add command definition in `.claude/commands/`
4. **Follow naming convention**: Use descriptive, lowercase names with underscores
5. **Include help text**: Use argparse for command-line arguments and help
6. **Add error handling**: Provide meaningful error messages and exit codes

## Script Guidelines

All scripts in this directory should follow these guidelines:

- **Self-contained**: Include all necessary imports and dependencies
- **Well-documented**: Clear docstrings and inline comments
- **Error handling**: Graceful failure with helpful error messages
- **Logging**: Use Python logging module for output
- **Type hints**: Include type annotations for better code clarity
- **Testing**: Consider adding tests for complex scripts

## Dependencies

Scripts may require additional Python packages. Install them with:

```bash
pip install -r requirements.txt
```

Or for development dependencies:

```bash
pip install -r requirements-dev.txt
```