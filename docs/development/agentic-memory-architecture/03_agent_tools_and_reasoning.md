# Agent Tools and Reasoning Framework

## Philosophy: Tools, Not Rules

The core principle is to provide agents with powerful tools for investigation and analysis, while keeping all reasoning and decision-making within the AI agents themselves. Tools return **facts and evidence**, agents provide **intelligence and reasoning**.

## Agent Tool Architecture

### Core Tool Categories

#### 1. Data Investigation Tools
Tools that help agents inspect and understand raw data without pre-interpreting it.

#### 2. Pattern Query Tools  
Tools that let agents search their own discovered knowledge without being bound by it.

#### 3. Analysis Tools
Tools that decompose complex data into analyzable components.

#### 4. Learning Tools
Tools that help agents store and refine their discoveries.

## Tool Implementations

### PatternSearchTool

**Purpose**: Allow agents to query previously discovered patterns as evidence for their reasoning.

```python
class PatternSearchTool(BaseTool):
    name = "pattern_search"
    description = """Search previously discovered patterns for evidence related to your analysis.
    This tool returns evidence, not conclusions - you must reason about the relevance and reliability of patterns."""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        super().__init__()
        self.memory_manager = memory_manager
    
    def _run(self, search_query: str, pattern_type: str = None, min_accuracy: float = 0.5) -> str:
        """
        Search for patterns based on agent's reasoning needs.
        
        Args:
            search_query: What the agent wants to search for
            pattern_type: Specific type of pattern (optional)
            min_accuracy: Minimum accuracy threshold for returned patterns
        
        Returns:
            Formatted evidence for agent reasoning
        """
        try:
            patterns = await self.memory_manager.tier3.search_patterns(
                search_query=search_query,
                pattern_type=pattern_type
            )
            
            # Filter by accuracy threshold
            reliable_patterns = [p for p in patterns if p['accuracy'] >= min_accuracy]
            
            if not reliable_patterns:
                return f"No reliable patterns found for '{search_query}' with accuracy >= {min_accuracy}"
            
            # Format evidence for agent reasoning
            evidence_summary = f"Found {len(reliable_patterns)} patterns for '{search_query}':\n\n"
            
            for i, pattern in enumerate(reliable_patterns[:5], 1):  # Top 5 patterns
                evidence_summary += f"{i}. Pattern: {pattern['pattern_value']}\n"
                evidence_summary += f"   Type: {pattern['pattern_type']}\n"
                evidence_summary += f"   Accuracy: {pattern['accuracy']:.1%} ({pattern['validation_count']} validations)\n"
                evidence_summary += f"   Confidence: {pattern['confidence_level']}\n"
                evidence_summary += f"   Insights: {json.dumps(pattern['insights'], indent=2)}\n"
                evidence_summary += f"   Discovery context: {pattern['discovery_context']}\n"
                if pattern['last_confirmed']:
                    evidence_summary += f"   Last confirmed: {pattern['last_confirmed']}\n"
                evidence_summary += "\n"
            
            evidence_summary += f"\nNote: These are historical patterns. Evaluate their relevance to your current analysis."
            
            return evidence_summary
            
        except Exception as e:
            return f"Error searching patterns: {str(e)}"
    
    async def arun(self, search_query: str, pattern_type: str = None, min_accuracy: float = 0.5) -> str:
        return self._run(search_query, pattern_type, min_accuracy)
```

### AssetDataQueryTool

**Purpose**: Allow agents to inspect specific aspects of asset data based on their hypotheses.

```python
class AssetDataQueryTool(BaseTool):
    name = "asset_data_query"
    description = """Inspect specific aspects of asset data to test your hypotheses.
    Ask focused questions about the data - this tool provides facts, you provide the interpretation."""
    
    def __init__(self, db_session):
        super().__init__()
        self.db = db_session
    
    def _run(self, asset_id: str, query_focus: str, additional_context: str = None) -> str:
        """
        Query specific asset data based on agent's investigative needs.
        
        Args:
            asset_id: ID of asset to investigate
            query_focus: What aspect to investigate (hostname, ports, software, etc.)
            additional_context: Additional context for the query
        
        Returns:
            Relevant factual data for agent analysis
        """
        try:
            asset = self._get_asset_by_id(asset_id)
            if not asset:
                return f"Asset {asset_id} not found"
            
            focus = query_focus.lower()
            
            if 'hostname' in focus:
                return self._analyze_hostname_data(asset)
            elif 'port' in focus or 'network' in focus:
                return self._analyze_network_data(asset)
            elif 'software' in focus or 'application' in focus:
                return self._analyze_software_data(asset)
            elif 'hardware' in focus or 'system' in focus:
                return self._analyze_hardware_data(asset)
            elif 'dependency' in focus or 'connection' in focus:
                return self._analyze_dependency_data(asset)
            elif 'business' in focus or 'usage' in focus:
                return self._analyze_business_data(asset)
            else:
                return self._analyze_general_data(asset)
                
        except Exception as e:
            return f"Error querying asset data: {str(e)}"
    
    def _analyze_hostname_data(self, asset) -> str:
        """Provide hostname analysis facts"""
        hostname = asset.hostname or 'Not specified'
        
        analysis = f"Hostname Analysis for {asset.name}:\n"
        analysis += f"Full hostname: {hostname}\n"
        
        if hostname and hostname != 'Not specified':
            # Decompose hostname
            parts = hostname.split('.')
            segments = hostname.split('-')
            
            analysis += f"Domain components: {parts}\n"
            analysis += f"Hyphen segments: {segments}\n"
            analysis += f"Length: {len(hostname)} characters\n"
            analysis += f"Contains numbers: {'Yes' if any(c.isdigit() for c in hostname) else 'No'}\n"
            
            # Pattern indicators (facts only, no interpretation)
            indicators = []
            if any(word in hostname.lower() for word in ['db', 'database', 'sql']):
                indicators.append('database-related terms')
            if any(word in hostname.lower() for word in ['web', 'www', 'http']):
                indicators.append('web-related terms')
            if any(word in hostname.lower() for word in ['app', 'application', 'svc', 'service']):
                indicators.append('application-related terms')
            if any(word in hostname.lower() for word in ['prod', 'production']):
                indicators.append('production environment indicators')
            if any(word in hostname.lower() for word in ['dev', 'development', 'test', 'staging']):
                indicators.append('non-production environment indicators')
            
            if indicators:
                analysis += f"Terminology indicators found: {', '.join(indicators)}\n"
        
        return analysis
    
    def _analyze_network_data(self, asset) -> str:
        """Provide network configuration facts"""
        analysis = f"Network Analysis for {asset.name}:\n"
        analysis += f"IP Address: {getattr(asset, 'ip_address', 'Not specified')}\n"
        
        # Check for port information in raw data
        raw_data = getattr(asset, 'raw_import_data', {})
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data) if raw_data.startswith('{') else {}
        
        if ports := raw_data.get('open_ports') or raw_data.get('ports'):
            analysis += f"Open ports detected: {ports}\n"
            
            # Port analysis (facts only)
            if isinstance(ports, (list, str)):
                port_list = ports if isinstance(ports, list) else [ports]
                port_analysis = []
                
                for port in port_list:
                    port_num = str(port)
                    if port_num in ['80', '443', '8080', '8443']:
                        port_analysis.append(f"{port_num} (HTTP/HTTPS)")
                    elif port_num in ['3306', '3307']:
                        port_analysis.append(f"{port_num} (MySQL)")
                    elif port_num in ['5432', '5433']:
                        port_analysis.append(f"{port_num} (PostgreSQL)")
                    elif port_num in ['1433', '1434']:
                        port_analysis.append(f"{port_num} (SQL Server)")
                    elif port_num in ['22']:
                        port_analysis.append(f"{port_num} (SSH)")
                    elif port_num in ['21']:
                        port_analysis.append(f"{port_num} (FTP)")
                    else:
                        port_analysis.append(f"{port_num} (Unknown service)")
                
                analysis += f"Port details: {', '.join(port_analysis)}\n"
        
        return analysis
    
    def _analyze_software_data(self, asset) -> str:
        """Provide software and application facts"""
        analysis = f"Software Analysis for {asset.name}:\n"
        
        # Check various software-related fields
        os_info = getattr(asset, 'operating_system', None)
        if os_info:
            analysis += f"Operating System: {os_info}\n"
        
        # Check raw data for software information
        raw_data = getattr(asset, 'raw_import_data', {})
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data) if raw_data.startswith('{') else {}
        
        software_fields = ['software', 'applications', 'services', 'processes']
        for field in software_fields:
            if value := raw_data.get(field):
                analysis += f"{field.title()}: {value}\n"
        
        # Check for version information
        version_fields = ['version', 'software_version', 'app_version']
        for field in version_fields:
            if value := raw_data.get(field) or getattr(asset, field, None):
                analysis += f"Version info: {value}\n"
        
        return analysis
    
    def _get_asset_by_id(self, asset_id: str):
        """Retrieve asset from database"""
        # Implementation would query the database
        # This is a placeholder for the actual database query
        pass
    
    async def arun(self, asset_id: str, query_focus: str, additional_context: str = None) -> str:
        return self._run(asset_id, query_focus, additional_context)
```

### HostnameAnalysisTool

**Purpose**: Break down hostnames into analyzable components without pre-interpreting their meaning.

```python
class HostnameAnalysisTool(BaseTool):
    name = "hostname_analysis"
    description = """Decompose hostnames into structural components for your analysis.
    This tool provides hostname structure facts - you determine their significance."""
    
    def _run(self, hostname: str) -> str:
        """
        Analyze hostname structure and components.
        
        Args:
            hostname: The hostname to analyze
        
        Returns:
            Structured breakdown of hostname components
        """
        if not hostname or hostname.lower() in ['none', 'null', 'not specified', '']:
            return "No hostname provided for analysis"
        
        analysis = f"Hostname Structure Analysis: '{hostname}'\n\n"
        
        # Basic characteristics
        analysis += f"Length: {len(hostname)} characters\n"
        analysis += f"Character types: "
        char_types = []
        if any(c.islower() for c in hostname):
            char_types.append("lowercase letters")
        if any(c.isupper() for c in hostname):
            char_types.append("uppercase letters")
        if any(c.isdigit() for c in hostname):
            char_types.append("numbers")
        if any(c in '-_.@' for c in hostname):
            char_types.append("separators")
        analysis += ", ".join(char_types) + "\n\n"
        
        # Domain decomposition
        if '.' in hostname:
            domain_parts = hostname.split('.')
            analysis += f"Domain components ({len(domain_parts)} parts):\n"
            for i, part in enumerate(domain_parts):
                analysis += f"  {i+1}. '{part}'\n"
        
        # Hyphen segmentation
        if '-' in hostname:
            hyphen_segments = hostname.split('-')
            analysis += f"\nHyphen segments ({len(hyphen_segments)} parts):\n"
            for i, segment in enumerate(hyphen_segments):
                analysis += f"  {i+1}. '{segment}'\n"
        
        # Underscore segmentation
        if '_' in hostname:
            underscore_segments = hostname.split('_')
            analysis += f"\nUnderscore segments ({len(underscore_segments)} parts):\n"
            for i, segment in enumerate(underscore_segments):
                analysis += f"  {i+1}. '{segment}'\n"
        
        # Number extraction
        import re
        numbers = re.findall(r'\d+', hostname)
        if numbers:
            analysis += f"\nNumber sequences found: {numbers}\n"
        
        # Common prefix/suffix analysis
        common_prefixes = ['web', 'app', 'db', 'sql', 'api', 'svc', 'srv', 'prod', 'dev', 'test', 'stage']
        common_suffixes = ['server', 'srv', 'svc', 'prod', 'dev', 'test', '01', '02', '03']
        
        hostname_lower = hostname.lower()
        found_prefixes = [prefix for prefix in common_prefixes if hostname_lower.startswith(prefix)]
        found_suffixes = [suffix for suffix in common_suffixes if hostname_lower.endswith(suffix)]
        
        if found_prefixes:
            analysis += f"\nCommon prefixes detected: {found_prefixes}\n"
        if found_suffixes:
            analysis += f"Common suffixes detected: {found_suffixes}\n"
        
        # Pattern indicators (factual observations only)
        patterns = []
        if re.search(r'(db|database|sql|mysql|postgres|oracle)', hostname_lower):
            patterns.append("database terminology")
        if re.search(r'(web|www|http|nginx|apache)', hostname_lower):
            patterns.append("web server terminology")
        if re.search(r'(app|application|svc|service|api)', hostname_lower):
            patterns.append("application terminology")
        if re.search(r'(prod|production)', hostname_lower):
            patterns.append("production environment terminology")
        if re.search(r'(dev|development|test|staging|stage)', hostname_lower):
            patterns.append("non-production environment terminology")
        if re.search(r'(lb|load|balance|proxy)', hostname_lower):
            patterns.append("load balancing terminology")
        if re.search(r'(mail|smtp|email)', hostname_lower):
            patterns.append("email service terminology")
        if re.search(r'(file|fs|storage|nas|san)', hostname_lower):
            patterns.append("storage terminology")
        
        if patterns:
            analysis += f"\nTerminology patterns observed: {', '.join(patterns)}\n"
        
        # Structural patterns
        if re.search(r'\d{2,}$', hostname):
            analysis += "\nEnds with multi-digit number (possible sequence/instance identifier)\n"
        if re.search(r'^[a-z]+-[a-z]+-[a-z]+', hostname_lower):
            analysis += "Follows hyphenated naming convention (role-environment-instance pattern)\n"
        if len(hostname.split('.')) > 2:
            analysis += "Multi-level domain structure detected\n"
        
        return analysis
    
    async def arun(self, hostname: str) -> str:
        return self._run(hostname)
```

### EpisodeRetrievalTool

**Purpose**: Help agents find similar past experiences for context and learning.

```python
class EpisodeRetrievalTool(BaseTool):
    name = "episode_retrieval"
    description = """Search for similar past episodes where agents analyzed comparable assets.
    Use this to learn from previous successful analyses and reasoning patterns."""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        super().__init__()
        self.memory_manager = memory_manager
    
    def _run(self, search_context: str, asset_type: str = None, limit: int = 3) -> str:
        """
        Search for similar past episodes.
        
        Args:
            search_context: Description of what you're looking for
            asset_type: Filter by asset type if specified
            limit: Maximum number of episodes to return
        
        Returns:
            Relevant past episodes for context
        """
        try:
            # Prepare search query
            search_query = {
                'task_description': search_context,
                'input_data': {'asset_type': asset_type} if asset_type else {}
            }
            
            episodes = await self.memory_manager.tier2.search_similar_episodes(
                current_task=search_query,
                limit=limit
            )
            
            if not episodes:
                return f"No similar episodes found for context: '{search_context}'"
            
            result = f"Found {len(episodes)} similar episodes:\n\n"
            
            for i, episode in enumerate(episodes, 1):
                result += f"{i}. Episode from {episode.get('completion_time', 'unknown date')}\n"
                result += f"   Agent: {episode.get('agent_type', 'unknown')}\n"
                result += f"   Task: {episode.get('task_description', 'not specified')}\n"
                result += f"   Asset analyzed: {episode.get('input_data', {}).get('asset_name', 'unknown')}\n"
                result += f"   Asset type: {episode.get('input_data', {}).get('asset_type', 'unknown')}\n"
                
                if reasoning := episode.get('reasoning_chain'):
                    result += f"   Reasoning approach: {' -> '.join([step.get('step', '') for step in reasoning[:3]])}\n"
                
                result += f"   Final conclusion: {episode.get('final_conclusion', 'not specified')}\n"
                result += f"   Confidence: {episode.get('confidence_score', 'unknown')}\n"
                
                if feedback := episode.get('user_feedback'):
                    result += f"   User feedback: {feedback.get('accepted', 'unknown')} "
                    if feedback.get('corrections'):
                        result += f"(with corrections: {feedback.get('corrections')})"
                    result += "\n"
                
                if success := episode.get('success_indicators'):
                    result += f"   Success indicators: {success}\n"
                
                result += "\n"
            
            result += "Note: These episodes provide context for your analysis, but each asset should be evaluated independently."
            
            return result
            
        except Exception as e:
            return f"Error retrieving episodes: {str(e)}"
    
    async def arun(self, search_context: str, asset_type: str = None, limit: int = 3) -> str:
        return self._run(search_context, asset_type, limit)
```

### LearningTool

**Purpose**: Allow agents to store their discoveries and reasoning for future use.

```python
class LearningTool(BaseTool):
    name = "learning_tool"
    description = """Store patterns and insights you discover during analysis for future reference.
    Use this when you identify reliable correlations or successful reasoning approaches."""
    
    def __init__(self, memory_manager: UnifiedMemoryManager, agent_name: str):
        super().__init__()
        self.memory_manager = memory_manager
        self.agent_name = agent_name
    
    def _run(self, pattern_type: str, pattern_value: str, insights: dict, reasoning: str, confidence: float) -> str:
        """
        Store a discovered pattern for future reference.
        
        Args:
            pattern_type: Type of pattern (hostname_analysis, port_analysis, etc.)
            pattern_value: The specific pattern (db-*, port_3306, etc.)
            insights: Dictionary of insights associated with this pattern
            reasoning: Your reasoning for why this pattern is significant
            confidence: Your confidence in this pattern (0.0 to 1.0)
        
        Returns:
            Confirmation of pattern storage
        """
        try:
            # Validate inputs
            if confidence < 0.0 or confidence > 1.0:
                return "Error: Confidence must be between 0.0 and 1.0"
            
            if not insights or not isinstance(insights, dict):
                return "Error: Insights must be a non-empty dictionary"
            
            # Create pattern object
            pattern = DiscoveredPattern(
                type=pattern_type,
                value=pattern_value,
                insight=insights,
                reasoning=reasoning,
                source_agent=self.agent_name,
                origin_flow_id=getattr(self, 'current_flow_id', None),
                discovery_method='agent_analysis',
                initial_confidence=confidence
            )
            
            # Store the pattern
            await self.memory_manager.tier3.store_discovered_pattern(pattern)
            
            return f"Pattern stored successfully:\n" \
                   f"Type: {pattern_type}\n" \
                   f"Pattern: {pattern_value}\n" \
                   f"Insights: {json.dumps(insights, indent=2)}\n" \
                   f"Confidence: {confidence}\n" \
                   f"This pattern will be available for future analyses."
            
        except Exception as e:
            return f"Error storing pattern: {str(e)}"
    
    async def arun(self, pattern_type: str, pattern_value: str, insights: dict, reasoning: str, confidence: float) -> str:
        return self._run(pattern_type, pattern_value, insights, reasoning, confidence)
```

## Asset Enrichment Workflow

### Agent-Driven Asset Analysis Process

The core workflow for populating asset enrichment fields through agent reasoning:

```python
class AssetEnrichmentWorkflow:
    """Orchestrates agent-driven asset enrichment"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
        self.enrichment_crew = EnhancedDataCleansingCrew(memory_manager)
    
    async def enrich_asset(self, asset: Asset) -> AssetEnrichmentResult:
        """Complete asset enrichment through agent analysis"""
        
        # Create task memory for this enrichment
        task_memory = await self.memory_manager.create_task_memory(
            task_id=f"enrich_{asset.id}",
            agent_type="AssetEnrichmentSpecialist"
        )
        
        # Prepare enrichment task
        enrichment_task = f"""
        Analyze asset '{asset.name}' to determine enrichment fields:
        
        Required Analysis:
        1. Asset subtype classification
        2. Business value assessment (1-10 scale)
        3. Availability requirements 
        4. Compliance requirements (PCI, HIPAA, SOX, GDPR)
        5. Data classification level
        
        Available Data:
        - Hostname: {asset.hostname}
        - Asset Type: {asset.asset_type}
        - Raw Import Data: {asset.raw_import_data}
        
        Process:
        1. Use HostnameAnalysisTool to analyze naming patterns
        2. Use AssetDataQueryTool to inspect detailed characteristics
        3. Use PatternSearchTool to find relevant historical patterns
        4. Use EpisodeRetrievalTool for similar asset analyses
        5. Apply reasoning to determine each enrichment field
        6. Store any new reliable patterns discovered
        
        For each field, provide:
        - Your conclusion
        - Confidence level (0-100%)
        - Supporting evidence
        - If confidence < 75% for critical fields, ask specific user question
        """
        
        # Execute agent analysis
        result = await self.enrichment_crew.analyze_asset(enrichment_task)
        
        # Parse agent response into structured format
        enrichment_result = self._parse_agent_analysis(result)
        
        # Update asset fields if confidence is sufficient
        if enrichment_result.overall_confidence >= 0.75:
            await self._update_asset_fields(asset, enrichment_result)
        
        # Complete task and store learning
        episode = TaskEpisode(
            id=f"enrich_{asset.id}",
            agent_type="AssetEnrichmentSpecialist", 
            task_description=enrichment_task,
            input_data={
                'asset_id': asset.id,
                'asset_name': asset.name,
                'hostname': asset.hostname,
                'asset_type': asset.asset_type
            },
            reasoning_chain=task_memory.reasoning_chain,
            conclusion=enrichment_result.summary,
            confidence=enrichment_result.overall_confidence,
            success_indicators={'enrichment_applied': True}
        )
        
        await self.memory_manager.complete_task(task_memory.task_id, episode)
        
        return enrichment_result
    
    async def _update_asset_fields(self, asset: Asset, result: AssetEnrichmentResult):
        """Update asset database fields from agent analysis"""
        
        # Update enrichment fields
        if result.asset_subtype and result.subtype_confidence >= 0.75:
            asset.asset_subtype = result.asset_subtype
            
        if result.business_value_score and result.business_value_confidence >= 0.75:
            asset.business_value_score = result.business_value_score
            
        if result.availability_requirement and result.availability_confidence >= 0.75:
            asset.availability_requirement = result.availability_requirement
            
        if result.compliance_requirements and result.compliance_confidence >= 0.75:
            asset.compliance_requirements = result.compliance_requirements
            
        if result.data_classification and result.classification_confidence >= 0.75:
            asset.data_classification = result.data_classification
        
        # Update metadata
        asset.ai_confidence_score = result.overall_confidence
        asset.enriching_agent = "AssetEnrichmentSpecialist"
        asset.enrichment_reasoning = result.reasoning_summary
        asset.last_enrichment_timestamp = datetime.utcnow()
        asset.enrichment_status = 'enhanced' if result.overall_confidence >= 0.85 else 'basic'
        
        # Calculate enrichment score based on populated fields
        asset.enrichment_score = self._calculate_enrichment_score(asset)
        
        # Save to database
        await self._save_asset(asset)
    
    def _calculate_enrichment_score(self, asset: Asset) -> int:
        """Calculate enrichment completeness score"""
        score = 0
        max_score = 100
        
        # Core fields (60 points total)
        if asset.asset_subtype:
            score += 15
        if asset.business_value_score:
            score += 20  # Most important field
        if asset.availability_requirement:
            score += 15
        if asset.data_classification:
            score += 10
        
        # Additional fields (40 points total)
        if asset.compliance_requirements and len(asset.compliance_requirements) > 0:
            score += 15
        if asset.application_version:
            score += 10
        if asset.end_of_support_date:
            score += 10
        if asset.container_ready is not None:
            score += 5
        
        return min(score, max_score)
```

### User Interaction for Low Confidence Fields

When agent confidence is low, structured questions are generated:

```python
class EnrichmentQuestionGenerator:
    """Generates user questions for low-confidence enrichment fields"""
    
    def generate_business_value_question(self, asset: Asset, agent_analysis: dict) -> dict:
        """Generate business value assessment question"""
        
        return {
            'question_id': f"bv_{asset.id}",
            'question_type': 'business_value_assessment',
            'title': 'Application Business Value',
            'question': f"How critical is '{asset.name}' to business operations?",
            'options': [
                "Low (1-3) - Internal tools, development systems",
                "Medium (4-6) - Supporting business operations", 
                "High (7-8) - Important business functions",
                "Critical (9-10) - Revenue generating, customer-facing"
            ],
            'context': {
                'asset_name': asset.name,
                'hostname': asset.hostname,
                'agent_reasoning': agent_analysis.get('business_value_reasoning', ''),
                'agent_suggestion': agent_analysis.get('business_value_suggestion', ''),
                'confidence': agent_analysis.get('business_value_confidence', 0)
            },
            'metadata': {
                'estimated_time_seconds': 20,
                'skip_allowed': False,  # Critical field
                'field_being_enriched': 'business_value_score'
            }
        }
    
    def generate_compliance_question(self, asset: Asset, agent_analysis: dict) -> dict:
        """Generate compliance requirements question"""
        
        return {
            'question_id': f"comp_{asset.id}",
            'question_type': 'compliance_assessment',
            'title': 'Compliance Requirements',
            'question': f"What compliance requirements apply to '{asset.name}'?",
            'options': [
                "PCI-DSS (Payment card data)",
                "HIPAA (Health information)", 
                "SOX (Financial reporting)",
                "GDPR (EU personal data)",
                "None/Internal use only",
                "Multiple (please specify in follow-up)"
            ],
            'context': {
                'asset_name': asset.name,
                'detected_patterns': agent_analysis.get('compliance_indicators', []),
                'agent_reasoning': agent_analysis.get('compliance_reasoning', ''),
                'confidence': agent_analysis.get('compliance_confidence', 0)
            },
            'metadata': {
                'estimated_time_seconds': 15,
                'skip_allowed': True,  # Can be determined later
                'field_being_enriched': 'compliance_requirements',
                'allow_multiple_selection': True
            }
        }
```

## Agent Reasoning Framework

### Enhanced Agent Task Descriptions

Instead of procedural instructions, agents receive reasoning-focused task descriptions:

```python
ASSET_ANALYSIS_TASK = """
You are an expert asset analyst tasked with determining the type, subtype, and business context of IT assets.

Your goal is to analyze the given asset and provide:
1. Asset type classification (server, application, database, network_device, etc.)
2. Asset subtype (if applicable)
3. Business context insights (criticality, usage patterns, etc.)
4. Confidence level in your analysis (0-100%)

Available tools:
- PatternSearchTool: Query previously discovered patterns for evidence
- AssetDataQueryTool: Inspect specific aspects of the asset data
- HostnameAnalysisTool: Analyze hostname structure and components
- EpisodeRetrievalTool: Find similar past analyses for context
- LearningTool: Store new patterns you discover

Reasoning process:
1. **Initial Assessment**: Review the basic asset information provided
2. **Hypothesis Formation**: Based on initial data, form preliminary hypotheses about asset type/purpose
3. **Evidence Gathering**: Use tools to gather supporting evidence for your hypotheses
4. **Pattern Analysis**: Check for previously discovered patterns that might apply
5. **Contextual Learning**: Look for similar past episodes to inform your analysis
6. **Synthesis**: Combine all evidence to reach your conclusion
7. **Confidence Assessment**: Evaluate the strength of your evidence and assign confidence
8. **Learning Storage**: If you discover reliable new patterns, store them for future use

If your confidence is below 85%, generate a specific, clear question for the user that will help resolve the ambiguity.

Remember:
- Tools provide FACTS and EVIDENCE, you provide REASONING and INTELLIGENCE
- Consider multiple hypotheses before settling on a conclusion
- Explain your reasoning process clearly
- Be honest about uncertainty - it's better to ask than to guess
- Learn from each analysis to improve future performance
"""
```

### Agent Reasoning Patterns

```python
class AgentReasoningTracker:
    """Tracks and guides agent reasoning processes"""
    
    def __init__(self, task_memory: AgenticShortTermMemory):
        self.memory = task_memory
        self.reasoning_steps = [
            'initial_assessment',
            'hypothesis_formation', 
            'evidence_gathering',
            'pattern_analysis',
            'contextual_learning',
            'synthesis',
            'confidence_assessment',
            'learning_storage'
        ]
        self.current_step = 0
    
    def guide_next_step(self) -> str:
        """Provide guidance for the next reasoning step"""
        if self.current_step >= len(self.reasoning_steps):
            return "Analysis complete. Review your findings and provide final conclusion."
        
        step = self.reasoning_steps[self.current_step]
        guidance = {
            'initial_assessment': "Review the basic asset data. What do you know for certain?",
            'hypothesis_formation': "Based on initial data, what are 2-3 possible asset types/purposes?",
            'evidence_gathering': "Use AssetDataQueryTool and HostnameAnalysisTool to gather specific evidence.",
            'pattern_analysis': "Use PatternSearchTool to check for relevant historical patterns.",
            'contextual_learning': "Use EpisodeRetrievalTool to find similar past analyses.",
            'synthesis': "Combine all evidence. Which hypothesis has the strongest support?",
            'confidence_assessment': "How confident are you? What evidence supports/contradicts your conclusion?",
            'learning_storage': "Did you discover any new reliable patterns? Use LearningTool to store them."
        }
        
        self.current_step += 1
        return f"Step {self.current_step}: {guidance[step]}"
    
    def record_reasoning_step(self, step_description: str, evidence: dict, confidence_change: float = 0):
        """Record a reasoning step in memory"""
        self.memory.add_reasoning_step(step_description, evidence)
        if confidence_change:
            # Update confidence based on new evidence
            pass
```

## Tool Integration with CrewAI

### Tool Registration

```python
class AgentToolRegistry:
    """Manages tool availability for different agent types"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
        self.tools = {}
    
    def register_tools_for_agent(self, agent_type: str) -> list:
        """Register appropriate tools for agent type"""
        
        base_tools = [
            PatternSearchTool(self.memory_manager),
            AssetDataQueryTool(self.memory_manager.db),
            HostnameAnalysisTool(),
            EpisodeRetrievalTool(self.memory_manager),
            LearningTool(self.memory_manager, agent_type)
        ]
        
        # Agent-specific tools
        if agent_type == 'DataCleansingCrew':
            base_tools.extend([
                DataQualityAnalysisTool(),
                FieldMappingTool()
            ])
        elif agent_type == 'InventoryBuildingCrew':
            base_tools.extend([
                BusinessContextTool(),
                ApplicationDiscoveryTool()
            ])
        elif agent_type == 'DependencyAnalysisCrew':
            base_tools.extend([
                NetworkAnalysisTool(),
                ComplianceCheckTool()
            ])
        
        self.tools[agent_type] = base_tools
        return base_tools
```

### Enhanced Crew Configuration

```python
class EnhancedDataCleansingCrew(Crew):
    """Enhanced data cleansing crew with agentic tools"""
    
    def __init__(self, memory_manager: UnifiedMemoryManager):
        self.memory_manager = memory_manager
        self.tool_registry = AgentToolRegistry(memory_manager)
        
        # Get tools for this agent type
        agent_tools = self.tool_registry.register_tools_for_agent('DataCleansingCrew')
        
        agents = [
            Agent(
                role="Asset Classification Specialist",
                goal="Accurately classify assets based on analysis of available data",
                backstory="""You are an expert in IT infrastructure analysis with years of experience 
                classifying diverse IT assets. You use systematic reasoning and evidence-based analysis 
                to determine asset types and characteristics.""",
                tools=agent_tools,
                verbose=True,
                allow_delegation=False,
                memory=True  # Re-enabled with fixed memory system
            )
        ]
        
        tasks = [
            Task(
                description=ASSET_ANALYSIS_TASK,
                agent=agents[0],
                expected_output="""
                Provide a structured analysis including:
                1. Asset classification with confidence score
                2. Supporting evidence for your conclusion  
                3. Any new patterns discovered
                4. Questions for user if confidence < 85%
                """
            )
        ]
        
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=True,
            memory=True,  # Re-enabled
            planning=True
        )
```

---

This agent tools and reasoning framework transforms the platform from a rule-based system to a truly intelligent, learning-based agentic platform where AI agents use tools to investigate, reason, and learn from experience.