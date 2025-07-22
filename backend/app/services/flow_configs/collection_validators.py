"""
Collection Flow Validators
ADCS: Validators for all Collection flow phases

Provides validation functions for platform detection, automated collection,
gap analysis, manual collection, and synthesis phases.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Platform Detection Validators
async def platform_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate platform detection inputs and configuration"""
    try:
        # Check required fields
        if not phase_input.get("environment_config"):
            return False, "Missing environment_config"
        
        if not phase_input.get("automation_tier"):
            return False, "Missing automation_tier"
        
        # Validate automation tier
        valid_tiers = ["tier_1", "tier_2", "tier_3", "tier_4"]
        if phase_input["automation_tier"] not in valid_tiers:
            return False, f"Invalid automation_tier. Must be one of: {valid_tiers}"
        
        # Validate environment config structure
        env_config = phase_input["environment_config"]
        required_env_fields = ["platforms", "regions"]
        
        for field in required_env_fields:
            if field not in env_config:
                return False, f"Missing required field in environment_config: {field}"
        
        # Validate platforms list
        if not isinstance(env_config["platforms"], list) or len(env_config["platforms"]) == 0:
            return False, "environment_config.platforms must be a non-empty list"
        
        logger.info(f"✅ Platform validation passed for {len(env_config['platforms'])} platforms")
        return True, None
        
    except Exception as e:
        logger.error(f"Platform validation error: {e}")
        return False, f"Platform validation failed: {str(e)}"


async def credential_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate credentials for platform access"""
    try:
        credentials = phase_input.get("credentials", {})
        env_config = phase_input.get("environment_config", {})
        platforms = env_config.get("platforms", [])
        
        # For each platform, check if credentials are provided (if required)
        missing_creds = []
        for platform in platforms:
            platform_type = platform.get("type", "unknown")
            
            # Skip validation for platforms that don't require credentials
            if platform_type in ["local", "manual", "documentation"]:
                continue
            
            platform_id = platform.get("id", platform_type)
            if platform_id not in credentials:
                # Check automation tier - higher tiers may proceed without all credentials
                if phase_input.get("automation_tier") in ["tier_3", "tier_4"]:
                    logger.warning(f"Missing credentials for {platform_id}, will use manual collection")
                else:
                    missing_creds.append(platform_id)
        
        if missing_creds:
            return False, f"Missing credentials for platforms: {missing_creds}"
        
        # Validate credential structure
        for platform_id, cred in credentials.items():
            if not isinstance(cred, dict):
                return False, f"Invalid credential structure for {platform_id}"
            
            # Basic validation - ensure it has some auth info
            if not any(key in cred for key in ["api_key", "username", "token", "service_account"]):
                return False, f"No authentication information found for {platform_id}"
        
        logger.info(f"✅ Credential validation passed for {len(credentials)} platforms")
        return True, None
        
    except Exception as e:
        logger.error(f"Credential validation error: {e}")
        return False, f"Credential validation failed: {str(e)}"


# Automated Collection Validators
async def collection_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate automated collection inputs and results"""
    try:
        # Check for detected platforms from previous phase
        if "detected_platforms" not in state:
            return False, "No detected platforms found in state"
        
        detected_platforms = state["detected_platforms"]
        if not isinstance(detected_platforms, list) or len(detected_platforms) == 0:
            return False, "No platforms detected for collection"
        
        # Validate adapter configurations
        adapter_configs = phase_input.get("adapter_configs", {})
        
        # Check if we have adapter config for each platform
        platforms_without_adapters = []
        for platform in detected_platforms:
            platform_id = platform.get("id", platform.get("type"))
            if platform_id not in adapter_configs:
                # Check if platform supports manual collection only
                if platform.get("collection_method") != "manual_only":
                    platforms_without_adapters.append(platform_id)
        
        if platforms_without_adapters:
            # Allow proceeding with warning for higher tiers
            if state.get("automation_tier") in ["tier_3", "tier_4"]:
                logger.warning(f"No adapters for platforms: {platforms_without_adapters}")
            else:
                return False, f"Missing adapter configurations for: {platforms_without_adapters}"
        
        logger.info(f"✅ Collection validation passed for {len(detected_platforms)} platforms")
        return True, None
        
    except Exception as e:
        logger.error(f"Collection validation error: {e}")
        return False, f"Collection validation failed: {str(e)}"


async def data_quality_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate quality of collected data"""
    try:
        # This validator runs after collection, so check crew results
        crew_results = state.get("crew_results", {})
        collected_data = crew_results.get("collected_data", {})
        quality_scores = crew_results.get("quality_scores", {})
        
        if not collected_data:
            return False, "No data collected"
        
        # Get quality threshold based on automation tier
        automation_tier = state.get("automation_tier", "tier_2")
        quality_thresholds = {
            "tier_1": 0.95,
            "tier_2": 0.85,
            "tier_3": 0.75,
            "tier_4": 0.60
        }
        min_quality = quality_thresholds.get(automation_tier, 0.8)
        
        # Check quality scores
        low_quality_platforms = []
        for platform_id, score in quality_scores.items():
            if score < min_quality:
                low_quality_platforms.append(f"{platform_id} (score: {score})")
        
        if low_quality_platforms:
            # For lower tiers, this is a warning not a failure
            if automation_tier in ["tier_3", "tier_4"]:
                logger.warning(f"Low quality data for: {low_quality_platforms}")
            else:
                return False, f"Data quality below threshold for: {low_quality_platforms}"
        
        # Validate data structure
        for platform_id, data in collected_data.items():
            if not isinstance(data, dict):
                return False, f"Invalid data structure for {platform_id}"
            
            # Check for minimum required fields based on platform type
            if "resources" not in data and "assets" not in data:
                return False, f"No resources or assets found for {platform_id}"
        
        logger.info(f"✅ Data quality validation passed with average score: {sum(quality_scores.values())/len(quality_scores):.2f}")
        return True, None
        
    except Exception as e:
        logger.error(f"Data quality validation error: {e}")
        return False, f"Data quality validation failed: {str(e)}"


# Gap Analysis Validators
async def gap_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate gap analysis inputs"""
    try:
        # Check for collected data
        if "collected_data" not in state:
            return False, "No collected data found for gap analysis"
        
        # Check for 6R requirements
        sixr_requirements = phase_input.get("sixr_requirements")
        if not sixr_requirements:
            return False, "Missing sixr_requirements for gap analysis"
        
        # Validate 6R requirements structure
        required_sixr_fields = ["mandatory_fields", "recommended_fields", "sixr_mappings"]
        for field in required_sixr_fields:
            if field not in sixr_requirements:
                return False, f"Missing required field in sixr_requirements: {field}"
        
        logger.info("✅ Gap validation passed")
        return True, None
        
    except Exception as e:
        logger.error(f"Gap validation error: {e}")
        return False, f"Gap validation failed: {str(e)}"


async def sixr_impact_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate 6R impact analysis results"""
    try:
        # This runs after gap analysis
        crew_results = state.get("crew_results", {})
        sixr_impact = crew_results.get("sixr_impact_analysis", {})
        
        if not sixr_impact:
            return False, "No 6R impact analysis found"
        
        # Validate impact structure
        required_impact_fields = ["rehost", "refactor", "replatform", "repurchase", "retire", "retain"]
        
        for strategy in required_impact_fields:
            if strategy not in sixr_impact:
                return False, f"Missing 6R strategy analysis: {strategy}"
            
            # Each strategy should have impact score and gap count
            strategy_data = sixr_impact[strategy]
            if not isinstance(strategy_data, dict):
                return False, f"Invalid structure for {strategy} impact analysis"
            
            if "impact_score" not in strategy_data or "gap_count" not in strategy_data:
                return False, f"Missing impact_score or gap_count for {strategy}"
        
        logger.info("✅ 6R impact validation passed")
        return True, None
        
    except Exception as e:
        logger.error(f"6R impact validation error: {e}")
        return False, f"6R impact validation failed: {str(e)}"


# Manual Collection Validators
async def response_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate questionnaire responses"""
    try:
        # Check for identified gaps
        if "identified_gaps" not in state:
            # No gaps means no manual collection needed
            logger.info("No gaps identified, skipping manual collection")
            return True, None
        
        # This runs after manual collection
        crew_results = state.get("crew_results", {})
        responses = crew_results.get("responses", {})
        validation_results = crew_results.get("validation", {})
        
        if not responses and state.get("identified_gaps"):
            return False, "No responses collected for identified gaps"
        
        # Validate response structure
        invalid_responses = []
        for gap_id, response in responses.items():
            if not isinstance(response, dict):
                invalid_responses.append(gap_id)
                continue
            
            # Check required response fields
            if "value" not in response or "confidence" not in response:
                invalid_responses.append(gap_id)
        
        if invalid_responses:
            return False, f"Invalid response structure for gaps: {invalid_responses}"
        
        # Check validation results
        failed_validations = []
        for gap_id, validation in validation_results.items():
            if not validation.get("is_valid", False):
                failed_validations.append(f"{gap_id}: {validation.get('reason', 'unknown')}")
        
        if failed_validations:
            return False, f"Response validation failed: {failed_validations}"
        
        logger.info(f"✅ Response validation passed for {len(responses)} responses")
        return True, None
        
    except Exception as e:
        logger.error(f"Response validation error: {e}")
        return False, f"Response validation failed: {str(e)}"


async def completeness_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate completeness of manual collection"""
    try:
        # Check response rate
        identified_gaps = state.get("identified_gaps", [])
        crew_results = state.get("crew_results", {})
        responses = crew_results.get("responses", {})
        
        if not identified_gaps:
            return True, None
        
        response_rate = len(responses) / len(identified_gaps) if identified_gaps else 1.0
        
        # Get minimum response rate based on tier
        automation_tier = state.get("automation_tier", "tier_2")
        min_response_rates = {
            "tier_1": 0.95,
            "tier_2": 0.85,
            "tier_3": 0.75,
            "tier_4": 0.60
        }
        min_rate = min_response_rates.get(automation_tier, 0.8)
        
        if response_rate < min_rate:
            return False, f"Response rate {response_rate:.2%} below minimum {min_rate:.2%}"
        
        # Check critical gaps are addressed
        critical_gaps = [g for g in identified_gaps if g.get("priority", 0) >= 8]
        critical_responses = [g for g in critical_gaps if g.get("id") in responses]
        
        if len(critical_responses) < len(critical_gaps):
            missing_critical = len(critical_gaps) - len(critical_responses)
            return False, f"{missing_critical} critical gaps remain unaddressed"
        
        logger.info(f"✅ Completeness validation passed with {response_rate:.2%} response rate")
        return True, None
        
    except Exception as e:
        logger.error(f"Completeness validation error: {e}")
        return False, f"Completeness validation failed: {str(e)}"


# Synthesis Validators
async def final_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Final validation of synthesized data"""
    try:
        # Check all data sources are present
        if "automated_collection_data" not in state:
            return False, "Missing automated collection data"
        
        # Manual collection data is optional (no gaps scenario)
        
        # Validate synthesis results
        crew_results = state.get("crew_results", {})
        final_data = crew_results.get("final_data", {})
        quality_report = crew_results.get("quality_report", {})
        
        if not final_data:
            return False, "No synthesized data produced"
        
        if not quality_report:
            return False, "No quality report generated"
        
        # Check data completeness
        completeness = quality_report.get("completeness", 0)
        min_completeness = 0.85  # Default threshold
        
        if completeness < min_completeness:
            return False, f"Data completeness {completeness:.2%} below threshold {min_completeness:.2%}"
        
        # Validate final data structure
        for platform_id, platform_data in final_data.items():
            if not isinstance(platform_data, dict):
                return False, f"Invalid data structure for platform {platform_id}"
            
            # Check for synthesized fields
            if "metadata" not in platform_data or "resources" not in platform_data:
                return False, f"Missing required fields in synthesized data for {platform_id}"
        
        logger.info(f"✅ Final validation passed with {completeness:.2%} completeness")
        return True, None
        
    except Exception as e:
        logger.error(f"Final validation error: {e}")
        return False, f"Final validation failed: {str(e)}"


async def sixr_readiness_validation(state: Dict[str, Any], phase_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate 6R readiness of collected data"""
    try:
        crew_results = state.get("crew_results", {})
        sixr_readiness = crew_results.get("sixr_readiness_score", 0)
        quality_report = crew_results.get("quality_report", {})
        
        # Get minimum readiness based on tier
        automation_tier = state.get("automation_tier", "tier_2")
        min_readiness_scores = {
            "tier_1": 0.90,
            "tier_2": 0.80,
            "tier_3": 0.70,
            "tier_4": 0.60
        }
        min_readiness = min_readiness_scores.get(automation_tier, 0.75)
        
        if sixr_readiness < min_readiness:
            return False, f"6R readiness score {sixr_readiness:.2f} below threshold {min_readiness:.2f}"
        
        # Check strategy-specific readiness
        strategy_readiness = quality_report.get("strategy_readiness", {})
        low_readiness_strategies = []
        
        for strategy, score in strategy_readiness.items():
            if score < 0.6:  # Minimum per-strategy threshold
                low_readiness_strategies.append(f"{strategy}: {score:.2f}")
        
        if low_readiness_strategies:
            logger.warning(f"Low readiness for strategies: {low_readiness_strategies}")
            # Don't fail for tier 3/4
            if automation_tier not in ["tier_3", "tier_4"]:
                return False, f"Insufficient readiness for: {low_readiness_strategies}"
        
        logger.info(f"✅ 6R readiness validation passed with score {sixr_readiness:.2f}")
        return True, None
        
    except Exception as e:
        logger.error(f"6R readiness validation error: {e}")
        return False, f"6R readiness validation failed: {str(e)}"


# Export all validators
__all__ = [
    # Platform Detection
    "platform_validation",
    "credential_validation",
    
    # Automated Collection
    "collection_validation", 
    "data_quality_validation",
    
    # Gap Analysis
    "gap_validation",
    "sixr_impact_validation",
    
    # Manual Collection
    "response_validation",
    "completeness_validation",
    
    # Synthesis
    "final_validation",
    "sixr_readiness_validation"
]