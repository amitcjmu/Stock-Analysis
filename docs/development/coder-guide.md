# Coder Guide: From Local Development to Merged Pull Request

This guide provides a comprehensive overview of the development workflow, from setting up your local environment to getting your pull request (PR) merged into the main branch. It is intended to help developers, especially those new to the project, understand our processes and quality standards.

## 1. Local Development Setup

Before you start coding, you need to set up your local environment. This includes installing the necessary tools and pre-commit hooks to ensure your code adheres to our quality standards.

### 1.1. Installing Pre-commit Hooks

We use pre-commit hooks to automate checks before you commit your code. This helps catch issues early and ensures that all code in our repository is of high quality.

To install the pre-commit hooks, run the following commands:

```bash
pip install pre-commit
pre-commit install
```

Once installed, the pre-commit hooks will run automatically every time you make a commit.

### 1.2. Understanding the Pre-commit Checks

The pre-commit hooks run a series of checks on your staged files. Here is an overview of the checks that are performed:

*   **Secret Detection**: Scans for any hardcoded secrets like API keys or passwords using Gitleaks.
*   **Python Security Linting**: Uses Bandit to find common security issues in Python code.
*   **Python Code Formatting**: Formats your Python code using Black to ensure a consistent style.
*   **Python Linting**: Checks your Python code for errors and style issues using Flake8.
*   **Type Checking**: Performs static type checking on your Python code using Mypy.
*   **Dockerfile Security**: Scans your Dockerfiles for common security issues using Hadolint.
*   **Basic File Checks**: A series of checks for YAML, JSON, and TOML files, as well as checks for merge conflicts, large files, and private keys.
*   **SQL Checks**: Lints your SQL files using SQLFluff to ensure they are well-formatted.
*   **Credential and Cloud Key Checks**: Scans for hardcoded credentials and cloud service keys.

If any of these checks fail, the commit will be aborted. You will need to fix the issues and stage the files again before you can commit.

## 2. Branching and Committing

We follow a structured branching and commit message convention to keep our repository organized and easy to navigate.

### 2.1. Branching Strategy

All new work should be done on a feature branch. The branch name should be descriptive and follow this format:

`<type>/<short-description>`

Where `<type>` can be one of the following:

*   **feat**: A new feature
*   **fix**: A bug fix
*   **docs**: Documentation changes
*   **style**: Code style changes
*   **refactor**: Code refactoring
*   **test**: Adding or improving tests
*   **chore**: General maintenance

For example, a branch for a new feature that adds user authentication could be named `feat/user-authentication`.

### 2.2. Commit Message Guidelines

We follow the Conventional Commits specification for our commit messages. This helps us generate automated changelogs and makes it easier to track changes.

Each commit message should have the following format:

`<type>(<scope>): <description>`

*   **type**: The type of change (e.g., `feat`, `fix`, `docs`).
*   **scope**: The part of the codebase that is affected (e.g., `backend`, `frontend`, `auth`). This is optional.
*   **description**: A short, imperative-tense description of the change.

For example:

`feat(auth): add user login endpoint`

## 3. The Pull Request Process

Once you have completed your work and pushed your branch to the repository, you can open a pull request (PR) to merge your changes into the `main` or `develop` branch.

### 3.1. Opening a Pull Request

When you open a PR, make sure to provide a clear title and a detailed description of the changes you have made. The PR title should follow the same conventional commit format as your commit messages.

The description should include:

*   A summary of the changes.
*   Any relevant context or background information.
*   Instructions for testing the changes.
*   Screenshots or videos if applicable.

### 3.2. CI/CD and Automated Checks

When you open a PR, a series of automated checks will run to ensure that your changes meet our quality standards. These checks are run by our CI/CD pipeline and include:

*   **PR Validation**: Validates the PR title and description, and checks for any breaking changes.
*   **Code Quality Gate**: Runs linting and type checking for both the frontend and backend code.
*   **Security Check**: Scans for security vulnerabilities and hardcoded secrets.
*   **Test Execution**: Runs our suite of smoke tests to ensure that the application is stable.
*   **Docker Build**: Verifies that the Docker images for the frontend and backend can be built successfully.

You can see the status of these checks on the PR page. If any of the checks fail, you will need to fix the issues and push the changes to your branch.

### 3.3. Code Review

Once all the automated checks have passed, your PR will be reviewed by at least one other developer. The reviewer will check your code for correctness, clarity, and adherence to our coding standards.

You may be asked to make changes based on the feedback from the reviewer. Once you have addressed all the comments and the reviewer has approved your PR, it can be merged.

### 3.4. Merging the Pull Request

After your PR is approved and all checks have passed, a maintainer will merge it into the target branch. Congratulations, your code is now part of the main codebase!

By following this guide, you can ensure that your contributions are of high quality and that the development process is smooth and efficient for everyone. If you have any questions, don't hesitate to ask for help in our development channel.
