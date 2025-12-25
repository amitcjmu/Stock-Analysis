# Architecture Diagrams

This directory contains architecture diagrams for the Stock Analysis Platform, generated using [Mermaid](https://mermaid.js.org/).

## Available Diagrams

### 1. Cassandra Integration Sequence Diagram
**File**: `cassandra-integration-sequence.mmd`

Shows the sequence of operations when a user searches for a stock, including:
- Frontend request flow
- Backend API processing
- Cache checking
- Database queries
- Cassandra logging
- Search history retrieval

### 2. Cassandra Architecture Diagram
**File**: `cassandra-architecture.mmd`

High-level architecture showing:
- Frontend layer
- API layer
- Data layer (PostgreSQL and Cassandra)
- Cassandra table structure

### 3. Stock Search Flow Diagram
**File**: `stock-search-flow.mmd`

Flowchart showing the complete stock search process:
- Cache checking
- Database search
- API fallback
- Cassandra logging
- Result caching

## How to Use

### Viewing Diagrams

1. **GitHub**: Mermaid diagrams are automatically rendered in markdown files on GitHub
2. **VS Code**: Install the "Markdown Preview Mermaid Support" extension
3. **Online**: Use [Mermaid Live Editor](https://mermaid.live/)

### Adding New Diagrams

1. Create a new `.mmd` file in this directory
2. Write your Mermaid diagram code
3. Reference it in your PR description or documentation:

```markdown
## Architecture

\`\`\`mermaid
graph TB
    A --> B
\`\`\`
```

### Generating Images

The GitHub Action workflow (`.github/workflows/generate-diagrams.yml`) automatically:
- Generates PNG and SVG images from `.mmd` files
- Posts them as comments on pull requests
- Commits generated images to `docs/architecture/generated/`

### Mermaid Syntax Reference

- **Sequence Diagrams**: `sequenceDiagram`
- **Flowcharts**: `flowchart TD` or `graph TB`
- **Class Diagrams**: `classDiagram`
- **State Diagrams**: `stateDiagram-v2`
- **Gantt Charts**: `gantt`

See [Mermaid Documentation](https://mermaid.js.org/intro/) for full syntax.

## Best Practices

1. **Keep diagrams focused**: One diagram per concept
2. **Use descriptive labels**: Make components and flows clear
3. **Update diagrams with code**: Keep diagrams in sync with implementation
4. **Add to PRs**: Include relevant diagrams in pull request descriptions
5. **Version control**: Commit `.mmd` source files, not just generated images

## Example: Adding a Diagram to a PR

```markdown
## Architecture Changes

This PR adds Cassandra integration for search history. The flow is:

\`\`\`mermaid
sequenceDiagram
    participant User
    participant API
    participant Cassandra
    User->>API: Search Stock
    API->>Cassandra: Log Search
    Cassandra-->>API: Success
    API-->>User: Results
\`\`\`
```

## Tools

- **Mermaid Live Editor**: https://mermaid.live/
- **VS Code Extension**: Markdown Preview Mermaid Support
- **GitHub**: Native Mermaid support in markdown
- **Mermaid CLI**: For generating images programmatically

