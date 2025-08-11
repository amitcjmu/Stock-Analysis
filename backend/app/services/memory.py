"""
Agent Memory System for CrewAI agents.
Provides persistent memory with learning capabilities and pattern recognition.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentMemory:
    """Persistent memory system for AI agents with learning capabilities."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.memory_file = self.data_dir / "agent_memory.pkl"

        # Memory structure
        self.experiences = {
            "analysis_attempt": [],  # Every analysis performed
            "user_feedback": [],  # All user corrections
            "learned_patterns": [],  # Extracted patterns
            "successful_analysis": [],  # Confirmed accurate analyses
            "placeholder_analysis": [],  # Intelligent fallback analyses
        }

        # Learning metrics
        self.learning_metrics = {
            "total_analyses": 0,
            "user_corrections": 0,
            "accuracy_improvements": 0.0,
            "confidence_evolution": [],
            "pattern_recognition_success": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Load existing memory
        self.load_memory()

    def add_experience(self, experience_type: str, data: Dict[str, Any]):
        """Add a new experience to memory."""
        if experience_type not in self.experiences:
            logger.warning(f"Unknown experience type: {experience_type}")
            return

        experience = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": experience_type,
            **data,
        }

        self.experiences[experience_type].append(experience)

        # Limit memory size to prevent unbounded growth
        max_experiences = 1000
        if len(self.experiences[experience_type]) > max_experiences:
            # Keep the most recent experiences
            self.experiences[experience_type] = self.experiences[experience_type][
                -max_experiences:
            ]

        # Auto-save after adding experience
        self.save_memory()

        logger.info(f"Added {experience_type} experience to agent memory")

    def get_relevant_experiences(self, filename: str, limit: int = 10) -> List[Dict]:
        """Get relevant past experiences for current analysis."""
        relevant = []

        # Get experiences with similar filenames or patterns
        for exp_type, experiences in self.experiences.items():
            for exp in experiences[-50:]:  # Look at recent experiences
                if self._is_relevant(exp, filename):
                    relevant.append(exp)

        # Sort by relevance and timestamp
        relevant.sort(
            key=lambda x: (
                self._calculate_relevance_score(x, filename),
                x.get("timestamp", ""),
            ),
            reverse=True,
        )

        return relevant[:limit]

    def get_recent_experiences(self, limit: int = 10) -> List[Dict]:
        """Get recent experiences regardless of type."""
        all_experiences = []

        # Collect all experiences from all types
        for exp_type, experiences in self.experiences.items():
            for exp in experiences:
                all_experiences.append(exp)

        # Sort by timestamp (most recent first)
        all_experiences.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return all_experiences[:limit]

    def _is_relevant(self, experience: Dict, filename: str) -> bool:
        """Check if an experience is relevant to the current analysis."""
        exp_filename = experience.get("filename", "")

        # Direct filename match
        if exp_filename == filename:
            return True

        # Similar filename patterns
        if exp_filename and filename:
            # Check for similar file extensions
            exp_ext = Path(exp_filename).suffix.lower()
            curr_ext = Path(filename).suffix.lower()
            if exp_ext == curr_ext and exp_ext in [".csv", ".xlsx", ".json"]:
                return True

            # Check for similar naming patterns
            exp_base = Path(exp_filename).stem.lower()
            curr_base = Path(filename).stem.lower()

            # Common CMDB export patterns
            cmdb_patterns = ["cmdb", "asset", "inventory", "server", "application"]
            if any(
                pattern in exp_base and pattern in curr_base
                for pattern in cmdb_patterns
            ):
                return True

        return False

    def _calculate_relevance_score(self, experience: Dict, filename: str) -> float:
        """Calculate relevance score for an experience."""
        score = 0.0

        exp_filename = experience.get("filename", "")

        # Direct filename match gets highest score
        if exp_filename == filename:
            score += 1.0

        # Similar file types
        if exp_filename and filename:
            exp_ext = Path(exp_filename).suffix.lower()
            curr_ext = Path(filename).suffix.lower()
            if exp_ext == curr_ext:
                score += 0.5

        # Recent experiences are more relevant
        try:
            exp_time = datetime.fromisoformat(experience.get("timestamp", ""))
            age_days = (datetime.utcnow() - exp_time).days
            if age_days < 7:
                score += 0.3
            elif age_days < 30:
                score += 0.1
        except (ValueError, TypeError):
            pass

        # Successful experiences are more relevant
        if experience.get("type") == "successful_analysis":
            score += 0.2

        return score

    def update_learning_metrics(self, metric: str, value: Any):
        """Update learning metrics with new values."""
        if metric in self.learning_metrics:
            if isinstance(self.learning_metrics[metric], (int, float)) and isinstance(
                value, (int, float)
            ):
                self.learning_metrics[metric] += value
            else:
                self.learning_metrics[metric] = value
        else:
            self.learning_metrics[metric] = value

        self.learning_metrics["last_updated"] = datetime.utcnow().isoformat()
        self.save_memory()

    def get_learning_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Get learned patterns, optionally filtered by type."""
        patterns = self.experiences.get("learned_patterns", [])

        if pattern_type:
            patterns = [p for p in patterns if p.get("pattern_type") == pattern_type]

        # Sort by confidence and recency
        patterns.sort(
            key=lambda x: (x.get("confidence_boost", 0), x.get("timestamp", "")),
            reverse=True,
        )

        return patterns

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics and health metrics."""
        total_experiences = sum(len(exp_list) for exp_list in self.experiences.values())

        stats = {
            "total_experiences": total_experiences,
            "experience_breakdown": {
                exp_type: len(exp_list)
                for exp_type, exp_list in self.experiences.items()
            },
            "learning_metrics": self.learning_metrics.copy(),
            "memory_file_exists": self.memory_file.exists(),
            "memory_file_size": (
                self.memory_file.stat().st_size if self.memory_file.exists() else 0
            ),
            "last_activity": self._get_last_activity(),
        }

        return stats

    def _get_last_activity(self) -> Optional[str]:
        """Get timestamp of last activity."""
        last_timestamp = None

        for exp_list in self.experiences.values():
            if exp_list:
                exp_timestamp = exp_list[-1].get("timestamp")
                if exp_timestamp and (
                    not last_timestamp or exp_timestamp > last_timestamp
                ):
                    last_timestamp = exp_timestamp

        return last_timestamp

    def save_memory(self):
        """Save memory to persistent storage."""
        try:
            memory_data = {
                "experiences": self.experiences,
                "learning_metrics": self.learning_metrics,
                "version": "1.0",
                "saved_at": datetime.utcnow().isoformat(),
            }

            # Use JSON serialization for security instead of pickle
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, default=str)

            logger.debug(f"Memory saved to {self.memory_file}")

        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def load_memory(self):
        """Load memory from persistent storage."""
        try:
            if self.memory_file.exists():
                # Use JSON deserialization for security instead of pickle
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.experiences = data.get("experiences", self.experiences)
                self.learning_metrics = data.get(
                    "learning_metrics", self.learning_metrics
                )

                logger.info(f"Memory loaded from {self.memory_file}")
                logger.info(
                    f"Loaded {sum(len(exp_list) for exp_list in self.experiences.values())} experiences"
                )
            else:
                logger.info("No existing memory file found, starting with fresh memory")

        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            # Initialize with empty memory on error
            self._initialize_empty_memory()

    def _initialize_empty_memory(self):
        """Initialize with empty memory structure."""
        self.experiences = {
            "analysis_attempt": [],
            "user_feedback": [],
            "learned_patterns": [],
            "successful_analysis": [],
            "placeholder_analysis": [],
        }

        self.learning_metrics = {
            "total_analyses": 0,
            "user_corrections": 0,
            "accuracy_improvements": 0.0,
            "confidence_evolution": [],
            "pattern_recognition_success": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def cleanup_old_experiences(self, days_to_keep: int = 90):
        """Clean up old experiences to prevent memory bloat."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_iso = cutoff_date.isoformat()

        cleaned_count = 0

        for exp_type, exp_list in self.experiences.items():
            original_count = len(exp_list)

            # Keep experiences newer than cutoff date
            self.experiences[exp_type] = [
                exp for exp in exp_list if exp.get("timestamp", "") > cutoff_iso
            ]

            cleaned_count += original_count - len(self.experiences[exp_type])

        if cleaned_count > 0:
            logger.info(
                f"Cleaned up {cleaned_count} old experiences (older than {days_to_keep} days)"
            )
            self.save_memory()

        return cleaned_count

    def export_memory(self, export_path: str) -> bool:
        """Export memory to JSON for analysis or backup."""
        try:
            export_data = {
                "experiences": self.experiences,
                "learning_metrics": self.learning_metrics,
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0",
            }

            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Memory exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
            return False


# Global agent memory instance
agent_memory = AgentMemory()
