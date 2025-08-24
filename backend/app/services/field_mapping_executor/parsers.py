"""
Field Mapping Parsers
Parsing logic for extracting field mappings and confidence scores from various input formats.
"""

import json
import re
import logging
from typing import Dict, List, Tuple, Optional, Any

from .exceptions import MappingParseError

logger = logging.getLogger(__name__)


class MappingParser:
    """Base class for mapping parsers"""

    def parse(self, text: str) -> Tuple[Dict[str, str], Dict[str, float]]:
        """
        Parse text to extract mappings and confidence scores

        Returns:
            Tuple of (mappings, confidence_scores)
        """
        raise NotImplementedError


# Alias for backward compatibility
BaseMappingParser = MappingParser


class JSONMappingParser(MappingParser):
    """Parser for JSON-formatted mapping results"""

    def parse(self, text: str) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Parse JSON formatted mapping results"""
        try:
            json_data = json.loads(text)
            logger.info("✅ Successfully parsed crew output as JSON")

            mappings = {}
            confidence_scores = {}

            # Extract mappings from JSON structure
            if "mappings" in json_data and isinstance(json_data["mappings"], dict):
                for source_field, mapping_info in json_data["mappings"].items():
                    if isinstance(mapping_info, dict):
                        target_field = mapping_info.get("target_field", "")
                        confidence = mapping_info.get("confidence", 0.7)
                        if target_field:
                            mappings[source_field] = target_field
                            confidence_scores[source_field] = confidence
                            logger.info(
                                f"✅ JSON mapping: {source_field} -> {target_field} (confidence: {confidence})"
                            )
                    elif isinstance(mapping_info, str):
                        # Simple string mapping
                        mappings[source_field] = mapping_info
                        confidence_scores[source_field] = 0.7
                        logger.info(
                            f"✅ JSON mapping: {source_field} -> {mapping_info}"
                        )

            return mappings, confidence_scores

        except json.JSONDecodeError as e:
            raise MappingParseError(f"JSON parsing failed: {e}", raw_text=text)


class PatternMappingParser(MappingParser):
    """Parser for pattern-based mapping results (arrows, colons, etc.)"""

    def __init__(self):
        self.confidence_patterns = [
            r"Confidence score:\s*(\d+)",
            r"Confidence:\s*(\d+)%?",
            r"confidence score:\s*(\d+)",
            r"Overall confidence:\s*(\d+)",
        ]

    def parse(self, text: str) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Parse pattern-based mapping results"""
        mappings = {}
        confidence_scores = {}
        overall_confidence = self._extract_overall_confidence(text)

        lines = text.split("\n")
        for line in lines:
            # Try different mapping formats
            mapping = self._parse_arrow_format(line)
            if not mapping:
                mapping = self._parse_colon_format(line)

            if mapping:
                source, target, confidence = mapping
                mappings[source] = target
                confidence_scores[source] = confidence or overall_confidence or 0.7
                logger.info(f"✅ Found mapping: {source} -> {target}")

        return mappings, confidence_scores

    def _extract_overall_confidence(self, text: str) -> Optional[float]:
        """Extract overall confidence score from text"""
        for pattern in self.confidence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                confidence = float(match.group(1))
                confidence = confidence / 100.0 if confidence > 1 else confidence
                logger.info(f"✅ Found overall confidence score: {confidence}")
                return confidence
        return None

    def _parse_arrow_format(
        self, line: str
    ) -> Optional[Tuple[str, str, Optional[float]]]:
        """Parse arrow format: source_field -> target_attribute"""
        if "->" not in line:
            return None

        parts = line.split("->")
        if len(parts) != 2:
            return None

        source = parts[0].strip().strip("\"'").strip(":").strip()
        target = parts[1].strip().strip("\"'").strip()

        # Skip numbered list items
        if re.match(r"^\d+\.\s*", source):
            source = re.sub(r"^\d+\.\s*", "", source).strip()

        # Extract confidence if present
        confidence = self._extract_line_confidence(line)

        if source and target:
            return source, target, confidence

        return None

    def _parse_colon_format(
        self, line: str
    ) -> Optional[Tuple[str, str, Optional[float]]]:
        """Parse colon format: source_field: target_attribute"""
        if ":" not in line:
            return None

        # Skip lines with keywords that aren't mappings
        skip_keywords = ["confidence", "status", "clarification", "question"]
        if any(keyword in line.lower() for keyword in skip_keywords):
            return None

        parts = line.split(":", 1)
        if len(parts) != 2:
            return None

        source = parts[0].strip().strip("\"'").strip()
        target = parts[1].strip().strip("\"'").strip()

        # Skip numbered list items
        if re.match(r"^\d+\.\s*", source):
            source = re.sub(r"^\d+\.\s*", "", source).strip()

        # Skip if it looks like a sentence or instruction
        if source and target and " " not in source.strip() and len(source) < 50:
            confidence = self._extract_line_confidence(line)
            return source, target, confidence

        return None

    def _extract_line_confidence(self, line: str) -> Optional[float]:
        """Extract confidence score from a single line"""
        conf_match = re.search(r"\((\d+)%?\)", line)
        if conf_match:
            confidence = float(conf_match.group(1))
            return confidence / 100.0 if confidence > 1 else confidence
        return None


class FallbackMappingParser(MappingParser):
    """Fallback parser for extracting mappings from malformed text"""

    def parse(self, text: str) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Parse using fallback methods"""
        mappings = {}
        confidence_scores = {}

        # Try to extract any JSON-like structures from the text
        mappings_from_json = self._extract_malformed_json(text)
        if mappings_from_json:
            mappings.update(mappings_from_json)
            for key in mappings_from_json:
                confidence_scores[key] = 0.7

        # Try flexible field name matching
        if not mappings:
            mappings_from_flexible = self._flexible_field_matching(text)
            mappings.update(mappings_from_flexible)
            for key in mappings_from_flexible:
                confidence_scores[key] = 0.6  # Lower confidence for flexible matching

        return mappings, confidence_scores

    def _extract_malformed_json(self, text: str) -> Dict[str, str]:
        """Extract mappings from malformed JSON-like text"""
        mappings = {}

        try:
            # Pattern to find field mappings like "field_name": "target_value"
            pattern = r'"([^"]+)"\s*:\s*"([^"]+)"'
            matches = re.findall(pattern, text)
            if matches:
                logger.info(f"✅ Extracted {len(matches)} mappings from malformed JSON")
                for source_field, target_field in matches:
                    # Skip malformed values
                    if target_field not in ["{", "}", "[", "]", "", "null"]:
                        mappings[source_field] = target_field
        except Exception as ex:
            logger.warning(f"Failed to extract from malformed JSON: {ex}")

        return mappings

    def _flexible_field_matching(self, text: str) -> Dict[str, str]:
        """Flexible field name matching using common patterns"""
        mappings = {}

        common_mappings = {
            "hostname": "hostname",
            "ip address": "ip_address",
            "operating system": "operating_system",
            "cpu cores": "cpu_cores",
            "ram": "memory_gb",
            "environment": "environment",
            "status": "status",
        }

        text_lower = text.lower()
        lines = text.split("\n")

        for source, target in common_mappings.items():
            if source in text_lower:
                # Try to find the actual field name in the original text
                for line in lines:
                    if source in line.lower():
                        # Extract the actual field name
                        field_match = re.search(r"([A-Za-z_\s]+)", line)
                        if field_match:
                            actual_field = field_match.group(1).strip()
                            if actual_field:
                                mappings[actual_field] = target
                                logger.info(
                                    f"✅ Found mapping via flexible parsing: {actual_field} -> {target}"
                                )
                                break

        return mappings


class ClarificationParser:
    """Parser for extracting clarification questions from text"""

    def __init__(self):
        self.clarification_indicators = [
            "clarification:",
            "question:",
            "please confirm:",
            "verify:",
        ]

    def parse_clarifications(self, text: str) -> List[str]:
        """Extract clarification questions from text result"""
        clarifications = []

        lines = text.split("\n")
        for line in lines:
            line = line.strip()

            # Check for clarification indicators
            if any(
                indicator in line.lower() for indicator in self.clarification_indicators
            ):
                clarifications.append(line)
            elif line.endswith("?"):
                clarifications.append(line)

        return clarifications


class CompositeMappingParser:
    """Composite parser that tries multiple parsing strategies"""

    def __init__(self):
        self.parsers = [
            JSONMappingParser(),
            PatternMappingParser(),
            FallbackMappingParser(),
        ]
        self.clarification_parser = ClarificationParser()

    def parse_mappings_and_confidence(
        self, text: str
    ) -> Tuple[Dict[str, str], Dict[str, float]]:
        """
        Parse text using multiple strategies in order of preference

        Returns:
            Tuple of (mappings, confidence_scores)
        """
        logger.info(f"🔍 DEBUG: Raw crew output text (first 1000 chars): {text[:1000]}")

        # Try each parser in order
        for parser in self.parsers:
            try:
                mappings, confidence_scores = parser.parse(text)

                if mappings:
                    logger.info(f"📊 Total mappings extracted: {len(mappings)}")
                    if mappings:
                        logger.info(
                            f"📋 Mappings found: {list(mappings.keys())[:5]}..."
                        )
                    logger.info(f"📊 Confidence scores: {confidence_scores}")
                    return mappings, confidence_scores

            except MappingParseError as e:
                logger.warning(
                    f"Parser {parser.__class__.__name__} failed: {e.message}"
                )
                continue
            except Exception as e:
                logger.warning(f"Parser {parser.__class__.__name__} error: {e}")
                continue

        # If no parser succeeded, raise error
        logger.error("❌ No mappings extracted from crew result - NO FALLBACK")
        logger.error(f"❌ Full crew output was: {text[:1000]}")
        raise MappingParseError(
            "CrewAI failed to generate field mappings. This needs to be fixed."
        )

    def parse_clarifications(self, text: str) -> List[str]:
        """Parse clarification questions from text"""
        return self.clarification_parser.parse_clarifications(text)

    async def parse_response(self, text: str) -> Dict[str, Any]:
        """
        Parse response text and return structured data.
        This method provides compatibility with the base executor interface.
        """
        try:
            mappings, confidence_scores = self.parse_mappings_and_confidence(text)
            clarifications = self.parse_clarifications(text)

            return {
                "mappings": [
                    {
                        "source_field": source,
                        "target_field": target,
                        "confidence": confidence_scores.get(source, 0.7),
                        "status": "suggested",
                    }
                    for source, target in mappings.items()
                ],
                "confidence_scores": confidence_scores,
                "clarifications": clarifications,
            }
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            raise MappingParseError(f"Response parsing failed: {e}")


# Factory function
def create_mapping_parser() -> CompositeMappingParser:
    """Create a composite mapping parser with all strategies"""
    return CompositeMappingParser()
