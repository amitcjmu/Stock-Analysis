"""
Risk Assessment Agent - Agentic Intelligence Implementation

This agent analyzes assets to identify security, operational, and compliance risks using:
1. Real CrewAI agent reasoning instead of rule-based risk matrices
2. Pattern learning from security incidents and vulnerability discoveries
3. Evidence-based risk scoring with detailed threat analysis
4. Integration with three-tier memory system for continuous risk intelligence

The agent uses agentic memory tools to:
- Search for existing risk patterns and threat indicators
- Record new risk patterns discovered during analysis
- Learn from security incidents and compliance violations
- Build institutional knowledge about risk factors across the environment
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# CrewAI imports
from crewai import Agent, Task, Crew, Process

# Internal imports
from app.services.agentic_intelligence.agent_reasoning_patterns import (
    AgentReasoningEngine, 
    ReasoningDimension,
    AssetReasoningPatterns
)
from app.services.agentic_memory import ThreeTierMemoryManager
from app.services.agentic_memory.agent_tools_functional import create_functional_agent_tools

logger = logging.getLogger(__name__)


class RiskAssessmentAgent:
    """
    Agentic Risk Assessment Specialist that learns and applies risk patterns.
    
    This agent specializes in:
    - Security risk assessment based on technology stack and configuration
    - Operational risk analysis considering dependencies and complexity
    - Compliance risk evaluation for regulatory requirements
    - Pattern discovery for emerging threats and vulnerabilities
    - Learning from incident history and security best practices
    """
    
    def __init__(self, crewai_service, client_account_id: uuid.UUID, engagement_id: uuid.UUID, flow_id: Optional[uuid.UUID] = None):
        self.crewai_service = crewai_service
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id
        
        # Initialize agentic memory system
        self.memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
        
        # Initialize reasoning engine
        self.reasoning_engine = AgentReasoningEngine(
            self.memory_manager, 
            client_account_id, 
            engagement_id
        )
        
        # Get configured LLM
        try:
            from app.services.llm_config import get_crewai_llm
            self.llm = get_crewai_llm()
            logger.info("✅ Risk Assessment Agent using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM: {e}")
            self.llm = getattr(crewai_service, 'llm', None)
        
        # Create agent tools for memory access
        self.agent_tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name="Risk Assessment Agent",
            flow_id=flow_id
        )
        
        logger.info(f"✅ Risk Assessment Agent initialized with {len(self.agent_tools)} memory tools")
    
    def create_risk_assessment_agent(self) -> Agent:
        """Create the CrewAI agent specialized in risk assessment with memory tools"""
        
        agent = Agent(
            role="Security and Risk Intelligence Analyst",
            goal="Assess security, operational, and compliance risks using evidence-based analysis and learned threat patterns",
            backstory="""You are a cybersecurity and risk assessment expert who specializes in 
            evaluating IT asset risks through intelligent analysis rather than static checklists.
            
            Your expertise includes:
            - Security vulnerability assessment based on technology stacks and configurations
            - Operational risk analysis considering system dependencies and complexity
            - Compliance risk evaluation for regulatory frameworks (SOX, GDPR, HIPAA, etc.)
            - Threat intelligence and pattern recognition from past incidents
            - Risk scoring based on environmental context and business impact
            
            Your analytical approach:
            1. Search your memory for relevant risk patterns from previous assessments
            2. Analyze technology stacks for known vulnerabilities and security concerns
            3. Evaluate operational risks based on system architecture and dependencies
            4. Assess compliance risks based on data types and regulatory requirements
            5. Apply learned patterns and discover new risk indicators
            6. Record new risk patterns for future intelligence
            7. Provide risk scores with detailed threat analysis and mitigation recommendations
            
            You have access to memory tools that allow you to:
            - Search for risk patterns and threat indicators from previous analyses
            - Query asset data to identify similar systems with known risks
            - Record new risk patterns and threat signatures you discover
            - Enrich assets with comprehensive risk assessments
            
            Always provide specific, actionable risk assessments with clear mitigation strategies.
            Focus on real threats and practical security concerns rather than theoretical risks.""",
            
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=self.agent_tools,
            memory=True,  # Use agent memory for threat intelligence
            max_iter=3,
            max_execution_time=60
        )
        
        return agent
    
    def create_risk_assessment_task(self, asset_data: Dict[str, Any]) -> Task:
        """Create a task for comprehensive risk assessment of an asset"""
        
        asset_summary = {
            "name": asset_data.get("name"),
            "asset_type": asset_data.get("asset_type"),
            "technology_stack": asset_data.get("technology_stack"),
            "environment": asset_data.get("environment"),
            "business_criticality": asset_data.get("business_criticality"),
            "network_exposure": asset_data.get("network_exposure"),
            "data_sensitivity": asset_data.get("data_sensitivity")
        }
        
        task = Task(
            description=f"""
            Conduct a comprehensive risk assessment for this asset using your security intelligence and memory tools:
            
            Asset Details:
            {json.dumps(asset_summary, indent=2)}
            
            Complete Risk Assessment Process:
            
            1. SEARCH FOR THREAT PATTERNS:
               Use your pattern search tool to find relevant risk patterns and threat indicators from previous assessments.
               Search for: security vulnerabilities, legacy technology risks, compliance violations, operational failures.
               
            2. TECHNOLOGY STACK ANALYSIS:
               Use your asset query tool to examine similar technology stacks and identify:
               - Known security vulnerabilities in the technology stack
               - End-of-life or unsupported software versions
               - Configuration weaknesses and security gaps
               - Compare with other systems to identify risk patterns
               
            3. SECURITY RISK ASSESSMENT:
               Evaluate security risks including:
               - Vulnerability exposure based on technology versions
               - Network security risks and exposure levels
               - Authentication and access control weaknesses
               - Data protection and encryption gaps
               - Supply chain and third-party risks
               
            4. OPERATIONAL RISK ANALYSIS:
               Assess operational risks such as:
               - Single points of failure and availability risks
               - Backup and recovery capabilities
               - Monitoring and incident response readiness
               - Change management and update processes
               - Dependency risks and cascade failure potential
               
            5. COMPLIANCE RISK EVALUATION:
               Determine compliance risks for:
               - Data privacy regulations (GDPR, CCPA, HIPAA)
               - Financial regulations (SOX, PCI-DSS)
               - Industry-specific compliance requirements
               - Audit trail and documentation requirements
               
            6. RISK SCORING:
               Provide an overall risk assessment:
               - Low Risk: Well-secured, current technology, good operational practices
               - Medium Risk: Some vulnerabilities or operational concerns, manageable with controls
               - High Risk: Significant security gaps, legacy technology, or compliance violations
               - Critical Risk: Immediate threats, end-of-life systems, or severe compliance failures
               
            7. PATTERN DISCOVERY:
               If you identify new risk patterns or threat indicators, use your pattern recording tool
               to save them for future threat intelligence.
               
            8. ASSET ENRICHMENT:
               Use your asset enrichment tool to update the asset with:
               - Overall risk assessment level
               - Specific risk categories and scores
               - Detailed threat analysis and reasoning
               - Mitigation recommendations and priority actions
               
            Provide your risk assessment in this format:
            Overall Risk Level: [Low/Medium/High/Critical]
            Security Risk Score: [1-10]
            Operational Risk Score: [1-10]
            Compliance Risk Score: [1-10]
            Confidence Level: [High/Medium/Low]
            Primary Threats: [Key security and operational threats identified]
            Vulnerability Summary: [Critical vulnerabilities and weaknesses]
            Compliance Concerns: [Regulatory and compliance risk factors]
            Risk Patterns Applied: [Patterns used from memory]
            New Patterns Discovered: [New risk patterns identified]
            Immediate Actions: [High-priority mitigation steps]
            Long-term Recommendations: [Strategic risk reduction measures]
            """,
            
            expected_output="""
            Comprehensive Risk Assessment Report with:
            - Overall risk level classification (Low/Medium/High/Critical)
            - Detailed risk scores for security, operational, and compliance domains
            - Specific threat analysis with vulnerability details
            - Evidence-based reasoning for risk assessments
            - New risk patterns discovered and recorded
            - Asset enrichment confirmation with risk metadata
            - Prioritized mitigation recommendations and action plans
            """,
            
            agent=self.create_risk_assessment_agent(),  # Fix: Assign agent to task
            max_execution_time=50
        )
        
        return task
    
    def create_risk_assessment_crew(self, asset_data: Dict[str, Any]) -> Crew:
        """Create a crew for comprehensive risk assessment"""
        
        agent = self.create_risk_assessment_agent()
        task = self.create_risk_assessment_task(asset_data)
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=True,  # Enable crew-level memory for threat intelligence
            max_execution_time=90
        )
        
        return crew
    
    async def analyze_asset_risk(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to analyze risk of an asset using agentic intelligence.
        
        This method:
        1. Creates a specialized risk assessment crew with threat intelligence tools
        2. Executes comprehensive security, operational, and compliance risk analysis
        3. Returns structured results with risk levels, threat analysis, and mitigation plans
        """
        try:
            logger.info(f"🛡️ Starting agentic risk assessment for asset: {asset_data.get('name')}")
            
            # Create and execute the risk assessment crew
            crew = self.create_risk_assessment_crew(asset_data)
            
            # Execute the crew (this will run the agent with all memory tools)
            result = crew.kickoff()
            
            # Parse the agent's output
            parsed_result = self._parse_risk_assessment_output(result, asset_data)
            
            logger.info(f"✅ Risk assessment completed - Level: {parsed_result.get('risk_assessment')}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {e}")
            
            # Fallback to reasoning engine if crew fails
            try:
                logger.info("🔄 Falling back to reasoning engine analysis")
                reasoning_result = await self.reasoning_engine.analyze_asset_risk_assessment(
                    asset_data, "Risk Assessment Agent"
                )
                return self._convert_reasoning_to_dict(reasoning_result)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback risk analysis also failed: {fallback_error}")
                return self._create_default_risk_assessment(asset_data)
    
    def _parse_risk_assessment_output(self, agent_output: str, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the agent's risk assessment output into structured data"""
        try:
            result = {
                "agent_analysis_type": "risk_assessment",
                "asset_id": asset_data.get("id"),
                "asset_name": asset_data.get("name"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Risk Assessment Agent"
            }
            
            output_lower = str(agent_output).lower()
            
            # Extract overall risk level
            if 'critical risk' in output_lower or 'overall risk level: critical' in output_lower:
                result["risk_assessment"] = "critical"
            elif 'high risk' in output_lower or 'overall risk level: high' in output_lower:
                result["risk_assessment"] = "high"
            elif 'medium risk' in output_lower or 'overall risk level: medium' in output_lower:
                result["risk_assessment"] = "medium"
            else:
                result["risk_assessment"] = "low"
            
            # Extract specific risk scores
            import re
            
            security_score_match = re.search(r'security risk score:?\s*(\d+)', output_lower)
            result["security_risk_score"] = int(security_score_match.group(1)) if security_score_match else self._risk_level_to_score(result["risk_assessment"])
            
            operational_score_match = re.search(r'operational risk score:?\s*(\d+)', output_lower)
            result["operational_risk_score"] = int(operational_score_match.group(1)) if operational_score_match else self._risk_level_to_score(result["risk_assessment"])
            
            compliance_score_match = re.search(r'compliance risk score:?\s*(\d+)', output_lower)
            result["compliance_risk_score"] = int(compliance_score_match.group(1)) if compliance_score_match else self._risk_level_to_score(result["risk_assessment"])
            
            # Extract confidence level
            if 'high' in output_lower and 'confidence' in output_lower:
                result["confidence_level"] = "high"
            elif 'medium' in output_lower and 'confidence' in output_lower:
                result["confidence_level"] = "medium"
            else:
                result["confidence_level"] = "medium"
            
            # Extract threat analysis
            threats_match = re.search(r'primary threats:(.+?)(?:vulnerability summary|$)', output_lower, re.DOTALL)
            if threats_match:
                result["primary_threats"] = threats_match.group(1).strip()
            else:
                result["primary_threats"] = "Standard security and operational risks assessed"
            
            # Extract vulnerability summary
            vuln_match = re.search(r'vulnerability summary:(.+?)(?:compliance concerns|$)', output_lower, re.DOTALL)
            if vuln_match:
                result["vulnerability_summary"] = vuln_match.group(1).strip()
            else:
                result["vulnerability_summary"] = "Technology stack and configuration assessed for vulnerabilities"
            
            # Extract immediate actions
            actions_match = re.search(r'immediate actions:(.+?)(?:long-term recommendations|$)', output_lower, re.DOTALL)
            if actions_match:
                actions_text = actions_match.group(1).strip()
                result["immediate_actions"] = [action.strip() for action in actions_text.split('-') if action.strip()]
            else:
                result["immediate_actions"] = ["Review security configuration", "Update to supported versions"]
            
            # Extract long-term recommendations
            longterm_match = re.search(r'long-term recommendations:(.+?)$', output_lower, re.DOTALL)
            if longterm_match:
                longterm_text = longterm_match.group(1).strip()
                result["longterm_recommendations"] = [rec.strip() for rec in longterm_text.split('-') if rec.strip()]
            else:
                result["longterm_recommendations"] = ["Implement comprehensive security monitoring", "Plan modernization to reduce risk"]
            
            # Set enrichment status
            result["enrichment_status"] = "agent_analyzed"
            result["analysis_method"] = "agentic_intelligence"
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse risk assessment output: {e}")
            return self._create_default_risk_assessment(asset_data)
    
    def _convert_reasoning_to_dict(self, reasoning: 'AgentReasoning') -> Dict[str, Any]:
        """Convert AgentReasoning object to dictionary format for risk assessment"""
        
        # Convert score to risk level
        risk_level = "low"
        if reasoning.score >= 8:
            risk_level = "critical"
        elif reasoning.score >= 6:
            risk_level = "high"
        elif reasoning.score >= 4:
            risk_level = "medium"
        
        return {
            "agent_analysis_type": "risk_assessment",
            "risk_assessment": risk_level,
            "security_risk_score": reasoning.score,
            "operational_risk_score": reasoning.score,
            "compliance_risk_score": reasoning.score,
            "confidence_level": "high" if reasoning.confidence >= 0.7 else "medium" if reasoning.confidence >= 0.4 else "low",
            "primary_threats": reasoning.reasoning_summary,
            "vulnerability_summary": f"Analysis identified {len(reasoning.evidence_pieces)} risk factors",
            "evidence_count": len(reasoning.evidence_pieces),
            "patterns_applied": len(reasoning.applied_patterns),
            "patterns_discovered": len(reasoning.discovered_patterns),
            "immediate_actions": reasoning.recommendations[:3],  # First 3 as immediate
            "longterm_recommendations": reasoning.recommendations[3:],  # Rest as long-term
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "agent_analyzed",
            "analysis_method": "reasoning_engine"
        }
    
    def _create_default_risk_assessment(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default risk assessment when both agent and reasoning engine fail"""
        return {
            "agent_analysis_type": "risk_assessment",
            "risk_assessment": "medium",  # Default medium risk
            "security_risk_score": 5,
            "operational_risk_score": 5,
            "compliance_risk_score": 5,
            "confidence_level": "low",
            "primary_threats": "Standard security and operational risks",
            "vulnerability_summary": "Basic risk assessment - detailed analysis unavailable",
            "immediate_actions": ["Review security configuration", "Verify software versions"],
            "longterm_recommendations": ["Plan security assessment", "Consider modernization"],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "enrichment_status": "basic",
            "analysis_method": "fallback"
        }
    
    def _risk_level_to_score(self, risk_level: str) -> int:
        """Convert risk level to numeric score"""
        risk_mapping = {
            "low": 2,
            "medium": 5,
            "high": 8,
            "critical": 10
        }
        return risk_mapping.get(risk_level, 5)


async def analyze_asset_risk_agentic(
    asset_data: Dict[str, Any], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Main function to analyze asset risk using agentic intelligence.
    
    This function creates a RiskAssessmentAgent and executes comprehensive threat analysis
    including security, operational, and compliance risk assessment.
    """
    
    agent = RiskAssessmentAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    return await agent.analyze_asset_risk(asset_data)


# Example usage pattern for integration with discovery flow
async def enrich_assets_with_risk_intelligence(
    assets: List[Dict[str, Any]], 
    crewai_service, 
    client_account_id: uuid.UUID, 
    engagement_id: uuid.UUID,
    flow_id: Optional[uuid.UUID] = None
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with comprehensive risk intelligence.
    
    This function processes assets in batches and enriches them with:
    - Overall risk assessment (Low/Medium/High/Critical)
    - Security, operational, and compliance risk scores
    - Threat analysis and vulnerability summaries
    - Immediate actions and long-term mitigation recommendations
    """
    
    enriched_assets = []
    
    # Initialize the risk assessment agent once for batch processing
    agent = RiskAssessmentAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id
    )
    
    for i, asset in enumerate(assets):
        try:
            logger.info(f"🛡️ Assessing risk for asset {i+1}/{len(assets)}: {asset.get('name')}")
            
            # Perform agentic risk assessment
            assessment_result = await agent.analyze_asset_risk(asset)
            
            # Merge assessment results with asset data
            enriched_asset = {**asset}
            enriched_asset.update({
                "risk_assessment": assessment_result.get("risk_assessment"),
                "security_risk_score": assessment_result.get("security_risk_score"),
                "operational_risk_score": assessment_result.get("operational_risk_score"),
                "compliance_risk_score": assessment_result.get("compliance_risk_score"),
                "risk_analysis_reasoning": assessment_result.get("primary_threats"),
                "vulnerability_summary": assessment_result.get("vulnerability_summary"),
                "risk_mitigation_actions": assessment_result.get("immediate_actions"),
                "risk_recommendations": assessment_result.get("longterm_recommendations"),
                "enrichment_status": "agent_enriched",
                "last_enriched_at": datetime.utcnow(),
                "last_enriched_by_agent": "Risk Assessment Agent"
            })
            
            enriched_assets.append(enriched_asset)
            
            logger.info(f"✅ Risk assessment completed - Level: {assessment_result.get('risk_assessment')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to assess risk for asset {asset.get('name')}: {e}")
            
            # Add asset with basic risk assessment
            enriched_asset = {**asset}
            enriched_asset.update({
                "risk_assessment": "medium",  # Default medium risk
                "risk_analysis_reasoning": "Risk assessment failed - using default classification",
                "enrichment_status": "basic",
                "last_enriched_at": datetime.utcnow()
            })
            enriched_assets.append(enriched_asset)
    
    logger.info(f"✅ Completed risk assessment for {len(enriched_assets)} assets")
    return enriched_assets