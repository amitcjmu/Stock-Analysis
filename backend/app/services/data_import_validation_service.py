"""
Data Import Validation Service
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.data_import_schemas import ValidationSession, ValidationAgentResult

class DataImportValidationService:
    """Service for handling data import validation operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.validation_sessions_path = "backend/data/validation_sessions"
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure the validation sessions storage directory exists"""
        os.makedirs(self.validation_sessions_path, exist_ok=True)
    
    async def store_validation_session(self, session_data: Dict[str, Any]) -> str:
        """
        Store validation session data
        In production, this would save to database
        For now, we save to file for persistence
        """
        try:
            session_id = session_data['file_id']
            file_path = os.path.join(self.validation_sessions_path, f"{session_id}.json")
            
            # Convert datetime objects to strings for JSON serialization
            serializable_data = self._make_json_serializable(session_data)
            
            with open(file_path, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            return session_id
            
        except Exception as e:
            print(f"Error storing validation session: {e}")
            return ""
    
    async def get_validation_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve validation session by ID"""
        try:
            file_path = os.path.join(self.validation_sessions_path, f"{session_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                session_data = json.load(f)
            
            return session_data
            
        except Exception as e:
            print(f"Error retrieving validation session {session_id}: {e}")
            return None
    
    async def get_user_validation_sessions(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get validation sessions for a specific user"""
        try:
            sessions = []
            
            # In a real implementation, this would be a database query
            # For now, scan the files directory
            if os.path.exists(self.validation_sessions_path):
                for filename in os.listdir(self.validation_sessions_path):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(self.validation_sessions_path, filename), 'r') as f:
                                session = json.load(f)
                                if session.get('uploaded_by') == user_id:
                                    sessions.append(session)
                        except:
                            continue
            
            # Sort by upload time (most recent first)
            sessions.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            print(f"Error getting user validation sessions: {e}")
            return []
    
    async def update_validation_status(self, session_id: str, status: str, agent_results: List[Dict[str, Any]] = None) -> bool:
        """Update validation session status and results"""
        try:
            session = await self.get_validation_session(session_id)
            if not session:
                return False
            
            session['status'] = status
            if agent_results:
                session['agent_results'] = agent_results
            session['completion_time'] = datetime.now().isoformat()
            
            await self.store_validation_session(session)
            return True
            
        except Exception as e:
            print(f"Error updating validation status: {e}")
            return False
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up validation sessions older than specified days"""
        try:
            cleanup_count = 0
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            if os.path.exists(self.validation_sessions_path):
                for filename in os.listdir(self.validation_sessions_path):
                    if filename.endswith('.json'):
                        file_path = os.path.join(self.validation_sessions_path, filename)
                        file_stat = os.stat(file_path)
                        
                        if file_stat.st_mtime < cutoff_date:
                            os.remove(file_path)
                            cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            print(f"Error cleaning up old sessions: {e}")
            return 0
    
    def _make_json_serializable(self, data: Any) -> Any:
        """Convert data to be JSON serializable"""
        if isinstance(data, dict):
            return {key: self._make_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics across all sessions"""
        try:
            stats = {
                'total_sessions': 0,
                'approved_sessions': 0,
                'rejected_sessions': 0,
                'sessions_with_warnings': 0,
                'by_category': {},
                'common_failures': [],
                'average_processing_time': 0
            }
            
            processing_times = []
            
            if os.path.exists(self.validation_sessions_path):
                for filename in os.listdir(self.validation_sessions_path):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(self.validation_sessions_path, filename), 'r') as f:
                                session = json.load(f)
                                
                                stats['total_sessions'] += 1
                                
                                status = session.get('status', 'unknown')
                                if status == 'approved':
                                    stats['approved_sessions'] += 1
                                elif status == 'rejected':
                                    stats['rejected_sessions'] += 1
                                elif status == 'approved_with_warnings':
                                    stats['sessions_with_warnings'] += 1
                                
                                category = session.get('category', 'unknown')
                                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                                
                                # Calculate processing time if available
                                uploaded_at = session.get('uploaded_at')
                                completed_at = session.get('completion_time')
                                if uploaded_at and completed_at:
                                    try:
                                        upload_time = datetime.fromisoformat(uploaded_at.replace('Z', ''))
                                        complete_time = datetime.fromisoformat(completed_at.replace('Z', ''))
                                        processing_time = (complete_time - upload_time).total_seconds()
                                        processing_times.append(processing_time)
                                    except:
                                        pass
                        except:
                            continue
            
            if processing_times:
                stats['average_processing_time'] = sum(processing_times) / len(processing_times)
            
            return stats
            
        except Exception as e:
            print(f"Error getting validation statistics: {e}")
            return {} 