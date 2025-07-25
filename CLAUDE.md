## Development Best Practices

### Git History and Code Modification Guidelines
- When solving an issue, always thoroughly review the project's Git history to understand past changes related to the code you intend to impact
- Ensure you comprehensively understand existing codebase support for the area you're modifying
- Validate that your proposed approach remains consistent with past implementation patterns
- Prioritize modifying existing code over adding new code to prevent unnecessary code sprawl
- Before introducing new implementations, carefully assess if existing code can be refactored or extended to meet the current requirements
- Never by pass pre-commit checks with --no-verify unless you have gone through the pre-commit checks at least once and fixed all the issues mentioned by the checks

### Development Environment Configuration
- Use /opt/homebrew/bin/gh for all Git CLI tools and /opt/homebrew/bin/python3.11@ for all Python executions in the app
