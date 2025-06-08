"""
Classification Handler for Agent-UI Communication
Manages data classifications and quality assessments.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from ..models.agent_communication import DataItem, DataClassification, ConfidenceLevel
from app.services.agent_ui_bridge_handlers.storage_manager import classification_storage
from app.models.agent_communication import AgentInsight, AgentQuestion

logger = logging.getLogger(__name__)

class ClassificationHandler:
    """Handles data item classifications and quality management."""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.data_classifications: Dict[str, DataItem] = {}
    
    def classify_data_item(self, item_id: str, data_type: str, content: Any, 
                             classification: DataClassification, 
                             agent_analysis: Dict, confidence: ConfidenceLevel,
                             page: str, issues: List[str], recommendations: List[str]):
        
        classification_entry = {
            "id": item_id,
            "type": data_type,
            "content": content,
            "classification": classification.value,
            "agent_analysis": agent_analysis,
            "confidence": confidence.value,
            "page": page,
            "issues": issues,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            classification_storage.save_classification(classification_entry)
            logger.info(f"Classified {data_type} item {item_id} as {classification.value}")
        except Exception as e:
            logger.error(f"Error saving classifications: {e}")
    
    def get_classified_data_for_page(self, page: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get classified data grouped by classification type for a page."""
        page_data = {
            "good_data": [],
            "needs_clarification": [],
            "unusable": []
        }
        
        for item in self.data_classifications.values():
            if item.page == page:
                item_dict = asdict(item)
                page_data[item.classification.value].append(item_dict)
        
        return page_data
    
    def update_data_classification(self, item_id: str, new_classification: DataClassification,
                                  updated_by: str = "user") -> Dict[str, Any]:
        """Update the classification of a data item."""
        if item_id not in self.data_classifications:
            return {"success": False, "error": "Data item not found"}
        
        old_classification = self.data_classifications[item_id].classification
        self.data_classifications[item_id].classification = new_classification
        
        # Log the update
        learning_context = {
            "item_id": item_id,
            "data_type": self.data_classifications[item_id].data_type,
            "old_classification": old_classification.value,
            "new_classification": new_classification.value,
            "updated_by": updated_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.storage_manager.store_learning_experience(learning_context)
        self.storage_manager.save_classifications(self.data_classifications)
        
        logger.info(f"Updated classification for {item_id}: {old_classification.value} -> {new_classification.value}")
        
        return {
            "success": True,
            "old_classification": old_classification.value,
            "new_classification": new_classification.value,
            "learning_stored": True
        }
    
    def get_classification_statistics(self, page: str = None) -> Dict[str, Any]:
        """Get classification statistics."""
        items = list(self.data_classifications.values())
        if page:
            items = [item for item in items if item.page == page]
        
        total_items = len(items)
        if total_items == 0:
            return {
                "total_items": 0,
                "by_classification": {},
                "by_confidence": {},
                "by_data_type": {},
                "quality_score": 0.0
            }
        
        # Group by classification
        by_classification = {}
        for item in items:
            cls = item.classification.value
            by_classification[cls] = by_classification.get(cls, 0) + 1
        
        # Group by confidence
        by_confidence = {}
        for item in items:
            conf = item.confidence.value
            by_confidence[conf] = by_confidence.get(conf, 0) + 1
        
        # Group by data type
        by_data_type = {}
        for item in items:
            dtype = item.data_type
            by_data_type[dtype] = by_data_type.get(dtype, 0) + 1
        
        # Calculate quality score (percentage of good data)
        good_data_count = by_classification.get("good_data", 0)
        quality_score = good_data_count / total_items if total_items > 0 else 0.0
        
        return {
            "total_items": total_items,
            "by_classification": by_classification,
            "by_confidence": by_confidence,
            "by_data_type": by_data_type,
            "quality_score": quality_score
        }
    
    def get_items_needing_clarification(self, page: str = None) -> List[Dict[str, Any]]:
        """Get data items that need clarification."""
        items = [
            asdict(item) for item in self.data_classifications.values()
            if item.classification == DataClassification.NEEDS_CLARIFICATION
            and (not page or item.page == page)
        ]
        
        # Sort by confidence (lowest first - most urgent)
        confidence_order = {"uncertain": 0, "low": 1, "medium": 2, "high": 3}
        items.sort(key=lambda x: confidence_order.get(x['confidence'], 0))
        
        return items
    
    def clear_classifications(self, page: str = None) -> int:
        """Clear classifications for a page or all pages."""
        initial_count = len(self.data_classifications)
        
        if page:
            self.data_classifications = {
                item_id: item for item_id, item in self.data_classifications.items()
                if item.page != page
            }
        else:
            self.data_classifications.clear()
        
        cleared_count = initial_count - len(self.data_classifications)
        
        if cleared_count > 0:
            self.storage_manager.save_classifications(self.data_classifications)
            logger.info(f"Cleared {cleared_count} data classifications")
        
        return cleared_count
    
    def load_classifications(self, classifications_data: Dict[str, Any]) -> None:
        """Load classifications from storage."""
        self.data_classifications.clear()
        for item_id, item_data in classifications_data.items():
            # Convert dict back to DataItem
            data_item = DataItem(
                id=item_data['id'],
                data_type=item_data['data_type'],
                classification=DataClassification(item_data['classification']),
                content=item_data['content'],
                agent_analysis=item_data['agent_analysis'],
                confidence=ConfidenceLevel(item_data['confidence']),
                issues=item_data.get('issues', []),
                recommendations=item_data.get('recommendations', []),
                page=item_data.get('page', 'discovery')
            )
            self.data_classifications[item_id] = data_item 