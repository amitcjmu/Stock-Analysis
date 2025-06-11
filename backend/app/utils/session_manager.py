from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.models.session import Session
from app.models.engagement import Engagement
from app.models.user import User
from app.schemas.session import SessionCreate, SessionUpdate
from app.core.security import get_password_hash

class SessionManager:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_engagements(self, user_id: str) -> List[Engagement]:
        """Get all engagements a user has access to"""
        result = await self.db.execute(
            select(Engagement)
            .join(User.roles)
            .filter(User.id == user_id)
        )
        return result.scalars().all()
    
    async def get_engagement_sessions(self, engagement_id: str) -> List[Session]:
        """Get all sessions for an engagement"""
        result = await self.db.execute(
            select(Session)
            .filter(Session.engagement_id == engagement_id)
            .order_by(Session.created_at.desc())
        )
        return result.scalars().all()
    
    async def create_session(
        self,
        engagement_id: str,
        user_id: str,
        session_data: Optional[Dict] = None,
        is_default: bool = False,
        description: Optional[str] = None
    ) -> Session:
        """Create a new session"""
        # If this is the first session for the engagement, make it the default
        existing_sessions = await self.get_engagement_sessions(engagement_id)
        if not existing_sessions:
            is_default = True
            
        # If making this the default, unset any existing default
        if is_default:
            await self.db.execute(
                Session.__table__
                .update()
                .where(Session.engagement_id == engagement_id)
                .values(is_default=False)
            )
        
        session = Session(
            id=str(uuid.uuid4()),
            engagement_id=engagement_id,
            created_by=user_id,
            is_default=is_default,
            description=description or "Initial data import",
            data=session_data or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def update_session(
        self,
        session_id: str,
        updates: Dict,
        user_id: str
    ) -> Optional[Session]:
        """Update an existing session"""
        result = await self.db.execute(
            select(Session)
            .filter(Session.id == session_id)
        )
        session = result.scalars().first()
        
        if not session:
            return None
            
        # If making this the default, unset any existing default
        if updates.get('is_default', False):
            await self.db.execute(
                Session.__table__
                .update()
                .where(Session.engagement_id == session.engagement_id)
                .values(is_default=False)
            )
        
        for key, value in updates.items():
            setattr(session, key, value)
            
        session.updated_by = user_id
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_default_session(self, engagement_id: str) -> Optional[Session]:
        """Get the default session for an engagement"""
        result = await self.db.execute(
            select(Session)
            .filter(
                Session.engagement_id == engagement_id,
                Session.is_default == True
            )
        )
        return result.scalars().first()
    
    async def get_session_context(
        self,
        user: User,
        client_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Get the appropriate session context based on user permissions and provided IDs.
        Returns a dictionary with client, engagement, and session information.
        """
        context = {
            'client': None,
            'engagement': None,
            'session': None,
            'available_clients': [],
            'available_engagements': [],
            'available_sessions': []
        }
        
        # Get user's accessible engagements
        engagements = await self.get_user_engagements(user.id)
        
        if not engagements:
            return context
            
        # Set available clients (unique from engagements)
        clients = {e.client for e in engagements}
        context['available_clients'] = [
            {'id': c.id, 'name': c.name}
            for c in clients
        ]
        
        # If no client specified, use the first one
        if not client_id and context['available_clients']:
            client_id = context['available_clients'][0]['id']
        
        if client_id:
            # Filter engagements for this client
            client_engagements = [e for e in engagements if e.client_id == client_id]
            context['available_engagements'] = [
                {'id': e.id, 'name': e.name}
                for e in client_engagements
            ]
            
            # If no engagement specified, use the first one
            if not engagement_id and client_engagements:
                engagement_id = client_engagements[0].id
                
            if engagement_id:
                engagement = next((e for e in client_engagements if e.id == engagement_id), None)
                if engagement:
                    context['engagement'] = {
                        'id': engagement.id,
                        'name': engagement.name,
                        'client_id': engagement.client_id
                    }
                    
                    # Get sessions for this engagement
                    sessions = await self.get_engagement_sessions(engagement_id)
                    context['available_sessions'] = [
                        {'id': s.id, 'name': s.description or f"Session {i+1}", 'is_default': s.is_default}
                        for i, s in enumerate(sessions)
                    ]
                    
                    # If no session specified, use the default or first one
                    if not session_id:
                        default_session = next((s for s in sessions if s.is_default), sessions[0] if sessions else None)
                        if default_session:
                            session_id = default_session.id
                    
                    if session_id:
                        session = next((s for s in sessions if s.id == session_id), None)
                        if session:
                            context['session'] = {
                                'id': session.id,
                                'name': session.description or 'Current Session',
                                'is_default': session.is_default,
                                'created_at': session.created_at.isoformat(),
                                'created_by': session.created_by
                            }
        
        return context
