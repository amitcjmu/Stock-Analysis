"""
Discovery Agent Orchestrator - Coordinates individual Discovery Flow agents
Manages agent-first workflow with strategic crew escalation
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import uuid

from .base_discovery_agent import AgentResult, AgentClarificationRequest, AgentInsight
from .data_import_validation_agent import DataImportValidationAgent
from .attribute_mapping_agent import AttributeMappingAgent
from .data_cleansing_agent import DataCleansingAgent

logger = logging.getLogger(__name__)

class DiscoveryAgentOrchestrator:
    """
    Discovery Agent Orchestrator
    
    Coordinates individual Discovery Flow agents in an agent-first architecture,
    managing sequential processing with parallel optimization where possible.
    """
    
    def __init__(self):
        self.orchestrator_id = f"discovery_orchestrator_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger("agents.discovery_orchestrator")
        
        # Initialize individual agents
        self.agents = {
            'data_validation': DataImportValidationAgent(),
            'attribute_mapping': AttributeMappingAgent(),
            'data_cleansing': DataCleansingAgent()
        }
        
        # Agent execution order
        self.agent_execution_order = [
            'data_validation',
            'attribute_mapping', 
            'data_cleansing'
        ]
        
        # Orchestration state
        self.current_execution = None
        self.execution_history = []
        self.all_clarifications = []
        self.all_insights = []
        
    async def execute_discovery_agents(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the Discovery Flow using individual agents
        
        Args:
            data: Input data for processing
            context: Flow context with metadata
            
        Returns:
            Comprehensive results from all agents
        """
        start_time = time.time()
        context = context or {}
        
        execution_id = str(uuid.uuid4())
        self.current_execution = execution_id
        
        self.logger.info(f"🚀 Starting Discovery Agent orchestration (ID: {execution_id})")
        
        try:
            # Initialize orchestration results
            orchestration_results = {
                'execution_id': execution_id,
                'agent_results': {},
                'data_flow': {},
                'overall_confidence': 0.0,
                'status': 'running',
                'all_clarifications': [],
                'all_insights': [],
                'execution_summary': {},
                'recommendations': []
            }
            
            # Execute agents in sequence with data flow
            current_data = data.copy()
            
            for agent_name in self.agent_execution_order:
                agent = self.agents[agent_name]
                
                self.logger.info(f"🤖 Executing {agent.agent_name}...")
                
                # Execute agent
                agent_result = await self._execute_agent_with_monitoring(
                    agent, current_data, context, agent_name
                )
                
                # Store agent result
                orchestration_results['agent_results'][agent_name] = agent_result.dict()
                
                # Collect clarifications and insights
                orchestration_results['all_clarifications'].extend(
                    [req.dict() for req in agent_result.clarifications_requested]
                )
                orchestration_results['all_insights'].extend(
                    [insight.dict() for insight in agent_result.insights_generated]
                )
                
                # Update data flow for next agent
                if agent_result.status == 'success':
                    current_data = await self._prepare_data_for_next_agent(
                        current_data, agent_result, agent_name
                    )
                    orchestration_results['data_flow'][agent_name] = {
                        'status': 'success',
                        'data_passed': True,
                        'confidence': agent_result.confidence_score
                    }
                else:
                    # Handle partial success or failure
                    self.logger.warning(f"⚠️ {agent.agent_name} completed with status: {agent_result.status}")
                    orchestration_results['data_flow'][agent_name] = {
                        'status': agent_result.status,
                        'data_passed': agent_result.status != 'failed',
                        'confidence': agent_result.confidence_score,
                        'errors': agent_result.errors
                    }
                    
                    # Continue with available data if not a complete failure
                    if agent_result.status != 'failed' and agent_result.data:
                        current_data = await self._prepare_data_for_next_agent(
                            current_data, agent_result, agent_name
                        )
            
            # Analyze overall results
            await self._analyze_orchestration_results(orchestration_results, current_data)
            
            # Generate orchestration insights
            await self._generate_orchestration_insights(orchestration_results)
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"✅ Discovery Agent orchestration completed in {execution_time:.2f}s")
            
            # Update execution history
            self.execution_history.append({
                'execution_id': execution_id,
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'status': orchestration_results['status'],
                'agents_executed': len(self.agent_execution_order),
                'total_clarifications': len(orchestration_results['all_clarifications']),
                'total_insights': len(orchestration_results['all_insights'])
            })
            
            return orchestration_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Discovery Agent orchestration failed: {str(e)}")
            
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': execution_time,
                'agent_results': {},
                'all_clarifications': [],
                'all_insights': []
            }
    
    async def _execute_agent_with_monitoring(self, agent, data: Dict[str, Any], context: Dict[str, Any], agent_name: str) -> AgentResult:
        """Execute an agent with monitoring and error handling"""
        try:
            # Reset agent state for clean execution
            agent.reset_agent_state()
            
            # Execute agent
            result = await agent.execute(data, context)
            
            self.logger.info(f"✅ {agent.agent_name} completed: {result.status} "
                           f"({result.confidence_score:.1f}% confidence, {result.execution_time:.2f}s)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {agent.agent_name} execution failed: {str(e)}")
            
            # Create error result
            return AgentResult(
                agent_name=agent.agent_name,
                execution_time=0.0,
                confidence_score=0.0,
                status="failed",
                data={},
                errors=[f"Agent execution failed: {str(e)}"]
            )
    
    async def _prepare_data_for_next_agent(self, current_data: Dict[str, Any], agent_result: AgentResult, agent_name: str) -> Dict[str, Any]:
        """Prepare data flow for the next agent in sequence"""
        next_data = current_data.copy()
        
        # Data flow logic based on agent type
        if agent_name == 'data_validation':
            # Pass validation results and cleaned data structure
            if agent_result.data:
                next_data['validation_results'] = agent_result.data
                next_data['validation_confidence'] = agent_result.confidence_score
        
        elif agent_name == 'attribute_mapping':
            # Pass field mappings for data cleansing
            if agent_result.data:
                critical_mappings = agent_result.data.get('critical_mappings', {})
                secondary_mappings = agent_result.data.get('secondary_mappings', {})
                
                # Combine mappings for cleansing agent
                all_mappings = {**critical_mappings, **secondary_mappings}
                next_data['field_mappings'] = all_mappings
                next_data['mapping_confidence'] = agent_result.confidence_score
                next_data['mapping_summary'] = agent_result.data.get('summary', {})
        
        elif agent_name == 'data_cleansing':
            # Pass cleaned data as final output
            if agent_result.data and 'cleaned_data' in agent_result.data:
                next_data['cleaned_data'] = agent_result.data['cleaned_data']
                next_data['cleansing_confidence'] = agent_result.confidence_score
                next_data['quality_metrics'] = agent_result.data.get('data_quality_metrics', {})
        
        return next_data
    
    async def _analyze_orchestration_results(self, results: Dict[str, Any], final_data: Dict[str, Any]):
        """Analyze overall orchestration results and determine status"""
        agent_results = results['agent_results']
        
        # Calculate overall confidence
        confidences = []
        statuses = []
        
        for agent_name, agent_result in agent_results.items():
            confidences.append(agent_result['confidence_score'])
            statuses.append(agent_result['status'])
        
        # Weighted confidence (later agents weighted higher as they depend on earlier ones)
        if confidences:
            weights = [1.0, 1.2, 1.5][:len(confidences)]  # Increasing weights
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
            results['overall_confidence'] = weighted_confidence
        else:
            results['overall_confidence'] = 0.0
        
        # Determine overall status
        if 'failed' in statuses:
            results['status'] = 'failed'
        elif 'partial' in statuses or results['overall_confidence'] < 70:
            results['status'] = 'partial'
        else:
            results['status'] = 'success'
        
        # Create execution summary
        results['execution_summary'] = {
            'total_agents': len(self.agent_execution_order),
            'successful_agents': statuses.count('success'),
            'partial_agents': statuses.count('partial'),
            'failed_agents': statuses.count('failed'),
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0.0,
            'total_execution_time': sum(
                agent_result['execution_time'] for agent_result in agent_results.values()
            ),
            'data_records_processed': len(final_data.get('raw_data', [])),
            'final_cleaned_records': len(final_data.get('cleaned_data', []))
        }
    
    async def _generate_orchestration_insights(self, results: Dict[str, Any]):
        """Generate high-level orchestration insights"""
        summary = results['execution_summary']
        
        # Overall execution insight
        orchestration_insight = {
            'insight_id': str(uuid.uuid4()),
            'title': 'Discovery Agent Orchestration Summary',
            'description': f"Executed {summary['total_agents']} agents: "
                         f"{summary['successful_agents']} successful, "
                         f"{summary['partial_agents']} partial, "
                         f"{summary['failed_agents']} failed. "
                         f"Overall confidence: {results['overall_confidence']:.1f}%",
            'confidence_score': results['overall_confidence'],
            'category': 'orchestration',
            'actionable': summary['failed_agents'] > 0 or summary['partial_agents'] > 0,
            'action_items': []
        }
        
        # Add action items based on results
        if summary['failed_agents'] > 0:
            orchestration_insight['action_items'].append("Review failed agent executions")
        if summary['partial_agents'] > 0:
            orchestration_insight['action_items'].append("Address partial agent completions")
        if len(results['all_clarifications']) > 0:
            orchestration_insight['action_items'].append(f"Respond to {len(results['all_clarifications'])} agent clarifications")
        
        results['all_insights'].append(orchestration_insight)
        
        # Data processing insight
        if summary['data_records_processed'] > 0:
            processing_insight = {
                'insight_id': str(uuid.uuid4()),
                'title': 'Data Processing Results',
                'description': f"Processed {summary['data_records_processed']} records, "
                             f"produced {summary['final_cleaned_records']} cleaned records. "
                             f"Processing time: {summary['total_execution_time']:.2f}s",
                'confidence_score': 85.0,
                'category': 'processing',
                'actionable': False,
                'action_items': []
            }
            results['all_insights'].append(processing_insight)
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents"""
        if agent_name and agent_name in self.agents:
            return self.agents[agent_name].get_agent_status()
        
        # Return status of all agents
        return {
            agent_name: agent.get_agent_status() 
            for agent_name, agent in self.agents.items()
        }
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get overall orchestration status"""
        return {
            'orchestrator_id': self.orchestrator_id,
            'current_execution': self.current_execution,
            'total_executions': len(self.execution_history),
            'agent_count': len(self.agents),
            'execution_order': self.agent_execution_order,
            'recent_executions': self.execution_history[-5:] if self.execution_history else [],
            'agents_status': self.get_agent_status()
        }
    
    async def process_clarification_response(self, question_id: str, response: Dict[str, Any]) -> bool:
        """Process user response to agent clarification"""
        # Find which agent owns this clarification
        for agent_name, agent in self.agents.items():
            if agent.process_clarification_response(question_id, response):
                self.logger.info(f"✅ Clarification response processed by {agent.agent_name}")
                return True
        
        self.logger.warning(f"⚠️ No agent found for clarification ID: {question_id}")
        return False
    
    async def get_pending_clarifications(self) -> List[Dict[str, Any]]:
        """Get all pending clarifications from all agents"""
        all_clarifications = []
        
        for agent_name, agent in self.agents.items():
            for clarification in agent.clarifications_pending:
                clarification_dict = clarification.dict()
                clarification_dict['agent_name'] = agent.agent_name
                clarification_dict['agent_id'] = agent.agent_id
                all_clarifications.append(clarification_dict)
        
        return all_clarifications
    
    async def get_all_insights(self) -> List[Dict[str, Any]]:
        """Get all insights from all agents"""
        all_insights = []
        
        for agent_name, agent in self.agents.items():
            for insight in agent.insights_generated:
                insight_dict = insight.dict()
                insight_dict['agent_name'] = agent.agent_name
                insight_dict['agent_id'] = agent.agent_id
                all_insights.append(insight_dict)
        
        return all_insights
    
    def reset_all_agents(self):
        """Reset state for all agents"""
        for agent in self.agents.values():
            agent.reset_agent_state()
        
        self.all_clarifications.clear()
        self.all_insights.clear()
        self.current_execution = None
        
        self.logger.info("🔄 All agents reset for new execution")
    
    async def execute_single_agent(self, agent_name: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """Execute a single agent independently"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        self.logger.info(f"🤖 Executing single agent: {agent.agent_name}")
        
        return await self._execute_agent_with_monitoring(agent, data, context, agent_name) 