# Database Schema Documentation Guide

This guide explains the two-part approach to database documentation in this project, designed to keep information accurate, version-controlled, and easily accessible to the development team.

## Part 1: In-Code Schema Comments

The primary source of truth for all database documentation is within the SQLAlchemy model definitions themselves. Every table and column is documented directly in the Python code.

### Why This Approach?

-   **Version Controlled**: Documentation lives with the code that defines the schema. When a model changes, the documentation changes in the same commit.
-   **Single Source of Truth**: Prevents documentation drift where external documents become outdated. The code is the documentation.
-   **Developer-Friendly**: Developers can see the purpose of a column directly in their IDE without switching context.

### How It's Implemented

We use the `comment` argument in SQLAlchemy's `Column` constructor. Alembic, our database migration tool, automatically picks up these comments and generates the necessary `COMMENT ON COLUMN` DDL statements.

**Example (`backend/app/models/client_account.py`):**
```python
class ClientAccount(Base):
    """
    Represents a client organization in the multi-tenant system.
    Each client account is a distinct, isolated entity with its own users, engagements, and data.
    """
    __tablename__ = "client_accounts"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, comment="Unique identifier for the client account.")
    name = Column(String(255), nullable=False, comment="The official name of the client company.")
    # ... and so on for all other columns
```

When adding or modifying a column, it is **mandatory** to also add or update its comment to reflect its purpose.

## Part 2: Automated HTML Documentation Generation

While in-code comments are the source of truth, they aren't easily browsable as a whole. To solve this, we use **SchemaSpy**, a tool that automatically generates a comprehensive and interactive HTML documentation site from the live database schema, including all the comments.

### Features of the Generated Documentation:

-   Interactive Entity-Relationship (ER) diagrams.
-   Browsable list of all tables, columns, and views.
-   Displays all comments associated with tables and columns.
-   Shows constraints, indexes, and other metadata.

### How to Generate the Documentation

A helper script is provided to automate this process.

**Requirements:**
1.  Docker must be installed and running.
2.  The project's Docker environment must be running (`docker-compose up`).

**Steps:**
1.  Open your terminal at the project root.
2.  Run the generation script:
    ```bash
    ./scripts/generate_db_docs.sh
    ```
3.  The script will pull the SchemaSpy Docker image, connect to the local development database, and generate the documentation.

### Viewing the Documentation

Once the script finishes, the documentation will be available in the `docs/database/` directory (which is excluded from Git by `.gitignore`).

Open the main entry point in your browser to view the site:
`docs/database/index.html`

It is recommended to regenerate the documentation after any significant database schema changes to ensure the browsable version stays up-to-date. 