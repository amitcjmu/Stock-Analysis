"""
Optimized Field Mapping Crew
Implements the enhanced memory and performance optimizations:
- Uses enhanced agent memory for pattern recognition
- Leverages previous mapping experiences
- Implements intelligent caching
- Provides fast execution with learning capabilities
"""

import logging
import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process

from .optimized_crew_base import OptimizedCrewBase
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.performance.response_optimizer import optimize_response

logger = logging.getLogger(__name__)


class OptimizedFieldMappingCrew(OptimizedCrewBase):
    """Optimized Field Mapping Crew with enhanced memory and learning"""
    
    def __init__(self, crewai_service, context: Optional[LearningContext] = None):
        super().__init__(
            crewai_service,
            context=context,
            enable_memory=True,
            enable_caching=True,
            enable_parallel=False  # Sequential for field mapping accuracy
        )
        
        # Field mapping specific settings
        self.standard_fields = [
            "asset_name", "asset_type", "asset_id", "environment",
            "business_criticality", "operating_system", "ip_address",
            "owner", "location", "status", "description", "notes"
        ]
        
        logger.info("🚀 Optimized Field Mapping Crew initialized with enhanced memory")
    
    async def create_memory_enhanced_agents(self) -> List[Agent]:
        """Create agents with memory-enhanced capabilities"""
        
        # Load previous field mapping experiences
        past_mappings = await enhanced_agent_memory.retrieve_memories(
            {"type": "field_mapping", "success": True},
            context=self.context,
            limit=10,
            memory_types=["field_mapping", "user_feedback"]
        )
        
        mapping_experience = ""
        if past_mappings:
            experiences = []
            for memory in past_mappings:
                content = memory.content
                if "source_field" in content and "target_field" in content:
                    experiences.append(f"- {content['source_field']} → {content['target_field']} (confidence: {memory.confidence_score:.2f})")
            
            if experiences:
                mapping_experience = f"""
                
LEARNED MAPPING PATTERNS (from {len(experiences)} past experiences):
{chr(10).join(experiences[:5])}  # Show top 5
                """
        
        # Primary Field Mapping Agent with memory enhancement
        field_mapper = self.create_optimized_agent(
            role="Enhanced CMDB Field Mapping Specialist",
            goal="Map source data fields to standard CMDB attributes using learned patterns and memory",
            backstory=f"""You are an expert field mapping specialist with access to organizational memory and learned patterns.
            
YOUR ENHANCED CAPABILITIES:
- Access to previous successful mapping patterns
- Learning from user feedback and corrections
- Pattern recognition across similar data sources
- Confidence scoring based on historical accuracy

STANDARD TARGET FIELDS:
{', '.join(self.standard_fields)}

MAPPING APPROACH:
1. First check if similar fields were mapped before (use memory)
2. Apply learned patterns from past successful mappings
3. Use semantic similarity for new field types
4. Assign confidence scores based on match quality and historical accuracy

CONFIDENCE SCORING RULES:
- 0.95+: Exact match with high historical success
- 0.90+: Semantic match with confirmed past success
- 0.80+: Strong pattern match with good history
- 0.70+: Semantic similarity with some history
- 0.60+: Possible match with limited history
- 0.50+: Weak similarity or new pattern
- <0.50: No clear match or unreliable pattern

{mapping_experience}

WORK EFFICIENTLY:
- Leverage memory patterns first
- Make decisions based on learned experience
- Complete mapping in under 45 seconds
- Focus on accuracy through learning, not speed alone
""",
            max_execution_time=60,
            allow_delegation=False,
            tools=[]
        )
        
        return [field_mapper]
    
    async def create_memory_enhanced_tasks(self, agents: List[Agent], raw_data: List[Dict[str, Any]]) -> List[Task]:
        """Create tasks that leverage memory and learning"""
        field_mapper = agents[0]
        
        headers = list(raw_data[0].keys()) if raw_data else []
        data_sample = raw_data[:3] if raw_data else []
        
        # Check for similar data structures in memory
        similar_structures = await enhanced_agent_memory.retrieve_memories(
            {
                "type": "data_structure",
                "field_count": len(headers),
                "sample_fields": headers[:5]
            },
            context=self.context,
            limit=3
        )
        
        context_info = ""
        if similar_structures:
            context_info = f"""
            
SIMILAR DATA STRUCTURES FOUND IN MEMORY:
{json.dumps([s.content for s in similar_structures], indent=2)}
            """
        
        # Enhanced mapping task with memory context
        mapping_task = self.create_optimized_task(
            description=f"""
ENHANCED FIELD MAPPING TASK WITH MEMORY:

Source Headers: {headers}
Sample Data: {json.dumps(data_sample, indent=2)}
{context_info}

YOUR ENHANCED TASK:
1. Analyze source fields against learned patterns
2. Apply memory-based mapping suggestions
3. Use historical confidence scores to guide decisions
4. Create optimized field mappings

MAPPING PROCESS:
1. For each source field, check memory for similar patterns
2. Apply learned mapping rules from past successes
3. Use semantic analysis for new or unclear fields
4. Assign confidence scores based on pattern strength and history
5. Flag uncertain mappings for potential user review

EXPECTED OUTPUT FORMAT:
```json
{{
    "mappings": {{
        "source_field_1": {{
            "target_field": "standard_field_name",
            "confidence": 0.85,
            "reasoning": "Exact match found in memory with 95% success rate",
            "memory_pattern_id": "pattern_id_if_used"
        }}
    }},
    "unmapped_fields": ["field1", "field2"],
    "mapping_summary": {{
        "total_fields": {len(headers)},
        "mapped_fields": 0,
        "avg_confidence": 0.0,
        "memory_patterns_used": 0,
        "new_patterns_identified": 0
    }},
    "learning_opportunities": {{
        "low_confidence_mappings": [],
        "new_field_patterns": [],
        "validation_needed": []
    }}
}}
```

QUALITY REQUIREMENTS:
- Each mapping must have clear reasoning
- Confidence scores must reflect actual certainty
- Flag mappings that need validation
- Identify new patterns for future learning
""",
            agent=field_mapper,
            expected_output="JSON field mapping result with memory-enhanced confidence scoring and learning identification",
            max_execution_time=60,
            human_input=False
        )
        
        return [mapping_task]
    
    @optimize_response("field_mapping_execution")
    async def execute_enhanced_mapping(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute field mapping with enhanced memory and learning"""
        try:
            # Create memory-enhanced agents and tasks
            agents = await self.create_memory_enhanced_agents()
            tasks = await self.create_memory_enhanced_tasks(agents, raw_data)
            
            # Create optimized crew
            crew = self.create_optimized_crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential
            )
            
            # Execute with performance monitoring
            result = await crew.kickoff()
            
            # Process and learn from result
            processed_result = await self._process_mapping_result(result, raw_data)
            
            # Store execution in memory for future reference
            await self._store_execution_memory(raw_data, processed_result)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Enhanced field mapping execution failed: {e}")
            return {
                "error": str(e),
                "success": False,
                "mappings": {},
                "execution_type": "enhanced_memory"
            }
    
    async def _process_mapping_result(self, raw_result: Any, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and validate mapping result"""
        try:
            # Parse result if it's a string
            if isinstance(raw_result, str):
                try:
                    parsed_result = json.loads(raw_result)
                except json.JSONDecodeError:
                    # Extract JSON from text response
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_result, re.DOTALL)
                    if json_match:
                        parsed_result = json.loads(json_match.group(1))
                    else:
                        raise ValueError("Could not parse JSON from result")
            else:
                parsed_result = raw_result
            
            # Validate and enhance result structure
            processed_result = {
                "success": True,
                "mappings": parsed_result.get("mappings", {}),
                "unmapped_fields": parsed_result.get("unmapped_fields", []),
                "mapping_summary": parsed_result.get("mapping_summary", {}),
                "learning_opportunities": parsed_result.get("learning_opportunities", {}),
                "execution_type": "enhanced_memory",
                "memory_patterns_used": parsed_result.get("mapping_summary", {}).get("memory_patterns_used", 0),
                "confidence_distribution": self._calculate_confidence_distribution(parsed_result.get("mappings", {})),
                "learning_integration": True
            }
            
            # Learn from successful mappings
            await self._learn_from_mappings(processed_result["mappings"], raw_data)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Failed to process mapping result: {e}")
            return {
                "error": f"Result processing failed: {str(e)}",
                "success": False,
                "mappings": {},
                "raw_result": str(raw_result)[:500],
                "execution_type": "enhanced_memory"
            }
    
    def _calculate_confidence_distribution(self, mappings: Dict[str, Any]) -> Dict[str, int]:
        """Calculate distribution of confidence scores"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for mapping_info in mappings.values():
            confidence = mapping_info.get("confidence", 0.0)
            if confidence >= 0.8:
                distribution["high"] += 1
            elif confidence >= 0.6:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution
    
    async def _learn_from_mappings(self, mappings: Dict[str, Any], raw_data: List[Dict[str, Any]]):
        """Learn from successful mappings for future use"""
        try:
            for source_field, mapping_info in mappings.items():
                target_field = mapping_info.get("target_field")
                confidence = mapping_info.get("confidence", 0.0)
                
                # Store field mapping pattern in memory
                await enhanced_agent_memory.store_memory(
                    {
                        "type": "field_mapping",
                        "source_field": source_field,
                        "target_field": target_field,
                        "confidence": confidence,
                        "reasoning": mapping_info.get("reasoning", ""),
                        "success": True,
                        "data_context": {
                            "total_fields": len(raw_data[0].keys()) if raw_data else 0,
                            "sample_values": raw_data[0].get(source_field) if raw_data and source_field in raw_data[0] else None
                        }
                    },
                    memory_type="field_mapping",
                    context=self.context,
                    metadata={
                        "confidence_score": confidence,
                        "mapping_type": "automatic",
                        "validation_status": "pending"
                    }
                )
                
                # Also store in the existing learning system
                await agent_learning_system.learn_field_mapping_pattern(
                    {
                        "original_field": source_field,
                        "mapped_field": target_field,
                        "confidence": confidence,
                        "field_type": mapping_info.get("field_type", "unknown"),
                        "validation_result": True
                    },
                    context=self.context
                )
            
            logger.info(f"Learned from {len(mappings)} field mappings")
            
        except Exception as e:
            logger.error(f"Failed to learn from mappings: {e}")
    
    async def _store_execution_memory(self, raw_data: List[Dict[str, Any]], result: Dict[str, Any]):
        """Store execution details in memory for future optimization"""
        try:
            execution_memory = {
                "type": "execution_result",
                "crew_type": "optimized_field_mapping",
                "data_characteristics": {
                    "field_count": len(raw_data[0].keys()) if raw_data else 0,
                    "record_count": len(raw_data),
                    "field_names": list(raw_data[0].keys()) if raw_data else []
                },
                "performance": {
                    "success": result.get("success", False),
                    "mapped_fields": len(result.get("mappings", {})),
                    "avg_confidence": self._calculate_avg_confidence(result.get("mappings", {})),
                    "memory_patterns_used": result.get("memory_patterns_used", 0)
                },
                "execution_timestamp": datetime.utcnow().isoformat()
            }
            
            await enhanced_agent_memory.store_memory(
                execution_memory,
                memory_type="execution_result",
                context=self.context,
                metadata={
                    "execution_type": "field_mapping",
                    "optimization_level": "enhanced"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store execution memory: {e}")
    
    def _calculate_avg_confidence(self, mappings: Dict[str, Any]) -> float:
        """Calculate average confidence across all mappings"""
        if not mappings:
            return 0.0
        
        confidences = [mapping.get("confidence", 0.0) for mapping in mappings.values()]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    async def get_mapping_intelligence_report(self) -> Dict[str, Any]:
        """Get intelligence report on mapping patterns and performance"""
        try:
            # Get memory statistics
            memory_stats = enhanced_agent_memory.get_memory_statistics()
            
            # Get field mapping specific memories
            mapping_memories = await enhanced_agent_memory.retrieve_memories(
                {"type": "field_mapping"},
                context=self.context,
                limit=100
            )
            
            # Analyze patterns
            field_patterns = defaultdict(list)
            confidence_trends = []
            
            for memory in mapping_memories:
                content = memory.content
                source_field = content.get("source_field", "")
                target_field = content.get("target_field", "")
                confidence = memory.confidence_score
                
                field_patterns[target_field].append({
                    "source": source_field,
                    "confidence": confidence
                })
                confidence_trends.append(confidence)
            
            # Calculate intelligence metrics
            report = {
                "memory_overview": memory_stats,
                "mapping_patterns": {
                    "total_patterns": len(mapping_memories),
                    "unique_targets": len(field_patterns),
                    "avg_confidence": sum(confidence_trends) / len(confidence_trends) if confidence_trends else 0.0,
                    "pattern_distribution": dict(field_patterns)
                },
                "performance_metrics": self.get_performance_report(),
                "recommendations": await self._generate_intelligence_recommendations(field_patterns, confidence_trends)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate intelligence report: {e}")
            return {"error": str(e)}
    
    async def _generate_intelligence_recommendations(
        self, 
        field_patterns: Dict[str, List[Dict]], 
        confidence_trends: List[float]
    ) -> List[str]:
        """Generate intelligent recommendations for mapping improvement"""
        recommendations = []
        
        try:
            # Analyze confidence trends
            if confidence_trends:
                avg_confidence = sum(confidence_trends) / len(confidence_trends)
                if avg_confidence < 0.7:
                    recommendations.append(
                        "Consider gathering more training data - average confidence is below optimal threshold"
                    )
            
            # Analyze pattern consistency
            inconsistent_patterns = []
            for target, patterns in field_patterns.items():
                if len(patterns) > 1:
                    confidences = [p["confidence"] for p in patterns]
                    confidence_variance = max(confidences) - min(confidences)
                    if confidence_variance > 0.3:
                        inconsistent_patterns.append(target)
            
            if inconsistent_patterns:
                recommendations.append(
                    f"Review mapping consistency for: {', '.join(inconsistent_patterns[:3])}"
                )
            
            # Performance recommendations
            perf_stats = self.performance_metrics
            if perf_stats.get("avg_task_duration", 0) > 45:
                recommendations.append(
                    "Consider enabling more aggressive caching to improve response times"
                )
            
            if perf_stats.get("memory_hits", 0) < 5:
                recommendations.append(
                    "Memory system is underutilized - consider pre-loading more patterns"
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]


# Import required for collections
from collections import defaultdict
from datetime import datetime