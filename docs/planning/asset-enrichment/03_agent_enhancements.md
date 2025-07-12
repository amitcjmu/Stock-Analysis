# CrewAI Agent Enhancement Specifications

## Overview

This document details how existing CrewAI agents will be enhanced to support intelligent asset enrichment while maintaining their core functionality. Each agent gains new capabilities for analyzing asset patterns, generating targeted questions, and learning from user feedback.

## Enhanced Agent Architecture

### **Agent Enhancement Pattern**

```python
class EnhancedAgentBase:
    """Base class for enhanced agents with enrichment capabilities"""
    
    def __init__(self):
        self.enrichment_analyzer = AssetEnrichmentAnalyzer()
        self.question_generator = QuestionGenerator()
        self.confidence_calculator = ConfidenceCalculator()
        self.learning_system = AgentLearningSystem()
    
    async def execute_with_enrichment(self, flow_id: str, phase_context: dict):
        # Execute core agent functionality
        core_results = await self.execute_core_logic(flow_id, phase_context)
        
        # Perform enrichment analysis
        enrichment_analysis = await self.analyze_enrichment_opportunities(
            flow_id, core_results
        )
        
        # Generate user questions if needed
        if enrichment_analysis.requires_user_input:
            questions = await self.generate_enrichment_questions(
                enrichment_analysis
            )
            await self.submit_questions_to_ui_bridge(questions)
        
        # Return combined results
        return {
            "core_results": core_results,
            "enrichment_analysis": enrichment_analysis,
            "questions_generated": len(questions) if 'questions' in locals() else 0
        }
```

## Agent-Specific Enhancements

### **1. DataCleansingCrew → AssetClassificationAgent**

#### **Enhanced Capabilities**

```python
class EnhancedDataCleansingCrew(CrewAIDataCleansingCrew):
    """Enhanced data cleansing with asset classification capabilities"""
    
    async def execute_cleansing_with_classification(self, flow_id: str):
        # Core data cleansing (existing functionality)
        cleansing_results = await self._perform_data_cleansing(flow_id)
        
        # NEW: Asset classification analysis
        assets = await self.get_flow_assets(flow_id)
        classification_analysis = await self._analyze_asset_classifications(assets)
        
        # NEW: Critical field gap analysis
        field_gaps = await self._identify_critical_field_gaps(assets)
        
        # NEW: Generate classification questions
        questions = []
        if classification_analysis.uncertain_classifications:
            questions.extend(
                await self._generate_classification_questions(
                    classification_analysis.uncertain_classifications
                )
            )
        
        if field_gaps.missing_critical_fields:
            questions.extend(
                await self._generate_field_gap_questions(
                    field_gaps.missing_critical_fields
                )
            )
        
        # Submit questions to UI bridge
        if questions:
            await self.agent_ui_bridge.add_batch_questions(questions)
        
        return {
            "cleansing": cleansing_results,
            "classification": classification_analysis,
            "field_gaps": field_gaps,
            "questions_pending": len(questions)
        }
    
    async def _analyze_asset_classifications(self, assets: List[Asset]) -> dict:
        """Analyze assets for type and subtype classification"""
        analysis_results = {
            "total_assets": len(assets),
            "classified_assets": 0,
            "uncertain_classifications": [],
            "confidence_scores": {},
            "suggested_subtypes": {}
        }
        
        for asset in assets:
            # Analyze hostname patterns
            hostname_score = self._analyze_hostname_pattern(asset.hostname)
            
            # Analyze operating system and software patterns
            software_score = self._analyze_software_patterns(asset)
            
            # Analyze network and port patterns from raw data
            network_score = self._analyze_network_patterns(asset.raw_data)
            
            # Calculate overall confidence
            overall_confidence = (hostname_score + software_score + network_score) / 3
            
            if overall_confidence >= 0.8:
                analysis_results["classified_assets"] += 1
                analysis_results["confidence_scores"][asset.id] = overall_confidence
            else:
                analysis_results["uncertain_classifications"].append({
                    "asset": asset,
                    "confidence": overall_confidence,
                    "hostname_patterns": hostname_score,
                    "software_patterns": software_score,
                    "network_patterns": network_score
                })
        
        return analysis_results
    
    async def _generate_classification_questions(self, uncertain_assets: List[dict]) -> List[dict]:
        """Generate targeted classification questions for uncertain assets"""
        questions = []
        
        for uncertain_asset in uncertain_assets[:10]:  # Limit to 10 questions per batch
            asset = uncertain_asset["asset"]
            confidence_details = uncertain_asset
            
            # Determine question type based on available data
            if asset.hostname and not asset.asset_type:
                question = await self._generate_hostname_classification_question(
                    asset, confidence_details
                )
            elif asset.operating_system and not asset.asset_subtype:
                question = await self._generate_subtype_classification_question(
                    asset, confidence_details
                )
            else:
                question = await self._generate_general_classification_question(
                    asset, confidence_details
                )
            
            questions.append(question)
        
        return questions
    
    async def _generate_hostname_classification_question(self, asset: Asset, confidence: dict) -> dict:
        """Generate hostname-based classification question"""
        
        # Analyze hostname for patterns
        hostname_analysis = self._analyze_hostname_pattern(asset.hostname)
        suggested_type = self._suggest_type_from_hostname(asset.hostname)
        
        return {
            "id": f"classification_{asset.id}_{uuid.uuid4()}",
            "question_type": "asset_classification",
            "priority": "high" if not asset.asset_type else "medium",
            "title": "Asset Type Verification",
            "question": f"Based on hostname '{asset.hostname}' and system analysis, what type of asset is this?",
            "options": [
                "Web Server",
                "Application Server", 
                "Database Server",
                "Load Balancer",
                "Network Device",
                "Storage System",
                "Other"
            ],
            "context": {
                "asset_id": asset.id,
                "asset_name": asset.name,
                "hostname": asset.hostname,
                "operating_system": asset.operating_system,
                "detected_patterns": hostname_analysis.get("patterns", []),
                "ai_suggestion": suggested_type,
                "confidence": confidence["confidence"],
                "raw_data_hints": self._extract_classification_hints(asset.raw_data)
            }
        }
```

#### **Classification Logic Examples**

```python
def _analyze_hostname_pattern(self, hostname: str) -> dict:
    """Analyze hostname for asset type patterns"""
    patterns = {
        "web": ["web", "www", "apache", "nginx", "iis"],
        "database": ["db", "sql", "mysql", "postgres", "oracle", "mongo"],
        "application": ["app", "api", "service", "backend"],
        "load_balancer": ["lb", "proxy", "haproxy", "f5"],
        "storage": ["nas", "san", "storage", "backup"],
        "network": ["fw", "firewall", "switch", "router", "vpn"]
    }
    
    hostname_lower = hostname.lower()
    matches = {}
    
    for asset_type, keywords in patterns.items():
        score = sum(1 for keyword in keywords if keyword in hostname_lower)
        if score > 0:
            matches[asset_type] = score / len(keywords)
    
    best_match = max(matches.items(), key=lambda x: x[1]) if matches else None
    
    return {
        "best_match": best_match[0] if best_match else None,
        "confidence": best_match[1] if best_match else 0.0,
        "all_matches": matches,
        "patterns": list(matches.keys())
    }

def _analyze_software_patterns(self, asset: Asset) -> float:
    """Analyze software and OS patterns for classification confidence"""
    confidence = 0.0
    
    if asset.operating_system:
        os_lower = asset.operating_system.lower()
        
        # Server OS patterns
        if any(pattern in os_lower for pattern in ["windows server", "ubuntu", "centos", "rhel"]):
            confidence += 0.3
        
        # Database-specific OS configurations
        if any(pattern in os_lower for pattern in ["mysql", "postgres", "oracle"]):
            confidence += 0.4
    
    # Check raw data for software indicators
    if asset.raw_data:
        raw_str = str(asset.raw_data).lower()
        
        # Web server indicators
        if any(pattern in raw_str for pattern in ["apache", "nginx", "iis", "port 80", "port 443"]):
            confidence += 0.3
        
        # Database indicators  
        if any(pattern in raw_str for pattern in ["port 3306", "port 5432", "port 1433"]):
            confidence += 0.4
    
    return min(confidence, 1.0)
```

### **2. InventoryBuildingCrew → BusinessContextAgent**

#### **Enhanced Capabilities**

```python
class EnhancedInventoryBuildingCrew(CrewAIInventoryBuildingCrew):
    """Enhanced inventory building with business context collection"""
    
    async def execute_inventory_with_business_context(self, flow_id: str):
        # Core inventory building (existing functionality)
        inventory_results = await self._build_asset_inventory(flow_id)
        
        # NEW: Business context analysis
        applications = await self.get_applications_by_flow(flow_id)
        business_analysis = await self._analyze_business_context(applications)
        
        # NEW: Application tier identification
        tier_analysis = await self._identify_application_tiers(applications)
        
        # NEW: Generate business context questions
        questions = []
        if business_analysis.requires_clarification:
            questions.extend(
                await self._generate_business_value_questions(
                    business_analysis.applications_needing_context
                )
            )
        
        if tier_analysis.uncertain_tiers:
            questions.extend(
                await self._generate_tier_clarification_questions(
                    tier_analysis.uncertain_tiers
                )
            )
        
        # Submit questions to UI bridge
        if questions:
            await self.agent_ui_bridge.add_batch_questions(questions)
        
        return {
            "inventory": inventory_results,
            "business_context": business_analysis,
            "application_tiers": tier_analysis,
            "questions_pending": len(questions)
        }
    
    async def _analyze_business_context(self, applications: List[Asset]) -> dict:
        """Analyze applications for business context indicators"""
        analysis = {
            "total_applications": len(applications),
            "context_complete": 0,
            "applications_needing_context": [],
            "detected_patterns": {},
            "business_value_suggestions": {}
        }
        
        for app in applications:
            context_completeness = self._calculate_context_completeness(app)
            
            if context_completeness < 0.7:  # Less than 70% complete
                # Analyze name and data for business value indicators
                business_indicators = self._detect_business_value_indicators(app)
                
                analysis["applications_needing_context"].append({
                    "application": app,
                    "completeness": context_completeness,
                    "business_indicators": business_indicators,
                    "suggested_value": business_indicators.get("suggested_value", 5),
                    "confidence": business_indicators.get("confidence", 0.5)
                })
            else:
                analysis["context_complete"] += 1
        
        return analysis
    
    def _detect_business_value_indicators(self, app: Asset) -> dict:
        """Detect business value indicators from app name and data"""
        name_lower = app.name.lower() if app.name else ""
        
        # High value indicators
        high_value_patterns = [
            "customer", "payment", "billing", "order", "sales", "revenue",
            "portal", "api", "gateway", "core", "main", "primary"
        ]
        
        # Critical value indicators
        critical_patterns = [
            "payment", "billing", "transaction", "money", "bank", "credit",
            "security", "auth", "authentication", "login"
        ]
        
        # Internal/support indicators
        internal_patterns = [
            "admin", "internal", "test", "dev", "staging", "backup",
            "monitor", "log", "report", "analytics"
        ]
        
        high_score = sum(1 for pattern in high_value_patterns if pattern in name_lower)
        critical_score = sum(1 for pattern in critical_patterns if pattern in name_lower)
        internal_score = sum(1 for pattern in internal_patterns if pattern in name_lower)
        
        if critical_score > 0:
            return {
                "suggested_value": 9,
                "confidence": 0.85,
                "reasoning": "Critical business functions detected",
                "patterns": critical_patterns
            }
        elif high_score > 0:
            return {
                "suggested_value": 7,
                "confidence": 0.75,
                "reasoning": "High business value indicators found",
                "patterns": high_value_patterns
            }
        elif internal_score > 0:
            return {
                "suggested_value": 3,
                "confidence": 0.65,
                "reasoning": "Internal/support system indicators",
                "patterns": internal_patterns
            }
        else:
            return {
                "suggested_value": 5,
                "confidence": 0.5,
                "reasoning": "No clear business value indicators",
                "patterns": []
            }
    
    async def _generate_business_value_questions(self, apps_needing_context: List[dict]) -> List[dict]:
        """Generate business value assessment questions"""
        questions = []
        
        for app_context in apps_needing_context[:8]:  # Limit to 8 questions
            app = app_context["application"]
            indicators = app_context["business_indicators"]
            
            question = {
                "id": f"business_value_{app.id}_{uuid.uuid4()}",
                "question_type": "business_value_assessment",
                "priority": "high",
                "title": "Application Business Value",
                "question": f"What's the business value/criticality of '{app.name}'?",
                "options": [
                    "Low (1-3) - Internal tools, development systems",
                    "Medium (4-6) - Supporting business operations", 
                    "High (7-8) - Important business functions",
                    "Critical (9-10) - Revenue generating, customer-facing"
                ],
                "context": {
                    "asset_id": app.id,
                    "application_name": app.name,
                    "detected_patterns": indicators.get("patterns", []),
                    "ai_reasoning": indicators.get("reasoning", ""),
                    "ai_suggestion": f"Score: {indicators.get('suggested_value', 5)}",
                    "confidence": indicators.get("confidence", 0.5)
                }
            }
            
            questions.append(question)
        
        return questions
```

### **3. DependencyAnalysisCrew → RiskAssessmentAgent**

#### **Enhanced Capabilities**

```python
class EnhancedDependencyAnalysisCrew(CrewAIDependencyAnalysisCrew):
    """Enhanced dependency analysis with risk assessment capabilities"""
    
    async def execute_dependencies_with_risk_assessment(self, flow_id: str):
        # Core dependency analysis (existing functionality)
        dependency_results = await self._analyze_dependencies(flow_id)
        
        # NEW: Risk assessment based on dependencies and asset data
        assets = await self.get_flow_assets(flow_id)
        risk_analysis = await self._assess_operational_risks(assets, dependency_results)
        
        # NEW: Compliance requirement analysis
        compliance_analysis = await self._analyze_compliance_requirements(assets)
        
        # NEW: Data classification analysis
        data_classification = await self._analyze_data_sensitivity(assets)
        
        # NEW: Generate risk assessment questions
        questions = []
        if risk_analysis.requires_clarification:
            questions.extend(
                await self._generate_risk_clarification_questions(
                    risk_analysis.high_risk_assets
                )
            )
        
        if compliance_analysis.uncertain_requirements:
            questions.extend(
                await self._generate_compliance_questions(
                    compliance_analysis.uncertain_requirements
                )
            )
        
        # Submit questions to UI bridge
        if questions:
            await self.agent_ui_bridge.add_batch_questions(questions)
        
        return {
            "dependencies": dependency_results,
            "risk_assessment": risk_analysis,
            "compliance_analysis": compliance_analysis,
            "data_classification": data_classification,
            "questions_pending": len(questions)
        }
    
    async def _analyze_compliance_requirements(self, assets: List[Asset]) -> dict:
        """Analyze assets for compliance requirement indicators"""
        analysis = {
            "total_assets": len(assets),
            "compliance_identified": 0,
            "uncertain_requirements": [],
            "compliance_patterns": {}
        }
        
        for asset in assets:
            # Check for compliance indicators in name and data
            compliance_indicators = self._detect_compliance_indicators(asset)
            
            if compliance_indicators["confidence"] < 0.8:
                analysis["uncertain_requirements"].append({
                    "asset": asset,
                    "indicators": compliance_indicators,
                    "suggested_requirements": compliance_indicators["suggested_compliance"]
                })
            else:
                analysis["compliance_identified"] += 1
        
        return analysis
    
    def _detect_compliance_indicators(self, asset: Asset) -> dict:
        """Detect compliance requirement indicators"""
        name_lower = asset.name.lower() if asset.name else ""
        
        # Compliance pattern indicators
        compliance_patterns = {
            "PCI-DSS": ["payment", "card", "credit", "transaction", "billing"],
            "HIPAA": ["health", "medical", "patient", "hospital", "clinic"],
            "SOX": ["financial", "accounting", "finance", "audit", "revenue"],
            "GDPR": ["customer", "personal", "profile", "user", "member"]
        }
        
        detected_compliance = []
        max_confidence = 0.0
        
        for compliance, patterns in compliance_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in name_lower)
            if matches > 0:
                confidence = min(matches * 0.3, 1.0)  # Max confidence per pattern type
                detected_compliance.append({
                    "type": compliance,
                    "confidence": confidence,
                    "matched_patterns": [p for p in patterns if p in name_lower]
                })
                max_confidence = max(max_confidence, confidence)
        
        return {
            "suggested_compliance": detected_compliance,
            "confidence": max_confidence,
            "reasoning": f"Detected patterns in asset name: {name_lower}"
        }
    
    async def _generate_compliance_questions(self, uncertain_requirements: List[dict]) -> List[dict]:
        """Generate compliance requirement clarification questions"""
        questions = []
        
        for req_context in uncertain_requirements[:6]:  # Limit to 6 compliance questions
            asset = req_context["asset"]
            indicators = req_context["indicators"]
            
            question = {
                "id": f"compliance_{asset.id}_{uuid.uuid4()}",
                "question_type": "compliance_requirement",
                "priority": "high",
                "title": "Compliance Requirements",
                "question": f"What compliance requirements apply to '{asset.name}'?",
                "options": [
                    "PCI-DSS (Payment card data)",
                    "HIPAA (Health information)",
                    "SOX (Financial reporting)",
                    "GDPR (EU personal data)",
                    "None/Internal use only",
                    "Multiple (please specify in follow-up)"
                ],
                "context": {
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type,
                    "detected_patterns": indicators.get("reasoning", ""),
                    "ai_suggestions": [comp["type"] for comp in indicators["suggested_compliance"]],
                    "confidence": indicators["confidence"]
                }
            }
            
            questions.append(question)
        
        return questions
```

## Question Generation Framework

### **Question Priority System**

```python
class QuestionPriorityManager:
    """Manages question priority and batching for optimal user experience"""
    
    PRIORITY_WEIGHTS = {
        "critical": 1.0,    # Asset type unknown, blocks progression
        "high": 0.8,        # Business criticality, compliance requirements
        "medium": 0.6,      # Performance metrics, additional context
        "low": 0.4          # Nice-to-have information
    }
    
    def prioritize_questions(self, questions: List[dict]) -> List[dict]:
        """Sort questions by priority and impact"""
        
        def calculate_priority_score(question: dict) -> float:
            base_priority = self.PRIORITY_WEIGHTS[question["priority"]]
            
            # Boost score for questions that unblock flow progression
            if question.get("blocks_progression", False):
                base_priority += 0.2
            
            # Boost score for applications with high business value
            if question["context"].get("business_value_score", 0) >= 8:
                base_priority += 0.1
            
            # Boost score for assets with high AI confidence
            if question["context"].get("confidence", 0) >= 0.8:
                base_priority += 0.05
            
            return min(base_priority, 1.0)
        
        return sorted(questions, key=calculate_priority_score, reverse=True)
    
    def batch_questions_for_ui(self, questions: List[dict], max_batch_size: int = 7) -> List[List[dict]]:
        """Create batches of questions for optimal user experience"""
        prioritized = self.prioritize_questions(questions)
        
        batches = []
        current_batch = []
        
        for question in prioritized:
            current_batch.append(question)
            
            if len(current_batch) >= max_batch_size:
                batches.append(current_batch)
                current_batch = []
        
        if current_batch:  # Add remaining questions
            batches.append(current_batch)
        
        return batches
```

### **Confidence Score Calculation**

```python
class ConfidenceCalculator:
    """Calculates AI confidence scores for enrichment suggestions"""
    
    def calculate_suggestion_confidence(self, suggestion_data: dict) -> float:
        """Calculate overall confidence score for a suggestion"""
        
        confidence_factors = {
            "pattern_match": suggestion_data.get("pattern_confidence", 0.0),
            "data_completeness": suggestion_data.get("data_completeness", 0.0),
            "historical_accuracy": suggestion_data.get("historical_accuracy", 0.7),  # Default
            "domain_knowledge": suggestion_data.get("domain_knowledge", 0.6)
        }
        
        # Weighted average
        weights = {
            "pattern_match": 0.4,
            "data_completeness": 0.3,
            "historical_accuracy": 0.2,
            "domain_knowledge": 0.1
        }
        
        weighted_confidence = sum(
            confidence_factors[factor] * weights[factor] 
            for factor in weights
        )
        
        return round(weighted_confidence, 2)
```

## Learning and Feedback Integration

### **Agent Learning System**

```python
class AgentLearningSystem:
    """System for agents to learn from user corrections and feedback"""
    
    async def record_user_correction(self, question_id: str, user_response: dict, agent_suggestion: dict):
        """Record user correction for future learning"""
        
        correction_record = {
            "question_id": question_id,
            "agent_suggestion": agent_suggestion,
            "user_response": user_response,
            "correction_type": self._determine_correction_type(agent_suggestion, user_response),
            "pattern_context": self._extract_pattern_context(question_id),
            "timestamp": datetime.utcnow()
        }
        
        await self._store_learning_record(correction_record)
        await self._update_pattern_weights(correction_record)
    
    def _determine_correction_type(self, suggestion: dict, response: dict) -> str:
        """Determine the type of correction made by user"""
        
        if suggestion.get("ai_suggestion") != response.get("selected_option"):
            if suggestion.get("confidence", 0) > 0.8:
                return "high_confidence_override"  # User disagreed with high-confidence suggestion
            else:
                return "low_confidence_correction"  # Expected correction on uncertain suggestion
        else:
            return "confirmation"  # User agreed with AI suggestion
    
    async def _update_pattern_weights(self, correction_record: dict):
        """Update pattern recognition weights based on user feedback"""
        
        correction_type = correction_record["correction_type"]
        pattern_context = correction_record["pattern_context"]
        
        if correction_type == "high_confidence_override":
            # Reduce weight for patterns that led to wrong high-confidence suggestions
            await self._adjust_pattern_weights(pattern_context, adjustment=-0.1)
        elif correction_type == "confirmation":
            # Increase weight for patterns that led to correct suggestions
            await self._adjust_pattern_weights(pattern_context, adjustment=0.05)
```

---

*Next: [04_ui_components_design.md](04_ui_components_design.md)*