# Modularization Test (Short Command)

**Command**: `modtest`

**Description**: Quick modularization analysis - alias for `modularization-test`.

## Usage

```bash
# Quick analysis with default settings (350 LOC threshold)
/modtest

# Custom threshold
/modtest --threshold 400

# Detailed analysis
/modtest --detailed

# Export results
/modtest --export-json report.json
```

This is a shorter alias for the full `modularization-test` command, perfect for quick checks during development.
