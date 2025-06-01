"""
Client Context Manager
Client/engagement-specific context management for agent behavior adaptation.
Implements Task C.1: Client/Engagement-Specific Context Management.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class ClientContextManager:
    """
    Manages client and engagement-specific context for agent behavior adaptation.
    Handles user preferences, organizational patterns, and clarification history.
    """
    
    def __init__(self, context_data_path: str = "data/client_context"):
        self.context_data_path = Path(context_data_path)
        self.context_data_path.mkdir(parents=True, exist_ok=True)
        
        # Client context storage
        self.client_contexts = {}
        self.engagement_contexts = {}
        
        # Load existing context data
        self._load_context_data()
        
        logger.info("Client Context Manager initialized")
    
    # === CLIENT CONTEXT MANAGEMENT ===
    
    async def create_client_context(self, client_account_id: int, 
                                  client_data: Dict[str, Any]) -> None:
        """Create or update client-specific context."""
        
        if client_account_id not in self.client_contexts:
            self.client_contexts[client_account_id] = {
                "client_id": client_account_id,
                "organizational_patterns": {},
                "user_preferences": {},
                "industry_context": {},
                "technology_patterns": {},
                "clarification_history": [],
                "agent_adaptations": {},
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": None
            }
        
        context = self.client_contexts[client_account_id]
        
        # Update client data
        context.update({
            "client_name": client_data.get("client_name"),
            "industry": client_data.get("industry"),
            "organization_size": client_data.get("organization_size"),
            "technology_profile": client_data.get("technology_profile", {}),
            "last_updated": datetime.utcnow().isoformat()
        })
        
        await self._save_context_data()
        
        logger.info(f"Created/updated client context for client {client_account_id}")
    
    async def create_engagement_context(self, engagement_id: str, 
                                      client_account_id: int,
                                      engagement_data: Dict[str, Any]) -> None:
        """Create or update engagement-specific context."""
        
        if engagement_id not in self.engagement_contexts:
            self.engagement_contexts[engagement_id] = {
                "engagement_id": engagement_id,
                "client_account_id": client_account_id,
                "engagement_preferences": {},
                "project_specific_patterns": {},
                "stakeholder_preferences": {},
                "asset_classification_patterns": {},
                "clarification_responses": {},
                "agent_learning_adaptations": {},
                "migration_preferences": {},
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": None
            }
        
        context = self.engagement_contexts[engagement_id]
        
        # Update engagement data
        context.update({
            "engagement_name": engagement_data.get("engagement_name"),
            "project_type": engagement_data.get("project_type"),
            "scope": engagement_data.get("scope", {}),
            "stakeholders": engagement_data.get("stakeholders", []),
            "timeline": engagement_data.get("timeline", {}),
            "last_updated": datetime.utcnow().isoformat()
        })
        
        await self._save_context_data()
        
        logger.info(f"Created/updated engagement context for engagement {engagement_id}")
    
    # === ORGANIZATIONAL PATTERN LEARNING ===
    
    async def learn_organizational_pattern(self, client_account_id: int, 
                                         pattern_data: Dict[str, Any]) -> None:
        """Learn organizational patterns specific to the client."""
        
        if client_account_id not in self.client_contexts:
            await self.create_client_context(client_account_id, {})
        
        context = self.client_contexts[client_account_id]
        pattern_type = pattern_data.get("pattern_type")
        pattern_details = pattern_data.get("pattern_details", {})
        
        if pattern_type not in context["organizational_patterns"]:
            context["organizational_patterns"][pattern_type] = {
                "patterns": [],
                "confidence": 0.0,
                "examples": [],
                "learning_count": 0
            }
        
        org_pattern = context["organizational_patterns"][pattern_type]
        org_pattern["patterns"].append({
            "details": pattern_details,
            "learned_at": datetime.utcnow().isoformat(),
            "source": pattern_data.get("source", "unknown")
        })
        org_pattern["examples"].extend(pattern_data.get("examples", []))
        org_pattern["learning_count"] += 1
        
        # Update confidence based on consistency
        await self._update_pattern_confidence(org_pattern)
        
        context["last_updated"] = datetime.utcnow().isoformat()
        await self._save_context_data()
        
        logger.info(f"Learned organizational pattern {pattern_type} for client {client_account_id}")
    
    async def get_organizational_patterns(self, client_account_id: int) -> Dict[str, Any]:
        """Get organizational patterns for a client."""
        
        if client_account_id not in self.client_contexts:
            return {}
        
        return self.client_contexts[client_account_id].get("organizational_patterns", {})
    
    # === USER PREFERENCE MANAGEMENT ===
    
    async def learn_user_preference(self, engagement_id: str, 
                                  preference_data: Dict[str, Any]) -> None:
        """Learn user preferences for the engagement."""
        
        if engagement_id not in self.engagement_contexts:
            # Need to create engagement context - requires client_account_id
            logger.warning(f"Engagement context not found for {engagement_id}")
            return
        
        context = self.engagement_contexts[engagement_id]
        preference_type = preference_data.get("preference_type")
        preference_value = preference_data.get("preference_value")
        user_context = preference_data.get("user_context", {})
        
        if preference_type not in context["engagement_preferences"]:
            context["engagement_preferences"][preference_type] = {
                "values": [],
                "most_preferred": None,
                "confidence": 0.0,
                "user_contexts": []
            }
        
        pref_pattern = context["engagement_preferences"][preference_type]
        pref_pattern["values"].append({
            "value": preference_value,
            "context": user_context,
            "learned_at": datetime.utcnow().isoformat()
        })
        pref_pattern["user_contexts"].append(user_context)
        
        # Update most preferred based on frequency
        await self._update_most_preferred(pref_pattern)
        
        context["last_updated"] = datetime.utcnow().isoformat()
        await self._save_context_data()
        
        logger.info(f"Learned user preference {preference_type} for engagement {engagement_id}")
    
    async def get_user_preferences(self, engagement_id: str) -> Dict[str, Any]:
        """Get user preferences for an engagement."""
        
        if engagement_id not in self.engagement_contexts:
            return {}
        
        return self.engagement_contexts[engagement_id].get("engagement_preferences", {})
    
    # === CLARIFICATION HISTORY MANAGEMENT ===
    
    async def store_clarification_response(self, engagement_id: str, 
                                         clarification_data: Dict[str, Any]) -> None:
        """Store clarification responses for learning."""
        
        if engagement_id not in self.engagement_contexts:
            logger.warning(f"Engagement context not found for {engagement_id}")
            return
        
        context = self.engagement_contexts[engagement_id]
        
        clarification_entry = {
            "question_id": clarification_data.get("question_id"),
            "question_type": clarification_data.get("question_type"),
            "question": clarification_data.get("question"),
            "user_response": clarification_data.get("user_response"),
            "context": clarification_data.get("context", {}),
            "agent_id": clarification_data.get("agent_id"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        question_type = clarification_data.get("question_type", "general")
        if question_type not in context["clarification_responses"]:
            context["clarification_responses"][question_type] = []
        
        context["clarification_responses"][question_type].append(clarification_entry)
        
        # Learn from the response
        await self._learn_from_clarification(engagement_id, clarification_entry)
        
        context["last_updated"] = datetime.utcnow().isoformat()
        await self._save_context_data()
        
        logger.info(f"Stored clarification response for engagement {engagement_id}")
    
    async def get_clarification_history(self, engagement_id: str, 
                                      question_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get clarification history for an engagement."""
        
        if engagement_id not in self.engagement_contexts:
            return []
        
        context = self.engagement_contexts[engagement_id]
        clarifications = context.get("clarification_responses", {})
        
        if question_type:
            return clarifications.get(question_type, [])
        
        # Return all clarifications
        all_clarifications = []
        for q_type, responses in clarifications.items():
            all_clarifications.extend(responses)
        
        return sorted(all_clarifications, key=lambda x: x["timestamp"])
    
    # === AGENT BEHAVIOR ADAPTATION ===
    
    async def adapt_agent_behavior(self, engagement_id: str, agent_id: str, 
                                 adaptation_data: Dict[str, Any]) -> None:
        """Store agent behavior adaptations for the engagement."""
        
        if engagement_id not in self.engagement_contexts:
            logger.warning(f"Engagement context not found for {engagement_id}")
            return
        
        context = self.engagement_contexts[engagement_id]
        
        if agent_id not in context["agent_learning_adaptations"]:
            context["agent_learning_adaptations"][agent_id] = {
                "adaptations": [],
                "behavior_patterns": {},
                "confidence_adjustments": {},
                "question_preferences": {}
            }
        
        agent_adaptations = context["agent_learning_adaptations"][agent_id]
        
        adaptation_entry = {
            "adaptation_type": adaptation_data.get("adaptation_type"),
            "adaptation_details": adaptation_data.get("adaptation_details", {}),
            "trigger_context": adaptation_data.get("trigger_context", {}),
            "expected_improvement": adaptation_data.get("expected_improvement"),
            "adapted_at": datetime.utcnow().isoformat()
        }
        
        agent_adaptations["adaptations"].append(adaptation_entry)
        
        # Update behavior patterns
        adaptation_type = adaptation_data.get("adaptation_type")
        if adaptation_type:
            if adaptation_type not in agent_adaptations["behavior_patterns"]:
                agent_adaptations["behavior_patterns"][adaptation_type] = []
            
            agent_adaptations["behavior_patterns"][adaptation_type].append(
                adaptation_data.get("adaptation_details", {})
            )
        
        context["last_updated"] = datetime.utcnow().isoformat()
        await self._save_context_data()
        
        logger.info(f"Stored agent adaptation for {agent_id} in engagement {engagement_id}")
    
    async def get_agent_adaptations(self, engagement_id: str, 
                                  agent_id: str) -> Dict[str, Any]:
        """Get agent behavior adaptations for an engagement."""
        
        if engagement_id not in self.engagement_contexts:
            return {}
        
        context = self.engagement_contexts[engagement_id]
        return context.get("agent_learning_adaptations", {}).get(agent_id, {})
    
    # === MIGRATION PREFERENCE MANAGEMENT ===
    
    async def learn_migration_preferences(self, engagement_id: str, 
                                        migration_data: Dict[str, Any]) -> None:
        """Learn migration-specific preferences for the engagement."""
        
        if engagement_id not in self.engagement_contexts:
            logger.warning(f"Engagement context not found for {engagement_id}")
            return
        
        context = self.engagement_contexts[engagement_id]
        
        migration_type = migration_data.get("migration_type")
        preference_details = migration_data.get("preference_details", {})
        
        if migration_type not in context["migration_preferences"]:
            context["migration_preferences"][migration_type] = {
                "preferences": [],
                "patterns": {},
                "constraints": [],
                "priorities": []
            }
        
        migration_prefs = context["migration_preferences"][migration_type]
        migration_prefs["preferences"].append({
            "details": preference_details,
            "context": migration_data.get("context", {}),
            "learned_at": datetime.utcnow().isoformat()
        })
        
        # Extract patterns from preferences
        await self._extract_migration_patterns(migration_prefs, preference_details)
        
        context["last_updated"] = datetime.utcnow().isoformat()
        await self._save_context_data()
        
        logger.info(f"Learned migration preferences for engagement {engagement_id}")
    
    # === CONTEXT RETRIEVAL METHODS ===
    
    async def get_client_context(self, client_account_id: int) -> Dict[str, Any]:
        """Get complete client context."""
        
        return self.client_contexts.get(client_account_id, {})
    
    async def get_engagement_context(self, engagement_id: str) -> Dict[str, Any]:
        """Get complete engagement context."""
        
        return self.engagement_contexts.get(engagement_id, {})
    
    async def get_combined_context(self, engagement_id: str) -> Dict[str, Any]:
        """Get combined client and engagement context."""
        
        engagement_context = self.engagement_contexts.get(engagement_id, {})
        client_account_id = engagement_context.get("client_account_id")
        
        if not client_account_id:
            return engagement_context
        
        client_context = self.client_contexts.get(client_account_id, {})
        
        return {
            "client_context": client_context,
            "engagement_context": engagement_context,
            "combined_at": datetime.utcnow().isoformat()
        }
    
    # === UTILITY METHODS ===
    
    async def _update_pattern_confidence(self, pattern: Dict[str, Any]) -> None:
        """Update confidence based on pattern consistency."""
        
        patterns = pattern.get("patterns", [])
        if len(patterns) < 2:
            pattern["confidence"] = 0.5
            return
        
        # Simple confidence calculation based on consistency
        # This would be enhanced with more sophisticated pattern matching
        pattern["confidence"] = min(0.9, 0.3 + (len(patterns) * 0.1))
    
    async def _update_most_preferred(self, preference_pattern: Dict[str, Any]) -> None:
        """Update most preferred value based on frequency."""
        
        values = preference_pattern.get("values", [])
        if not values:
            return
        
        # Count preference frequencies
        value_counts = {}
        for pref in values:
            value = pref["value"]
            value_counts[value] = value_counts.get(value, 0) + 1
        
        # Find most frequent
        most_preferred = max(value_counts.items(), key=lambda x: x[1])[0]
        preference_pattern["most_preferred"] = most_preferred
        
        # Calculate confidence
        total_count = len(values)
        max_count = value_counts[most_preferred]
        preference_pattern["confidence"] = max_count / total_count
    
    async def _learn_from_clarification(self, engagement_id: str, 
                                      clarification_entry: Dict[str, Any]) -> None:
        """Learn patterns from clarification responses."""
        
        question_type = clarification_entry.get("question_type")
        user_response = clarification_entry.get("user_response")
        
        # Extract learning patterns from the response
        if question_type == "field_mapping":
            await self._learn_field_mapping_from_clarification(engagement_id, clarification_entry)
        elif question_type == "data_classification":
            await self._learn_classification_from_clarification(engagement_id, clarification_entry)
        elif question_type == "business_context":
            await self._learn_business_context_from_clarification(engagement_id, clarification_entry)
    
    async def _learn_field_mapping_from_clarification(self, engagement_id: str, 
                                                    entry: Dict[str, Any]) -> None:
        """Learn field mapping patterns from clarification responses."""
        
        context = self.engagement_contexts[engagement_id]
        
        # Extract field mapping information
        user_response = entry.get("user_response")
        question_context = entry.get("context", {})
        
        if isinstance(user_response, dict) and "field_mappings" in user_response:
            field_mappings = user_response["field_mappings"]
            
            if "asset_classification_patterns" not in context:
                context["asset_classification_patterns"] = {}
            
            for original_field, mapped_field in field_mappings.items():
                if original_field not in context["asset_classification_patterns"]:
                    context["asset_classification_patterns"][original_field] = {
                        "mappings": [],
                        "most_common": None,
                        "confidence": 0.0
                    }
                
                pattern = context["asset_classification_patterns"][original_field]
                pattern["mappings"].append({
                    "mapped_to": mapped_field,
                    "context": question_context,
                    "learned_at": datetime.utcnow().isoformat()
                })
                
                # Update most common mapping
                await self._update_most_common_mapping(pattern)
    
    async def _learn_classification_from_clarification(self, engagement_id: str, 
                                                     entry: Dict[str, Any]) -> None:
        """Learn data classification patterns from clarification responses."""
        
        # This would extract classification patterns from user responses
        # and store them for future use
        pass
    
    async def _learn_business_context_from_clarification(self, engagement_id: str, 
                                                       entry: Dict[str, Any]) -> None:
        """Learn business context patterns from clarification responses."""
        
        # This would extract business context information from user responses
        # and store organizational patterns
        pass
    
    async def _update_most_common_mapping(self, pattern: Dict[str, Any]) -> None:
        """Update most common mapping for a field pattern."""
        
        mappings = pattern.get("mappings", [])
        if not mappings:
            return
        
        # Count mapping frequencies
        mapping_counts = {}
        for mapping in mappings:
            mapped_to = mapping["mapped_to"]
            mapping_counts[mapped_to] = mapping_counts.get(mapped_to, 0) + 1
        
        # Find most common
        most_common = max(mapping_counts.items(), key=lambda x: x[1])[0]
        pattern["most_common"] = most_common
        
        # Calculate confidence
        total_count = len(mappings)
        max_count = mapping_counts[most_common]
        pattern["confidence"] = max_count / total_count
    
    async def _extract_migration_patterns(self, migration_prefs: Dict[str, Any], 
                                        preference_details: Dict[str, Any]) -> None:
        """Extract patterns from migration preferences."""
        
        # Extract common patterns from migration preferences
        for key, value in preference_details.items():
            if key not in migration_prefs["patterns"]:
                migration_prefs["patterns"][key] = []
            
            migration_prefs["patterns"][key].append(value)
    
    # === DATA PERSISTENCE ===
    
    def _load_context_data(self) -> None:
        """Load existing context data from storage."""
        
        try:
            # Load client contexts
            client_file = self.context_data_path / "client_contexts.json"
            if client_file.exists():
                with open(client_file, 'r') as f:
                    self.client_contexts = json.load(f)
            
            # Load engagement contexts
            engagement_file = self.context_data_path / "engagement_contexts.json"
            if engagement_file.exists():
                with open(engagement_file, 'r') as f:
                    self.engagement_contexts = json.load(f)
            
            logger.info("Loaded existing context data")
        except Exception as e:
            logger.error(f"Error loading context data: {e}")
    
    async def _save_context_data(self) -> None:
        """Save context data to storage."""
        
        try:
            # Save client contexts
            client_file = self.context_data_path / "client_contexts.json"
            with open(client_file, 'w') as f:
                json.dump(self.client_contexts, f, indent=2)
            
            # Save engagement contexts
            engagement_file = self.context_data_path / "engagement_contexts.json"
            with open(engagement_file, 'w') as f:
                json.dump(self.engagement_contexts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context data: {e}")
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """Get statistics about context management."""
        
        total_clients = len(self.client_contexts)
        total_engagements = len(self.engagement_contexts)
        
        # Count patterns across all contexts
        total_org_patterns = 0
        total_clarifications = 0
        
        for context in self.client_contexts.values():
            total_org_patterns += len(context.get("organizational_patterns", {}))
        
        for context in self.engagement_contexts.values():
            clarifications = context.get("clarification_responses", {})
            for responses in clarifications.values():
                total_clarifications += len(responses)
        
        return {
            "total_clients": total_clients,
            "total_engagements": total_engagements,
            "organizational_patterns": total_org_patterns,
            "clarification_responses": total_clarifications
        }

# Global instance for client context management
client_context_manager = ClientContextManager() 