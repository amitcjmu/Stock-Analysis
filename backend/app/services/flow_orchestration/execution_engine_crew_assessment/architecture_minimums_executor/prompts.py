"""
Prompts for architecture minimums compliance validation

Prompt templates for three-level compliance validation using CrewAI agents.
"""

# Three-level compliance validation prompt template
THREE_LEVEL_COMPLIANCE_PROMPT = """
You are validating technology compliance for cloud migration assessment using a three-level approach.

## Level 1: OS Compliance
For each asset, validate the operating system and version against engagement standards:
- Extract operating_system and os_version from asset data
- Use the eol_catalog_lookup tool to check EOL dates
- If cache miss, use rag_eol_enrichment to get EOL data
- Compare against engagement minimum OS requirements

## Level 2: Application (COTS) Compliance
For COTS applications detected in the technology stack:
- Identify commercial off-the-shelf software (SAP, Oracle EBS, Salesforce, etc.)
- Check version against vendor support lifecycle
- Use eol_catalog_lookup first, then rag_eol_enrichment if needed

## Level 3: Component Compliance
For technology components (databases, runtimes, frameworks):
- Validate database_type and database_version
- Check runtime versions (Java, .NET, Node.js, Python)
- Verify framework versions meet engagement minimums

## Asset Data
{assets}

## Engagement Standards
{engagement_standards}

## Instructions
1. For each asset, perform all three levels of validation
2. Use eol_catalog_lookup tool for each technology to check cached EOL dates
3. If cache_hit is false, use rag_eol_enrichment to get and cache EOL data
4. After getting EOL data, use asset_product_linker to link the asset to the product
5. Return JSON with this exact structure:

{{
    "checked_items": [
        {{
            "asset_id": "uuid-string",
            "application_name": "string",
            "level": "os|application|component",
            "category": "operating_system|database|runtime|framework|cots",
            "technology": "string",
            "current_version": "string",
            "eol_date": "YYYY-MM-DD or null",
            "eol_status": "active|eol_soon|eol_expired|unknown",
            "is_compliant": true/false,
            "issue": "string or null",
            "severity": "critical|high|medium|low or null",
            "source": "catalog|rag|engagement_standards"
        }}
    ],
    "summary": {{
        "total_checked": number,
        "compliant": number,
        "non_compliant": number,
        "eol_expired": number,
        "eol_soon": number,
        "by_level": {{
            "os": {{"checked": n, "compliant": n}},
            "application": {{"checked": n, "compliant": n}},
            "component": {{"checked": n, "compliant": n}}
        }}
    }},
    "recommendations": ["string"]
}}
"""
