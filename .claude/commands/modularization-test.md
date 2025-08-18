# Modularization Test Command

**Command**: `modularization-test`

**Description**: Analyze repository files for modularization compliance and identify files exceeding 300-400 LOC standards.

## Usage

```bash
# Basic analysis with default 350 LOC threshold
/modularization-test

# Custom threshold
/modularization-test --threshold 400

# Detailed breakdown of all files
/modularization-test --detailed

# Export results to JSON
/modularization-test --export-json results.json

# Full analysis with custom threshold and export
/modularization-test --threshold 300 --detailed --export-json modularization_report.json
```

## Command Implementation

This command runs the modularization testing script located at `scripts/modularization_test.py`.

The script analyzes:
- **Backend Python** files (.py)
- **Frontend TypeScript/React** files (.ts, .tsx)
- **Frontend JavaScript** files (.js, .jsx)
- **Configuration** files (.json, .yaml, .yml)
- **Migration** files (.sql)
- **Documentation** files (.md)
- **Scripts** (.sh, .bash)
- **Styles** (.css, .scss)

## Output Categories

- 🚨 **CRITICAL**: Files >500 LOC requiring immediate refactoring
- ⚠️  **HIGH PRIORITY**: Files 400-500 LOC needing attention
- 🔄 **MEDIUM PRIORITY**: Files exceeding threshold but <400 LOC
- ✅ **COMPLIANT**: Files within acceptable range

## Recommendations Provided

- 📦 Module splitting suggestions
- 🔄 Function grouping recommendations
- 🏗️  Class separation advice
- 🧠 Complexity reduction tips
- ⚛️  Framework-specific guidance (React, Python, TypeScript)

## Example Output

```
🎯 MODULARIZATION ANALYSIS REPORT
============================================================
📊 Total files analyzed: 245
⚠️  Files exceeding 350 LOC: 18
📈 Compliance rate: 92.7%

📋 SUMMARY BY CATEGORY
----------------------------------------
Backend Python:
  Total files: 89
  Exceeding threshold: 12
  Average LOC: 287

Frontend React:
  Total files: 67
  Exceeding threshold: 4
  Average LOC: 234

🚨 FILES EXCEEDING THRESHOLD
----------------------------------------

📁 BACKEND PYTHON
──────────────────────────────
📄 backend/app/services/discovery_flow_service.py
   Lines: 567 LOC
   Functions: 23
   Classes: 1
   Complexity: 2.1
   Recommendations:
     • 🚨 CRITICAL: File exceeds 500 LOC - requires immediate refactoring
     • 📦 Consider splitting into multiple modules (>20 functions)
     • 🧠 High complexity - consider simplifying logic
     • 🐍 Python: Split into services, repositories, and models
```

## Integration with Development Workflow

This command helps maintain code quality by:
1. **Identifying refactoring candidates** before they become problematic
2. **Providing actionable recommendations** for improvement
3. **Categorizing files** for prioritized refactoring efforts
4. **Tracking compliance rates** across different parts of the codebase
5. **Exporting data** for integration with other tools or tracking systems
