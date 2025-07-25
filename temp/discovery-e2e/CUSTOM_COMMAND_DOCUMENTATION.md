# Multi-Agent Issue Resolution System - Claude Code Custom Command

## Overview
This custom command allows you to invoke the multi-agent issue resolution system directly from Claude Code using screenshots, error logs, or manual descriptions as input. The system automatically analyzes the input, categorizes the issue, assigns appropriate agents, and manages the complete resolution workflow.

## Installation

### 1. Copy Files to Claude Code Directory
```bash
# Create Claude Code custom commands directory
mkdir -p ~/.claude/commands/multi-agent-resolver

# Copy files
cp /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/resolve-issue ~/.claude/commands/multi-agent-resolver/
cp /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/claude-code-command.py ~/.claude/commands/multi-agent-resolver/
cp /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/workflow-enforcement-system.py ~/.claude/commands/multi-agent-resolver/

# Make executable
chmod +x ~/.claude/commands/multi-agent-resolver/resolve-issue
```

### 2. Add to Claude Code Configuration
Add this to your Claude Code configuration file (`~/.claude/config.json`):

```json
{
  "custom_commands": {
    "resolve-issue": {
      "path": "~/.claude/commands/multi-agent-resolver/resolve-issue",
      "description": "Multi-agent issue resolution system",
      "category": "Development Tools"
    }
  }
}
```

## Usage

### Command Syntax
```bash
resolve-issue [OPTIONS]
```

### Options
- `--screenshot PATH` - Resolve issue from screenshot file
- `--logs "LOG_CONTENT"` - Resolve issue from error logs
- `--description "DESC"` - Resolve issue from manual description
- `--launch` - Launch multi-agent resolution immediately
- `--status ISSUE_ID` - Get status of existing issue
- `--help` - Show help message

## Usage Examples

### 1. Resolve UI Issue from Screenshot
```bash
# Take screenshot of UI issue and resolve it
resolve-issue --screenshot /path/to/ui-error.png --launch
```

**What happens:**
- Screenshot analyzed for UI patterns
- Issue categorized as "ui" type
- Agent-1 (UI Testing) assigned as original reporter
- Full multi-agent workflow initiated
- Agent instructions created in session directory

### 2. Resolve Backend Issue from Error Logs
```bash
# Pass error logs from backend
resolve-issue --logs "ERROR: Database connection timeout after 30s
Stack trace:
  File '/app/database.py', line 45, in connect
  sqlalchemy.exc.OperationalError: connection timeout" --launch
```

**What happens:**
- Error logs analyzed for backend/database keywords
- Issue categorized as "backend" type
- Agent-2 (Backend Monitoring) assigned as original reporter
- Workflow enforcement system engaged
- Historical review initiated

### 3. Resolve Issue from Manual Description
```bash
# Describe the issue manually
resolve-issue --description "The login button on the authentication page is not responding to clicks. Users can't log in to the application." --launch
```

**What happens:**
- Description analyzed for keyword patterns
- Issue categorized as "ui" type based on "button" and "clicks"
- Agent-1 assigned as original reporter
- Complete agent workflow initiated

### 4. Check Issue Status
```bash
# Check progress of existing issue
resolve-issue --status ISSUE-20250115-001
```

**Output:**
```json
{
  "issue_id": "ISSUE-20250115-001",
  "current_state": "IMPLEMENTATION",
  "created_at": "2025-01-15T16:30:00",
  "issue_type": "ui",
  "priority": "high",
  "transitions": [
    {
      "from": "IDENTIFIED",
      "to": "HISTORICAL_REVIEW",
      "timestamp": "2025-01-15T16:31:00",
      "agent": "agent-5"
    }
  ]
}
```

## Workflow Process

### 1. Issue Analysis
The system automatically analyzes your input:

- **Screenshots**: Analyzed for UI patterns, file naming conventions
- **Error Logs**: Keyword analysis for backend/database/UI patterns
- **Manual Description**: Text analysis for issue categorization

### 2. Agent Assignment
Based on analysis, appropriate agents are assigned:

- **UI Issues**: Agent-1 (UI Testing) as original reporter
- **Backend Issues**: Agent-2 (Backend Monitoring) as original reporter
- **Database Issues**: Agent-3 (Database Validation) as original reporter
- **Architecture Issues**: Agent-4 (Solution Architect) as original reporter

### 3. Workflow Execution
The system follows the enhanced workflow:

```
IDENTIFIED → HISTORICAL_REVIEW → SOLUTION_APPROVED → IMPLEMENTATION → VERIFICATION → ORIGINAL_REPORTER_VALIDATION → COMPLETED
```

### 4. Agent Instructions
Each agent receives specific instructions in the session directory:

- **Agent-5**: Historical review instructions
- **Original Reporter**: Validation and reproduction instructions
- **Agent-4**: Solution architecture instructions
- **Agent-8**: Implementation instructions
- **Agent-7**: Verification instructions

## Output and Session Management

### Session Directory Structure
```
/Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/session_YYYYMMDD_HHMMSS/
├── ISSUE-YYYYMMDD-001.json                    # Issue data
├── ISSUE-YYYYMMDD-001_execution_plan.json     # Agent execution plan
├── ISSUE-YYYYMMDD-001_screenshot.png          # Screenshot copy (if applicable)
├── ISSUE-YYYYMMDD-001_error_logs.txt          # Error logs (if applicable)
└── agent_instructions/
    ├── ISSUE-YYYYMMDD-001_agent-1_instructions.md
    ├── ISSUE-YYYYMMDD-001_agent-4_instructions.md
    ├── ISSUE-YYYYMMDD-001_agent-5_instructions.md
    ├── ISSUE-YYYYMMDD-001_agent-7_instructions.md
    └── ISSUE-YYYYMMDD-001_agent-8_instructions.md
```

### Issue Data Structure
```json
{
  "issue_id": "ISSUE-20250115-001",
  "created_at": "2025-01-15T16:30:00",
  "session_id": "20250115_163000",
  "analysis": {
    "issue_type": "ui",
    "confidence": 0.85,
    "source_type": "screenshot",
    "suggested_reporter": "agent-1",
    "description": "UI issue identified from screenshot"
  },
  "workflow_state": "IDENTIFIED",
  "priority": "high",
  "estimated_effort": "medium",
  "suggested_agents": ["agent-8", "agent-1", "agent-7", "agent-5"],
  "next_steps": [
    "1. Agent-5 performs historical review",
    "2. agent-1 validates issue reproduction",
    "3. Agent-4 documents solution approach",
    "4. Agent-8 implements the solution",
    "5. Agent-7 verifies implementation",
    "6. agent-1 validates resolution",
    "7. Issue marked as completed"
  ]
}
```

## Integration with Claude Code

### Custom Command Registration
1. **Add to PATH**: Ensure the `resolve-issue` command is in your PATH
2. **Claude Code Integration**: Register as a custom command in Claude Code
3. **Workflow Integration**: System integrates with existing workflow enforcement

### Claude Code Usage Patterns
```bash
# In Claude Code, you can use:
!resolve-issue --screenshot /path/to/screenshot.png --launch
!resolve-issue --logs "$(cat error.log)" --launch
!resolve-issue --description "Button not working" --launch
!resolve-issue --status ISSUE-20250115-001
```

## Advanced Features

### 1. Intelligent Issue Categorization
- **Keyword Analysis**: Analyzes text for domain-specific keywords
- **Confidence Scoring**: Provides confidence levels for categorization
- **Context Awareness**: Considers file names, paths, and error patterns

### 2. Workflow Enforcement Integration
- **State Management**: Tracks issue state through complete workflow
- **Compliance Checking**: Ensures proper process adherence
- **Agent Validation**: Enforces original reporter validation

### 3. Session Management
- **Unique Sessions**: Each command creates a unique session
- **File Organization**: Organized directory structure for easy navigation
- **Progress Tracking**: Complete audit trail of agent activities

### 4. Agent Coordination
- **Role-Based Assignment**: Agents assigned based on expertise
- **Instruction Generation**: Customized instructions for each agent
- **Validation Requirements**: Specific validation criteria for each issue type

## Troubleshooting

### Common Issues

#### 1. Command Not Found
```bash
# Check if script is executable
ls -la ~/.claude/commands/multi-agent-resolver/resolve-issue

# Make executable if needed
chmod +x ~/.claude/commands/multi-agent-resolver/resolve-issue
```

#### 2. Python Dependencies
```bash
# Install required packages
pip install argparse json logging datetime uuid base64 hashlib
```

#### 3. Session Directory Permissions
```bash
# Ensure write permissions
chmod 755 /Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/discovery-e2e/
```

### Debug Mode
Add debug logging by setting environment variable:
```bash
export PYTHONPATH="/path/to/resolve-issue:$PYTHONPATH"
export DEBUG=1
resolve-issue --screenshot /path/to/screenshot.png --launch
```

## Best Practices

### 1. Screenshot Guidelines
- **Clear Screenshots**: Ensure error messages are visible
- **Descriptive Filenames**: Use descriptive names like "login-button-error.png"
- **Multiple Angles**: Provide different views if issue is complex

### 2. Error Log Guidelines
- **Complete Logs**: Include full stack traces when possible
- **Context Information**: Include timestamps and relevant context
- **Sanitized Data**: Remove sensitive information before submitting

### 3. Manual Description Guidelines
- **Be Specific**: Describe exact steps to reproduce
- **Include Context**: Mention which page, component, or feature
- **Expected vs Actual**: Describe what should happen vs what actually happens

### 4. Issue Tracking
- **Use Status Checks**: Regularly check issue status
- **Review Agent Instructions**: Check session directory for progress
- **Validate Resolutions**: Ensure original reporter validates properly

## Security Considerations

### 1. Data Sanitization
- **Remove Sensitive Data**: Clean error logs of passwords, tokens, etc.
- **Screenshot Privacy**: Ensure screenshots don't contain sensitive information
- **Session Data**: Session data is stored locally, not transmitted

### 2. File Permissions
- **Restrict Access**: Ensure session directories have appropriate permissions
- **Clean Up**: Regularly clean up old session data
- **Audit Trail**: Maintain logs for security auditing

## Performance Optimization

### 1. Large Files
- **Screenshot Size**: Optimize screenshot size for faster processing
- **Log Truncation**: Truncate very large log files to relevant sections
- **Session Cleanup**: Regularly clean up old session directories

### 2. Resource Usage
- **Memory Management**: System handles large files efficiently
- **Disk Space**: Monitor disk usage for session directories
- **Processing Time**: Complex issues may take longer to analyze

## Conclusion

This custom command provides a comprehensive interface to the multi-agent issue resolution system, enabling you to:

- **Quickly Start Issue Resolution**: From screenshots or error logs
- **Automated Agent Assignment**: Based on intelligent issue analysis
- **Complete Workflow Management**: Through workflow enforcement system
- **Quality Assurance**: Via original reporter validation
- **Progress Tracking**: Through status monitoring and session management

The system transforms ad-hoc issue resolution into a structured, compliant, and quality-assured process that ensures every issue is properly resolved from identification to validation.

---

**Command Version**: 1.0.0
**Workflow Integration**: Enhanced with original reporter validation
**Claude Code Compatible**: Yes
**Session Management**: Automated
