# Quick Start: Using Architecture Diagrams in PRs

## Step 1: Add Diagrams to Your PR Description

When creating a pull request, use the PR template (`.github/PULL_REQUEST_TEMPLATE.md`) which includes sections for architecture diagrams.

### Example PR Description:

```markdown
## Architecture Overview

### Sequence Diagram
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Cassandra
    
    User->>Frontend: Search Stock
    Frontend->>Backend: API Request
    Backend->>Cassandra: Log Search
    Backend-->>Frontend: Return Results
```

### Architecture Diagram
```mermaid
graph TB
    Frontend[React Frontend] --> API[FastAPI Backend]
    API --> PostgreSQL[(PostgreSQL)]
    API --> Cassandra[(Cassandra)]
```
```

## Step 2: Create New Diagrams

1. Create a `.mmd` file in `docs/architecture/`:

```bash
touch docs/architecture/my-feature-sequence.mmd
```

2. Write your Mermaid diagram:

```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Request
    B-->>A: Response
```

3. Reference it in your PR or documentation.

## Step 3: Automatic Generation

The GitHub Action (`.github/workflows/generate-diagrams.yml`) will:
- ✅ Automatically generate PNG/SVG images from `.mmd` files
- ✅ Post diagrams as comments on your PR
- ✅ Commit generated images to the repository

## Step 4: View Diagrams

- **On GitHub**: Diagrams render automatically in markdown
- **In VS Code**: Install "Markdown Preview Mermaid Support" extension
- **Online**: Use [Mermaid Live Editor](https://mermaid.live/) to test

## Common Diagram Types

### Sequence Diagram
```mermaid
sequenceDiagram
    A->>B: Request
    B-->>A: Response
```

### Flowchart
```mermaid
flowchart TD
    Start([Start]) --> Process[Process]
    Process --> End([End])
```

### Architecture Diagram
```mermaid
graph TB
    A[Component A] --> B[Component B]
    B --> C[Component C]
```

## Tips

1. **Keep it simple**: Focus on the key interactions
2. **Use colors**: Style important components
3. **Add notes**: Use `Note over` for explanations
4. **Update diagrams**: Keep them in sync with code changes

## Need Help?

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- See `docs/architecture/README.md` for more details

