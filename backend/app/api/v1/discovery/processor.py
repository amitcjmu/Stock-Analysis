"""
CMDB Data Processor
Handles intelligent data processing and validation with agentic intelligence.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import io
from datetime import datetime
import re

from app.services.crewai_service import CrewAIService
from .models import AssetCoverage

logger = logging.getLogger(__name__)


class CMDBDataProcessor:
    """Handles intelligent data processing and validation."""
    
    def __init__(self):
        self.crewai_service = CrewAIService()
        
    def parse_file_content(self, content: str, file_type: str, filename: str = "") -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """Parse file content intelligently based on file type and content."""
        try:
            # Try structured data parsing first
            df = self._parse_structured_data(content, file_type)
            if df is not None:
                return df, {"type": "structured", "parsed_as": "dataframe"}
            
            # For non-structured content, extract text and delegate to AI crew
            text_content = self._extract_text_content(content, file_type, filename)
            if text_content:
                # Let AI crew analyze the text content
                ai_analysis = self._analyze_text_with_ai_crew(text_content, file_type, filename)
                return None, {
                    "type": "unstructured", 
                    "content": text_content,
                    "ai_analysis": ai_analysis
                }
            
            # Fallback for unknown content
            return None, {
                "type": "unknown",
                "content": content[:1000] if len(content) > 1000 else content,
                "ai_analysis": {"error": f"Unable to process file type: {file_type}"}
            }
            
        except Exception as e:
            logger.error(f"Error parsing file content: {e}")
            # Even on error, try to get AI crew insights
            try:
                ai_analysis = self._analyze_text_with_ai_crew(content[:2000], file_type, filename)
                return None, {
                    "type": "error",
                    "error": str(e),
                    "ai_analysis": ai_analysis
                }
            except:
                raise ValueError(f"Failed to parse file: {str(e)}")
    
    def _parse_structured_data(self, content: str, file_type: str) -> Optional[pd.DataFrame]:
        """Parse structured data formats (CSV, JSON, Excel)."""
        try:
            if file_type in ['text/csv', 'application/csv']:
                return pd.read_csv(io.StringIO(content))
            elif file_type in ['application/json']:
                data = json.loads(content)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame([data])
            elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                # For Excel files, we'd need to handle binary content differently
                # This is a simplified version for demo purposes
                return pd.read_csv(io.StringIO(content))
            else:
                return None
        except:
            return None
    
    def _extract_text_content(self, content: str, file_type: str, filename: str) -> str:
        """Extract text content from various file types."""
        try:
            if file_type == 'application/pdf':
                # For PDF files, return content as-is for now
                # In production, you'd use a proper PDF parser like PyPDF2 or pdfplumber
                return f"PDF Document: {filename}\n\nContent analysis required by AI crew.\n\nNote: This appears to be a PDF document. AI crew will analyze the document structure and extract relevant information for migration assessment."
            
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return f"Word Document: {filename}\n\nContent: {content[:2000]}..."
            
            elif file_type == 'text/markdown':
                return f"Markdown Document: {filename}\n\n{content}"
            
            elif file_type.startswith('text/'):
                return content
            
            else:
                # For unknown types, return basic info
                return f"Document: {filename}\nType: {file_type}\nContent preview: {content[:500]}..."
                
        except Exception as e:
            logger.warning(f"Error extracting text content: {e}")
            return f"File: {filename}\nContent extraction error, delegating to AI crew for analysis."
    
    def _analyze_text_with_ai_crew(self, text_content: str, file_type: str, filename: str) -> Dict[str, Any]:
        """Use AI crew to analyze unstructured content."""
        try:
            # Create a prompt for the AI crew to analyze the content
            analysis_prompt = f"""
            Analyze this content for migration assessment purposes:
            
            Filename: {filename}
            File Type: {file_type}
            
            Content:
            {text_content[:2000]}
            
            Please identify:
            1. What type of information this contains (applications, servers, documentation, etc.)
            2. Any specific assets, applications, or infrastructure mentioned
            3. Relevance to cloud migration planning (1-10 scale)
            4. Key insights that would help with migration assessment
            5. Recommended next steps for processing this information
            """
            
            # For now, return a structured response
            # In production, you'd call the actual AI crew service
            return {
                "content_type": self._detect_content_type(text_content, filename),
                "relevance_score": self._calculate_relevance_score(text_content),
                "insights": self._extract_key_insights(text_content, filename),
                "assets_mentioned": self._find_asset_references(text_content),
                "recommendation": self._get_processing_recommendation(file_type, text_content)
            }
            
        except Exception as e:
            logger.error(f"AI crew analysis failed: {e}")
            return {
                "content_type": "unknown",
                "relevance_score": 50,
                "insights": ["Content requires manual review"],
                "assets_mentioned": [],
                "recommendation": "Manual analysis recommended"
            }
    
    def _detect_content_type(self, content: str, filename: str) -> str:
        """Detect the type of content based on keywords and patterns."""
        content_lower = content.lower()
        
        # Application-related keywords
        app_keywords = ['application', 'service', 'api', 'microservice', 'database', 'web app']
        if any(keyword in content_lower for keyword in app_keywords):
            return "application_documentation"
        
        # Infrastructure keywords
        infra_keywords = ['server', 'vm', 'instance', 'infrastructure', 'network', 'storage']
        if any(keyword in content_lower for keyword in infra_keywords):
            return "infrastructure_documentation"
        
        # Architecture keywords
        arch_keywords = ['architecture', 'design', 'diagram', 'component', 'system']
        if any(keyword in content_lower for keyword in arch_keywords):
            return "architecture_documentation"
        
        # Migration keywords
        migration_keywords = ['migration', 'modernization', 'cloud', 'aws', 'azure', 'gcp']
        if any(keyword in content_lower for keyword in migration_keywords):
            return "migration_documentation"
        
        # Based on file extension
        if filename.lower().endswith('.pdf'):
            return "pdf_document"
        elif filename.lower().endswith(('.md', '.txt')):
            return "text_documentation"
        
        return "general_documentation"
    
    def _calculate_relevance_score(self, content: str) -> int:
        """Calculate relevance score for migration assessment."""
        content_lower = content.lower()
        score = 50  # Base score
        
        # Positive indicators
        positive_keywords = [
            'application', 'database', 'server', 'infrastructure', 'migration',
            'cloud', 'architecture', 'system', 'service', 'api', 'dependency'
        ]
        
        for keyword in positive_keywords:
            if keyword in content_lower:
                score += 5
        
        # Specific technology mentions
        tech_keywords = ['java', 'python', '.net', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb']
        for tech in tech_keywords:
            if tech in content_lower:
                score += 3
        
        return min(100, max(10, score))
    
    def _extract_key_insights(self, content: str, filename: str) -> List[str]:
        """Extract key insights from the content."""
        insights = []
        content_lower = content.lower()
        
        if 'pdf' in filename.lower():
            insights.append("PDF document detected - may contain detailed technical specifications")
        
        if any(word in content_lower for word in ['application', 'system', 'service']):
            insights.append("Contains application or system information relevant to migration")
        
        if any(word in content_lower for word in ['database', 'sql', 'oracle', 'mysql']):
            insights.append("Database information detected - important for data migration planning")
        
        if any(word in content_lower for word in ['architecture', 'design', 'diagram']):
            insights.append("Architectural information found - valuable for understanding system structure")
        
        if not insights:
            insights.append("Document requires further analysis to determine migration relevance")
        
        return insights
    
    def _find_asset_references(self, content: str) -> List[str]:
        """Find potential asset references in the content."""
        assets = []
        
        # Look for common naming patterns
        patterns = [
            r'\b[A-Z][A-Za-z0-9-]+(?:Server|DB|App|Service)\b',
            r'\b(?:app|db|srv|web|api)-[A-Za-z0-9-]+\b',
            r'\b[A-Za-z0-9]+\.[A-Za-z0-9]+\.com\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            assets.extend(matches[:5])  # Limit to 5 matches per pattern
        
        return list(set(assets))[:10]  # Return unique assets, max 10
    
    def _get_processing_recommendation(self, file_type: str, content: str) -> str:
        """Get recommendation for how to process this content."""
        if file_type == 'application/pdf':
            return "Extract structured data using PDF parsing tools and analyze for application inventory"
        elif 'application' in content.lower() or 'system' in content.lower():
            return "Analyze for application metadata and add to asset inventory"
        elif 'server' in content.lower() or 'infrastructure' in content.lower():
            return "Extract infrastructure details for migration planning"
        else:
            return "Review manually and extract relevant migration information"
    
    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the structure and quality of the data."""
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
        
        # Calculate basic data quality metrics
        total_cells = len(df) * len(df.columns)
        null_count = df.isnull().sum().sum()
        null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
        duplicate_count = len(df) - len(df.drop_duplicates())
        
        # Calculate basic quality score
        base_score = 100.0
        base_score -= min(30.0, null_percentage)  # Deduct up to 30 points for nulls
        if len(df) > 0:
            base_score -= min(20.0, (duplicate_count / len(df)) * 100)  # Deduct up to 20 points for duplicates
        
        # Ensure quality_score is a valid integer between 0 and 100
        quality_score = max(0, min(100, int(base_score)))
        
        analysis['quality_score'] = quality_score
        analysis['null_percentage'] = null_percentage
        analysis['duplicate_count'] = duplicate_count
        
        return analysis
    
    def identify_asset_types(self, df: pd.DataFrame) -> AssetCoverage:
        """Identify different types of assets in the data with improved heuristics."""
        columns = [col.lower() for col in df.columns]
        
        # Initialize counters
        applications = 0
        servers = 0
        databases = 0
        dependencies = 0
        
        # Check if there's an explicit asset type column (including workload_type)
        type_columns = ['ci_type', 'type', 'asset_type', 'category', 'classification', 'sys_class_name', 'workload_type', 'workload type']
        type_column = None
        for col in df.columns:
            if col.lower().replace(' ', '_') in [tc.replace(' ', '_') for tc in type_columns]:
                type_column = col
                break
        
        if type_column:
            # Use explicit type column for classification
            type_values = df[type_column].str.lower().fillna('unknown')
            
            # Enhanced patterns for workload type detection
            # Application indicators (including workload-specific patterns)
            app_patterns = ['application', 'app', 'service', 'software', 'business_service', 'app server', 'application server', 'web server', 'api server']
            applications = sum(type_values.str.contains('|'.join(app_patterns), na=False))
            
            # Database indicators (including workload-specific patterns)
            db_patterns = ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb', 'db server', 'database server']
            databases = sum(type_values.str.contains('|'.join(db_patterns), na=False))
            
            # Server indicators (catch-all for generic servers)
            server_patterns = ['server', 'host', 'machine', 'vm', 'instance', 'computer', 'node']
            # Only count as generic servers if not already counted as app or db servers
            remaining_servers = len(df) - applications - databases
            
            # For workload type, we need to be more specific about what counts as a "generic server"
            if 'workload' in type_column.lower():
                # With workload type, count specific server types that aren't apps or databases
                generic_server_patterns = ['file server', 'print server', 'mail server', 'dns server', 'dhcp server', 'domain controller']
                servers = sum(type_values.str.contains('|'.join(generic_server_patterns), na=False))
                
                # Add any remaining unclassified items as servers
                unclassified = len(df) - applications - databases - servers
                if unclassified > 0:
                    servers += unclassified
            else:
                # For non-workload columns, use original server detection
                servers = sum(type_values.str.contains('|'.join(server_patterns), na=False))
            
            logger.info(f"Asset type detection from column '{type_column}': Apps={applications}, DBs={databases}, Servers={servers}")
            
        else:
            # Fallback to heuristic-based detection using field patterns
            
            # Look for application-specific fields
            app_fields = ['version', 'business_service', 'application_owner', 'related_ci']
            app_score = sum(1 for field in app_fields if any(field in col for col in columns))
            
            # Look for server-specific fields
            server_fields = ['ip_address', 'hostname', 'os', 'cpu', 'memory', 'ram']
            server_score = sum(1 for field in server_fields if any(field in col for col in columns))
            
            # Look for database-specific fields
            db_fields = ['database', 'schema', 'instance', 'port', 'connection']
            db_score = sum(1 for field in db_fields if any(field in col for col in columns))
            
            # Classify based on field patterns
            total_rows = len(df)
            if app_score >= server_score and app_score >= db_score:
                applications = total_rows
            elif server_score >= app_score and server_score >= db_score:
                servers = total_rows
            elif db_score >= app_score and db_score >= server_score:
                databases = total_rows
            else:
                # Default to applications if unclear
                applications = total_rows
        
        # Look for dependency relationships
        dep_fields = ['related_ci', 'depends_on', 'relationship', 'parent_ci', 'child_ci']
        if any(field in ' '.join(columns) for field in dep_fields):
            # Count non-empty dependency relationships
            for col in df.columns:
                if any(dep_field in col.lower() for dep_field in dep_fields):
                    dependencies = df[col].notna().sum()
                    break
        
        return AssetCoverage(
            applications=applications,
            servers=servers,
            databases=databases,
            dependencies=dependencies
        )
    
    def identify_missing_fields(self, df: pd.DataFrame) -> List[str]:
        """Identify missing required fields using enhanced pattern analysis and learned mappings."""
        columns = df.columns.tolist()
        missing_fields = []
        
        # Determine primary asset type
        coverage = self.identify_asset_types(df)
        primary_type = 'application'
        if coverage.servers > coverage.applications and coverage.servers > coverage.databases:
            primary_type = 'server'
        elif coverage.databases > coverage.applications and coverage.databases > coverage.servers:
            primary_type = 'database'
        
        # Use pattern analysis to understand available data
        try:
            from app.services.tools.field_mapping_tool import field_mapping_tool
            
            # Prepare sample data for pattern analysis
            sample_rows = []
            for _, row in df.head(10).iterrows():
                sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
                sample_rows.append(sample_row)
            
            # Get pattern analysis results
            pattern_analysis = field_mapping_tool.analyze_data_patterns(columns, sample_rows, primary_type)
            column_mappings = pattern_analysis.get("column_analysis", {})
            confidence_scores = pattern_analysis.get("confidence_scores", {})
            
            logger.info(f"Pattern analysis found {len(column_mappings)} field mappings")
            
        except Exception as e:
            logger.warning(f"Pattern analysis failed, using fallback: {e}")
            column_mappings = {}
            confidence_scores = {}
        
        # Define essential fields by asset type (focused on migration assessment needs)
        if primary_type == 'application':
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner', 
                'Criticality'
            ]
        elif primary_type == 'server':
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
            ]
        elif primary_type == 'mixed':
            # For mixed asset types, focus on the most critical migration fields
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
            ]
        else:  # database
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
            ]
        
        # Check each essential field
        for essential_field in essential_fields:
            field_found = False
            
            # Check if any column maps to this essential field with high confidence
            for column, mapped_field in column_mappings.items():
                if mapped_field == essential_field:
                    confidence = confidence_scores.get(column, 0.0)
                    if confidence > 0.6:  # Accept medium to high confidence mappings
                        field_found = True
                        logger.info(f"Found mapping: {column} → {essential_field} (confidence: {confidence:.2f})")
                        break
            
            # If not found through pattern analysis, try fallback mapping
            if not field_found:
                field_found = self._check_fallback_field_mapping(essential_field, columns)
            
            if not field_found:
                missing_fields.append(essential_field)
                logger.info(f"Missing field: {essential_field}")
        
        return missing_fields
    
    def _check_fallback_field_mapping(self, essential_field: str, available_columns: List[str]) -> bool:
        """Fallback method to check for field mappings using simple name matching."""
        columns_lower = [col.lower().strip() for col in available_columns]
        
        # Simple fallback mappings for common cases (focused on migration assessment)
        fallback_mappings = {
            'Asset Name': ['name', 'hostname', 'asset_name', 'ci_name', 'server_name'],
            'Environment': ['environment', 'env', 'stage', 'tier'],
            'Business Owner': ['business_owner', 'owner', 'application_owner', 'app_owner', 'responsible_party', 'contact', 'primary_contact'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance', 'critical', 'business_priority']
        }
        
        variations = fallback_mappings.get(essential_field, [])
        return any(variation in columns_lower for variation in variations)
    
    def suggest_processing_steps(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[str]:
        """Suggest data processing steps based on analysis."""
        processing_steps = []
        
        # Check for high null values
        if analysis['quality_score'] < 70:
            processing_steps.append("Clean missing data and fill null values")
        
        # Check for duplicates
        if analysis['duplicate_count'] > 0:
            processing_steps.append(f"Remove {analysis['duplicate_count']} duplicate records")
        
        # Check for data type issues
        if 'object' in str(analysis['data_types'].values()):
            processing_steps.append("Standardize data types and formats")
        
        # Check for naming consistency
        columns = df.columns.tolist()
        if any(' ' in col or col != col.lower() for col in columns):
            processing_steps.append("Normalize column names and formats")
        
        # Check for data validation
        processing_steps.append("Validate asset relationships and dependencies")
        processing_steps.append("Enrich data with additional metadata")
        
        return processing_steps 