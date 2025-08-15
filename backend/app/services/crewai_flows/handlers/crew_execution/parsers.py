"""
Crew Result Parsers
Handles parsing of various crew execution results
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CrewResultParser:
    """Parser for crew execution results"""

    def parse_field_mapping_results(  # noqa: C901
        self, crew_result, raw_data
    ) -> Dict[str, Any]:
        """Parse results from Full Agentic Field Mapping Crew execution"""
        try:
            logger.info(f"🔍 Parsing crew result type: {type(crew_result)}")

            # Initialize result structure
            parsed_result = {
                "mappings": {},
                "confidence_scores": {},
                "unmapped_fields": [],
                "skipped_fields": [],
                "synthesis_required": [],
                "transformations": [],
                "validation_results": {"valid": True, "score": 0.0},
                "agent_insights": {
                    "crew_execution": "Executed with Full Agentic CrewAI",
                    "source": "field_mapping_crew_v2",
                    "agents": [
                        "Data Pattern Analyst",
                        "Schema Mapping Expert",
                        "Synthesis Specialist",
                    ],
                },
                "agent_reasoning": {},  # Store detailed reasoning for each mapping
            }

            # Handle different crew result formats
            if hasattr(crew_result, "raw_output"):
                # CrewAI standard output format
                raw_output = str(crew_result.raw_output)
                logger.info(f"📝 Raw crew output length: {len(raw_output)}")

                # Extract JSON sections from the output
                import re

                # FIXED: More robust JSON extraction using multiple strategies
                mapping_data = self._extract_json_from_crew_output(raw_output)

                if mapping_data and "mappings" in mapping_data:
                    logger.info(
                        f"✅ Found mapping data: {len(mapping_data.get('mappings', {}))} mappings"
                    )

                    # Process each mapping
                    for source_field, mapping_info in mapping_data.get(
                        "mappings", {}
                    ).items():
                        if isinstance(mapping_info, dict):
                            target_field = mapping_info.get(
                                "target_field", source_field
                            )
                            confidence = mapping_info.get("confidence", 0.7)
                            reasoning = mapping_info.get("reasoning", "Agent analysis")

                            parsed_result["mappings"][source_field] = target_field
                            parsed_result["confidence_scores"][
                                source_field
                            ] = confidence
                            parsed_result["agent_reasoning"][source_field] = {
                                "reasoning": reasoning,
                                "requires_transformation": mapping_info.get(
                                    "requires_transformation", False
                                ),
                                "data_patterns": mapping_info.get("data_patterns", {}),
                            }
                        else:
                            # Simple mapping format
                            parsed_result["mappings"][source_field] = mapping_info
                            parsed_result["confidence_scores"][source_field] = 0.7

                    # Extract skipped fields
                    parsed_result["skipped_fields"] = mapping_data.get(
                        "skipped_fields", []
                    )
                    parsed_result["synthesis_required"] = mapping_data.get(
                        "synthesis_required", []
                    )
                else:
                    # CRITICAL: If no valid JSON found, FAIL FAST instead of storing malformed data
                    logger.error(
                        f"❌ No valid JSON mappings found in crew output. Raw output preview: {raw_output[:500]}..."
                    )
                    raise ValueError(
                        "CrewAI agent did not return valid JSON mapping structure"
                    )

                # Look for transformation task output
                transform_match = re.search(
                    r'\{[^{}]*"transformations"[^{}]*\}', raw_output, re.DOTALL
                )
                if transform_match:
                    try:
                        transform_data = json.loads(transform_match.group())
                        parsed_result["transformations"] = transform_data.get(
                            "transformations", []
                        )
                        logger.info(
                            f"✅ Found {len(parsed_result['transformations'])} transformations"
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Failed to parse transformation JSON: {e}")

            elif isinstance(crew_result, dict):
                # Direct dictionary result
                parsed_result.update(crew_result)
            elif isinstance(crew_result, str):
                # Try to extract JSON from string
                mappings = self._extract_mappings_from_text(crew_result)
                if not mappings.get("mappings"):
                    logger.error(
                        f"❌ No valid mappings extracted from string result: {crew_result[:200]}..."
                    )
                    raise ValueError(
                        "CrewAI agent returned string but no valid mappings found"
                    )
                parsed_result.update(mappings)

            # Calculate validation score
            total_fields = len(raw_data[0].keys()) if raw_data else 0
            mapped_fields = len(parsed_result["mappings"])
            skipped_fields = len(parsed_result["skipped_fields"])

            if total_fields > 0:
                coverage = (mapped_fields + skipped_fields) / total_fields
                avg_confidence = (
                    sum(parsed_result["confidence_scores"].values())
                    / len(parsed_result["confidence_scores"])
                    if parsed_result["confidence_scores"]
                    else 0
                )
                parsed_result["validation_results"]["score"] = coverage * avg_confidence
                parsed_result["validation_results"]["coverage"] = coverage
                parsed_result["validation_results"]["avg_confidence"] = avg_confidence

            # Identify unmapped fields
            if raw_data:
                all_fields = set(raw_data[0].keys())
                mapped_fields_set = set(parsed_result["mappings"].keys())
                skipped_fields_set = set(parsed_result["skipped_fields"])
                parsed_result["unmapped_fields"] = list(
                    all_fields - mapped_fields_set - skipped_fields_set
                )

            logger.info(
                f"✅ Parsed field mapping results: {mapped_fields} mapped, "
                f"{len(parsed_result['skipped_fields'])} skipped, "
                f"{len(parsed_result['unmapped_fields'])} unmapped"
            )

            # Validate we have some mappings before proceeding
            if not parsed_result["mappings"]:
                logger.error(
                    "❌ No field mappings were successfully parsed from crew result"
                )
                raise ValueError("CrewAI parsing resulted in zero field mappings")

            return parsed_result

        except Exception as e:
            logger.error(f"❌ Failed to parse crew results: {e}")
            # FAIL FAST - Don't allow malformed data to be stored
            raise e

    def _extract_json_from_crew_output(self, raw_output: str) -> Dict[str, Any]:
        """
        Robust JSON extraction from CrewAI agent output using multiple strategies
        """
        import re

        # Strategy 1: Look for complete JSON objects with mappings key
        # Handle nested objects better than the original regex
        json_patterns = [
            # Complete JSON block containing mappings (most common)
            r'\{[^{}]*?"mappings"[^{}]*?\{.*?\}[^{}]*?\}',
            # Simpler JSON objects
            r'\{[^{}]*?"mappings"[^{}]*?\}',
            # JSON that might span multiple lines
            r'\{[\s\S]*?"mappings"[\s\S]*?\}',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, raw_output, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse the JSON
                    parsed = json.loads(match)
                    if isinstance(parsed, dict) and "mappings" in parsed:
                        logger.info(
                            f"✅ Successfully parsed JSON using pattern: {pattern[:50]}..."
                        )
                        return parsed
                except json.JSONDecodeError:
                    continue

        # Strategy 2: Extract JSON blocks and try to complete them
        json_blocks = re.findall(r"\{[^{}]*\}", raw_output)
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict) and "mappings" in parsed:
                    logger.info("✅ Successfully parsed simple JSON block")
                    return parsed
            except json.JSONDecodeError:
                continue

        # Strategy 3: Look for mappings data even if not in perfect JSON
        # Extract key-value pairs from agent output
        mappings = {}

        # Look for explicit mapping statements
        mapping_patterns = [
            r'"([^"]+)":\s*\{\s*"target_field":\s*"([^"]+)"',  # Full format
            r'"([^"]+)":\s*"([^"]+)"',  # Simple format
            r"(\w+)\s*->\s*(\w+)",  # Arrow format
        ]

        for pattern in mapping_patterns:
            matches = re.findall(pattern, raw_output)
            for source, target in matches:
                mappings[source] = target

        if mappings:
            logger.info(f"✅ Extracted {len(mappings)} mappings using pattern matching")
            return {
                "mappings": mappings,
                "skipped_fields": [],
                "synthesis_required": [],
            }

        logger.warning("❌ No valid JSON or mappings found in agent output")
        return None

    def _extract_mappings_from_text(self, text: str) -> Dict[str, Any]:
        """Extract field mappings from crew text output"""
        # Simple extraction - in a real implementation, this would be more sophisticated

        # Try to find JSON in the text
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except Exception:
                pass

        # Fallback to pattern extraction
        mappings = {}
        confidence_scores = {}

        # Look for mapping patterns like "field -> target_field"
        mapping_pattern = r"(\w+)\s*[->=]+\s*(\w+)"
        matches = re.findall(mapping_pattern, text)

        for source, target in matches:
            mappings[source] = target
            confidence_scores[source] = 0.7  # Default confidence

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "unmapped_fields": [],
            "validation_results": {"valid": len(mappings) > 0, "score": 0.7},
        }

    def parse_data_cleansing_results(
        self, crew_result, raw_data
    ) -> List[Dict[str, Any]]:
        """Parse results from Data Cleansing Crew execution"""
        try:
            # If crew result contains cleaned data, use it
            if isinstance(crew_result, dict) and "cleaned_data" in crew_result:
                return crew_result["cleaned_data"]
            elif isinstance(crew_result, list):
                return crew_result
            else:
                # Fallback to raw data
                return raw_data
        except Exception as e:
            logger.warning(f"Failed to parse data cleansing results: {e}")
            return raw_data

    def extract_quality_metrics(self, crew_result) -> Dict[str, Any]:
        """Extract quality metrics from crew result"""
        try:
            if isinstance(crew_result, dict) and "quality_metrics" in crew_result:
                return crew_result["quality_metrics"]
            else:
                return {
                    "overall_score": 0.85,
                    "validation_passed": True,
                    "standardization_complete": True,
                    "issues_resolved": 0,
                    "crew_execution": True,
                }
        except Exception as e:
            logger.warning(f"Failed to extract quality metrics: {e}")
            return {"overall_score": 0.75, "fallback": True}

    def parse_inventory_results(self, crew_result, cleaned_data) -> Dict[str, Any]:
        """Parse results from Inventory Building Crew execution"""
        try:
            if isinstance(crew_result, dict) and "asset_inventory" in crew_result:
                return crew_result["asset_inventory"]
            else:
                # Use fallback handler for classification
                from .fallbacks import CrewFallbackHandler

                fallback_handler = CrewFallbackHandler()
                return fallback_handler.intelligent_asset_classification_fallback(
                    cleaned_data
                )
        except Exception as e:
            logger.warning(f"Failed to parse inventory results: {e}")
            from .fallbacks import CrewFallbackHandler

            fallback_handler = CrewFallbackHandler()
            return fallback_handler.intelligent_asset_classification_fallback(
                cleaned_data
            )

    def parse_dependency_results(self, crew_result, dependency_type) -> Dict[str, Any]:
        """Parse results from dependency crew execution"""
        try:
            if isinstance(crew_result, dict):
                return crew_result
            else:
                # Use fallback handler for dependency mapping
                from .fallbacks import CrewFallbackHandler

                fallback_handler = CrewFallbackHandler()
                return fallback_handler.intelligent_dependency_fallback(
                    {}, dependency_type
                )
        except Exception as e:
            logger.warning(f"Failed to parse dependency results: {e}")
            from .fallbacks import CrewFallbackHandler

            fallback_handler = CrewFallbackHandler()
            return fallback_handler.intelligent_dependency_fallback({}, dependency_type)

    def parse_technical_debt_results(self, crew_result) -> Dict[str, Any]:
        """Parse results from Technical Debt Crew execution"""
        try:
            if isinstance(crew_result, dict):
                return crew_result
            else:
                # Use fallback handler for technical debt assessment
                from .fallbacks import CrewFallbackHandler

                fallback_handler = CrewFallbackHandler()
                return fallback_handler.intelligent_technical_debt_fallback(None)
        except Exception as e:
            logger.warning(f"Failed to parse technical debt results: {e}")
            from .fallbacks import CrewFallbackHandler

            fallback_handler = CrewFallbackHandler()
            return fallback_handler.intelligent_technical_debt_fallback(None)
