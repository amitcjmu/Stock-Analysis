"""
Unit tests for gap detection services.

Tests verify:
- ColumnInspector detects missing/empty/null attributes
- EnrichmentInspector detects missing/incomplete enrichment tables
- Completeness scores are correctly calculated and clamped
- System columns are excluded from gap analysis
- Performance meets targets (<10ms column, <20ms enrichment)
"""
