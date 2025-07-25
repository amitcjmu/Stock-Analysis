# Python Version Requirements

This project requires **Python 3.11** for consistency across all environments.

## Current Setup
- **Docker**: Python 3.11-slim-bookworm (see `backend/Dockerfile`)
- **Pre-commit hooks**: Configured for Python 3.11
- **Backend code**: Designed for Python 3.11 features

## Local Development Requirements
To run pre-commit hooks locally, you need Python 3.11 installed:

### macOS (using Homebrew)
```bash
brew install python@3.11
```

### macOS (using pyenv)
```bash
pyenv install 3.11
pyenv local 3.11
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

## Pre-commit Hook Issues
If you encounter errors like:
```
RuntimeError: failed to find interpreter for Builtin discover of python_spec='python3.11'
```

This means Python 3.11 is not installed on your system. You can either:
1. Install Python 3.11 locally (recommended)
2. Use `git commit --no-verify` to bypass pre-commit hooks (not recommended for production)
3. Run all code quality checks inside Docker where Python 3.11 is available

## Docker Development
The recommended approach is to use Docker for development to ensure version consistency:
```bash
docker-compose up -d
```

This ensures all developers use the same Python version and dependencies.
