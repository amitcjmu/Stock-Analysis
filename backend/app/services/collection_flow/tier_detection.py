"""
Environment Tier Detection Service

This service analyzes customer environments to determine the appropriate
automation tier for data collection based on available platforms, tools,
and integration capabilities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import AutomationTier
from app.services.collection_flow.adapters import AdapterCapability, adapter_registry

logger = logging.getLogger(__name__)


class PlatformCategory(str, Enum):
    """Platform categories for tier detection"""
    CMDB = "cmdb"
    MONITORING = "monitoring"
    ORCHESTRATION = "orchestration"
    VIRTUALIZATION = "virtualization"
    CLOUD = "cloud"
    CONTAINER = "container"
    DATABASE = "database"
    MIDDLEWARE = "middleware"
    NETWORK = "network"
    SECURITY = "security"


@dataclass
class PlatformInfo:
    """Information about a detected platform"""
    name: str
    category: PlatformCategory
    version: Optional[str] = None
    api_available: bool = False
    script_support: bool = False
    export_capability: bool = False
    authentication_type: Optional[str] = None
    confidence_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TierAssessment:
    """Assessment result for tier detection"""
    recommended_tier: AutomationTier
    confidence_score: float
    platforms_detected: List[PlatformInfo]
    capabilities_available: List[AdapterCapability]
    limitations: List[str]
    recommendations: List[str]
    assessment_metadata: Dict[str, Any]


class TierDetectionService:
    """
    Service for detecting and recommending automation tiers based on
    customer environment analysis.
    """
    
    # Platform tier mappings
    TIER_4_PLATFORMS = {
        "servicenow": {"api": True, "categories": [PlatformCategory.CMDB, PlatformCategory.ORCHESTRATION]},
        "vmware_vcenter": {"api": True, "categories": [PlatformCategory.VIRTUALIZATION]},
        "aws": {"api": True, "categories": [PlatformCategory.CLOUD]},
        "azure": {"api": True, "categories": [PlatformCategory.CLOUD]},
        "gcp": {"api": True, "categories": [PlatformCategory.CLOUD]},
        "kubernetes": {"api": True, "categories": [PlatformCategory.CONTAINER]},
        "ansible_tower": {"api": True, "categories": [PlatformCategory.ORCHESTRATION]},
        "datadog": {"api": True, "categories": [PlatformCategory.MONITORING]},
        "splunk": {"api": True, "categories": [PlatformCategory.MONITORING, PlatformCategory.SECURITY]}
    }
    
    TIER_3_PLATFORMS = {
        "bmc_remedy": {"api": True, "categories": [PlatformCategory.CMDB]},
        "microsoft_sccm": {"api": True, "categories": [PlatformCategory.CMDB]},
        "nagios": {"api": False, "script": True, "categories": [PlatformCategory.MONITORING]},
        "zabbix": {"api": True, "categories": [PlatformCategory.MONITORING]},
        "puppet": {"api": True, "categories": [PlatformCategory.ORCHESTRATION]},
        "chef": {"api": True, "categories": [PlatformCategory.ORCHESTRATION]},
        "openshift": {"api": True, "categories": [PlatformCategory.CONTAINER]},
        "oracle_db": {"api": False, "script": True, "categories": [PlatformCategory.DATABASE]}
    }
    
    TIER_2_PLATFORMS = {
        "excel": {"script": True, "categories": [PlatformCategory.CMDB]},
        "csv_export": {"script": True, "categories": [PlatformCategory.CMDB]},
        "powershell": {"script": True, "categories": [PlatformCategory.ORCHESTRATION]},
        "bash_scripts": {"script": True, "categories": [PlatformCategory.ORCHESTRATION]},
        "sql_server": {"script": True, "categories": [PlatformCategory.DATABASE]},
        "mysql": {"script": True, "categories": [PlatformCategory.DATABASE]},
        "postgresql": {"script": True, "categories": [PlatformCategory.DATABASE]}
    }
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Tier Detection Service.
        
        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        
    async def detect_environment_tier(
        self,
        environment_info: Dict[str, Any],
        requested_capabilities: Optional[List[AdapterCapability]] = None
    ) -> TierAssessment:
        """
        Detect the appropriate automation tier for the environment.
        
        Args:
            environment_info: Information about the customer environment
            requested_capabilities: Optional list of required capabilities
            
        Returns:
            TierAssessment with recommendations
        """
        try:
            # Extract platform information
            platforms = await self._detect_platforms(environment_info)
            
            # Analyze capabilities
            capabilities = await self._analyze_capabilities(platforms, requested_capabilities)
            
            # Determine tier
            tier, confidence = self._determine_tier(platforms, capabilities)
            
            # Generate recommendations
            limitations = self._identify_limitations(platforms, tier)
            recommendations = self._generate_recommendations(platforms, tier, limitations)
            
            # Create assessment
            assessment = TierAssessment(
                recommended_tier=tier,
                confidence_score=confidence,
                platforms_detected=platforms,
                capabilities_available=capabilities,
                limitations=limitations,
                recommendations=recommendations,
                assessment_metadata={
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                    "environment_summary": self._create_environment_summary(platforms),
                    "tier_rationale": self._explain_tier_selection(tier, platforms, capabilities)
                }
            )
            
            logger.info(
                f"Environment tier detection completed: {tier.value} "
                f"(confidence: {confidence:.2f})"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to detect environment tier: {str(e)}")
            raise
    
    async def _detect_platforms(
        self,
        environment_info: Dict[str, Any]
    ) -> List[PlatformInfo]:
        """
        Detect platforms in the environment.
        
        Args:
            environment_info: Environment information
            
        Returns:
            List of detected platforms
        """
        detected_platforms = []
        
        # Check for explicitly declared platforms
        declared_platforms = environment_info.get("platforms", [])
        for platform_data in declared_platforms:
            platform_name = platform_data.get("name", "").lower()
            platform_info = await self._create_platform_info(platform_name, platform_data)
            if platform_info:
                detected_platforms.append(platform_info)
        
        # Check for platform indicators in various data sources
        if "inventory_sources" in environment_info:
            for source in environment_info["inventory_sources"]:
                platform_info = await self._detect_from_inventory_source(source)
                if platform_info and platform_info not in detected_platforms:
                    detected_platforms.append(platform_info)
        
        # Check for tool availability
        if "available_tools" in environment_info:
            for tool in environment_info["available_tools"]:
                platform_info = await self._detect_from_tool(tool)
                if platform_info and platform_info not in detected_platforms:
                    detected_platforms.append(platform_info)
        
        return detected_platforms
    
    async def _create_platform_info(
        self,
        platform_name: str,
        platform_data: Dict[str, Any]
    ) -> Optional[PlatformInfo]:
        """
        Create PlatformInfo from platform data.
        
        Args:
            platform_name: Platform name
            platform_data: Platform data
            
        Returns:
            PlatformInfo or None
        """
        # Check Tier 4 platforms
        if platform_name in self.TIER_4_PLATFORMS:
            platform_def = self.TIER_4_PLATFORMS[platform_name]
            return PlatformInfo(
                name=platform_name,
                category=platform_def["categories"][0],
                version=platform_data.get("version"),
                api_available=platform_def.get("api", False),
                script_support=platform_def.get("script", False),
                export_capability=platform_data.get("export_available", False),
                authentication_type=platform_data.get("auth_type"),
                confidence_score=0.9,
                metadata=platform_data
            )
        
        # Check Tier 3 platforms
        if platform_name in self.TIER_3_PLATFORMS:
            platform_def = self.TIER_3_PLATFORMS[platform_name]
            return PlatformInfo(
                name=platform_name,
                category=platform_def["categories"][0],
                version=platform_data.get("version"),
                api_available=platform_def.get("api", False),
                script_support=platform_def.get("script", False),
                export_capability=platform_data.get("export_available", False),
                authentication_type=platform_data.get("auth_type"),
                confidence_score=0.8,
                metadata=platform_data
            )
        
        # Check Tier 2 platforms
        if platform_name in self.TIER_2_PLATFORMS:
            platform_def = self.TIER_2_PLATFORMS[platform_name]
            return PlatformInfo(
                name=platform_name,
                category=platform_def["categories"][0],
                version=platform_data.get("version"),
                api_available=False,
                script_support=platform_def.get("script", False),
                export_capability=True,
                authentication_type=platform_data.get("auth_type"),
                confidence_score=0.7,
                metadata=platform_data
            )
        
        # Unknown platform - assume Tier 1
        return PlatformInfo(
            name=platform_name,
            category=PlatformCategory.CMDB,
            version=platform_data.get("version"),
            api_available=False,
            script_support=False,
            export_capability=platform_data.get("export_available", False),
            authentication_type=platform_data.get("auth_type"),
            confidence_score=0.5,
            metadata=platform_data
        )
    
    async def _detect_from_inventory_source(
        self,
        source: Dict[str, Any]
    ) -> Optional[PlatformInfo]:
        """Detect platform from inventory source information."""
        source_type = source.get("type", "").lower()
        
        # Map common source types to platforms
        source_platform_map = {
            "servicenow_cmdb": "servicenow",
            "vmware": "vmware_vcenter",
            "aws_config": "aws",
            "azure_resource_graph": "azure",
            "gcp_asset_inventory": "gcp",
            "remedy_itsm": "bmc_remedy",
            "sccm": "microsoft_sccm"
        }
        
        if source_type in source_platform_map:
            platform_name = source_platform_map[source_type]
            return await self._create_platform_info(platform_name, source)
        
        return None
    
    async def _detect_from_tool(
        self,
        tool: Dict[str, Any]
    ) -> Optional[PlatformInfo]:
        """Detect platform from available tool information."""
        tool_name = tool.get("name", "").lower()
        
        # Direct platform mapping
        if tool_name in self.TIER_4_PLATFORMS:
            return await self._create_platform_info(tool_name, tool)
        if tool_name in self.TIER_3_PLATFORMS:
            return await self._create_platform_info(tool_name, tool)
        if tool_name in self.TIER_2_PLATFORMS:
            return await self._create_platform_info(tool_name, tool)
        
        return None
    
    async def _analyze_capabilities(
        self,
        platforms: List[PlatformInfo],
        requested_capabilities: Optional[List[AdapterCapability]] = None
    ) -> List[AdapterCapability]:
        """
        Analyze available capabilities based on detected platforms.
        
        Args:
            platforms: Detected platforms
            requested_capabilities: Optional requested capabilities
            
        Returns:
            List of available capabilities
        """
        available_capabilities = set()
        
        # Map platforms to capabilities
        for platform in platforms:
            # Check registered adapters
            adapters = adapter_registry.get_adapters_by_platform(platform.name)
            for adapter_metadata in adapters:
                available_capabilities.update(adapter_metadata.capabilities)
            
            # Add implied capabilities based on platform features
            if platform.api_available:
                available_capabilities.add(AdapterCapability.SERVER_DISCOVERY)
                available_capabilities.add(AdapterCapability.APPLICATION_DISCOVERY)
                
                if platform.category == PlatformCategory.CMDB:
                    available_capabilities.add(AdapterCapability.DEPENDENCY_MAPPING)
                elif platform.category == PlatformCategory.MONITORING:
                    available_capabilities.add(AdapterCapability.PERFORMANCE_METRICS)
                    
            if platform.script_support:
                available_capabilities.add(AdapterCapability.CONFIGURATION_EXPORT)
                
            if platform.export_capability:
                available_capabilities.add(AdapterCapability.CONFIGURATION_EXPORT)
        
        # Filter by requested capabilities if specified
        if requested_capabilities:
            available_capabilities = available_capabilities.intersection(requested_capabilities)
        
        return list(available_capabilities)
    
    def _determine_tier(
        self,
        platforms: List[PlatformInfo],
        capabilities: List[AdapterCapability]
    ) -> Tuple[AutomationTier, float]:
        """
        Determine the appropriate tier based on platforms and capabilities.
        
        Args:
            platforms: Detected platforms
            capabilities: Available capabilities
            
        Returns:
            Tuple of (tier, confidence_score)
        """
        if not platforms:
            return AutomationTier.TIER_1, 0.5
        
        # Count platforms by tier
        tier_4_count = sum(1 for p in platforms if p.name in self.TIER_4_PLATFORMS)
        tier_3_count = sum(1 for p in platforms if p.name in self.TIER_3_PLATFORMS)
        tier_2_count = sum(1 for p in platforms if p.name in self.TIER_2_PLATFORMS)
        
        # Calculate API availability percentage
        api_platforms = sum(1 for p in platforms if p.api_available)
        api_percentage = api_platforms / len(platforms) if platforms else 0
        
        # Determine tier based on multiple factors
        if tier_4_count > 0 and api_percentage >= 0.7:
            # Strong Tier 4 - multiple modern platforms with APIs
            confidence = min(0.95, 0.7 + (tier_4_count * 0.1))
            return AutomationTier.TIER_4, confidence
            
        elif (tier_4_count > 0 or tier_3_count >= 2) and api_percentage >= 0.5:
            # Tier 3 - mix of modern and traditional platforms
            confidence = min(0.85, 0.6 + (api_percentage * 0.3))
            return AutomationTier.TIER_3, confidence
            
        elif tier_2_count > 0 or any(p.script_support for p in platforms):
            # Tier 2 - script-based collection available
            confidence = min(0.75, 0.5 + (tier_2_count * 0.1))
            return AutomationTier.TIER_2, confidence
            
        else:
            # Tier 1 - manual/template-based only
            confidence = 0.6
            return AutomationTier.TIER_1, confidence
    
    def _identify_limitations(
        self,
        platforms: List[PlatformInfo],
        tier: AutomationTier
    ) -> List[str]:
        """Identify limitations based on platforms and tier."""
        limitations = []
        
        # Check for missing critical platforms
        has_cmdb = any(p.category == PlatformCategory.CMDB for p in platforms)
        has_monitoring = any(p.category == PlatformCategory.MONITORING for p in platforms)
        
        if not has_cmdb:
            limitations.append("No CMDB platform detected - inventory data may be incomplete")
            
        if not has_monitoring:
            limitations.append("No monitoring platform detected - performance metrics unavailable")
        
        # Check for authentication limitations
        auth_issues = [p for p in platforms if not p.authentication_type]
        if auth_issues:
            limitations.append(
                f"Authentication not configured for {len(auth_issues)} platform(s)"
            )
        
        # Tier-specific limitations
        if tier == AutomationTier.TIER_1:
            limitations.append("Manual data collection required - increased time and effort")
            limitations.append("Limited validation capabilities")
            
        elif tier == AutomationTier.TIER_2:
            limitations.append("Script execution required - potential security constraints")
            limitations.append("Limited real-time data collection")
        
        return limitations
    
    def _generate_recommendations(
        self,
        platforms: List[PlatformInfo],
        tier: AutomationTier,
        limitations: List[str]
    ) -> List[str]:
        """Generate recommendations for improving data collection."""
        recommendations = []
        
        # Tier upgrade recommendations
        if tier == AutomationTier.TIER_1:
            recommendations.append(
                "Consider implementing ServiceNow or similar CMDB for automated collection"
            )
            recommendations.append(
                "Enable API access on existing platforms where available"
            )
            
        elif tier == AutomationTier.TIER_2:
            api_capable = [p for p in platforms if p.name in {**self.TIER_3_PLATFORMS, **self.TIER_4_PLATFORMS}]
            if api_capable:
                recommendations.append(
                    f"Enable API access for {api_capable[0].name} to upgrade to Tier 3"
                )
                
        elif tier == AutomationTier.TIER_3:
            if not any(p.name in self.TIER_4_PLATFORMS for p in platforms):
                recommendations.append(
                    "Consider adopting modern platforms (ServiceNow, cloud-native tools) for Tier 4"
                )
        
        # Platform-specific recommendations
        if not any(p.category == PlatformCategory.CMDB for p in platforms):
            recommendations.append("Implement a CMDB solution for centralized asset management")
            
        if not any(p.category == PlatformCategory.MONITORING for p in platforms):
            recommendations.append("Deploy monitoring tools for performance and dependency data")
        
        # Security recommendations
        insecure_platforms = [p for p in platforms if not p.authentication_type]
        if insecure_platforms:
            recommendations.append(
                "Configure secure authentication for all data collection platforms"
            )
        
        return recommendations
    
    def _create_environment_summary(self, platforms: List[PlatformInfo]) -> Dict[str, Any]:
        """Create a summary of the environment."""
        return {
            "total_platforms": len(platforms),
            "platforms_by_category": self._group_platforms_by_category(platforms),
            "api_enabled_count": sum(1 for p in platforms if p.api_available),
            "script_enabled_count": sum(1 for p in platforms if p.script_support),
            "average_confidence": sum(p.confidence_score for p in platforms) / len(platforms) if platforms else 0
        }
    
    def _group_platforms_by_category(
        self,
        platforms: List[PlatformInfo]
    ) -> Dict[str, List[str]]:
        """Group platforms by category."""
        grouped = {}
        for platform in platforms:
            category = platform.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(platform.name)
        return grouped
    
    def _explain_tier_selection(
        self,
        tier: AutomationTier,
        platforms: List[PlatformInfo],
        capabilities: List[AdapterCapability]
    ) -> str:
        """Explain why a specific tier was selected."""
        explanations = {
            AutomationTier.TIER_4: (
                f"Tier 4 selected due to {sum(1 for p in platforms if p.api_available)} "
                f"API-enabled platforms and {len(capabilities)} automated capabilities"
            ),
            AutomationTier.TIER_3: (
                f"Tier 3 selected with mix of API and script-based platforms. "
                f"{len([p for p in platforms if p.api_available])} platforms support API integration"
            ),
            AutomationTier.TIER_2: (
                f"Tier 2 selected for script-assisted collection. "
                f"{len([p for p in platforms if p.script_support])} platforms support scripting"
            ),
            AutomationTier.TIER_1: (
                "Tier 1 selected due to limited automation capabilities. "
                "Manual or template-based collection required"
            )
        }
        
        return explanations.get(tier, "Tier selection based on available platforms and capabilities")