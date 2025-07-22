"""
Progress Tracking Service for Manual Collection

Tracks progress of manual data collection activities including form completion,
validation status, confidence scores, and user engagement metrics.

Agent Team B3 - Task B3.5
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from .adaptive_form_service import AdaptiveForm, FormField
from .validation_service import FieldValidationResult


class ProgressStatus(str, Enum):
    """Progress status for collection activities"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    OVERDUE = "overdue"


class EngagementLevel(str, Enum):
    """User engagement levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISENGAGED = "disengaged"


class MilestoneType(str, Enum):
    """Types of progress milestones"""
    FORM_STARTED = "form_started"
    SECTION_COMPLETED = "section_completed"
    VALIDATION_PASSED = "validation_passed"
    FORM_SUBMITTED = "form_submitted"
    TEMPLATE_APPLIED = "template_applied"
    BULK_UPLOAD = "bulk_upload"
    CONFIDENCE_THRESHOLD = "confidence_threshold"


@dataclass
class ProgressMilestone:
    """Individual progress milestone"""
    milestone_id: str
    milestone_type: MilestoneType
    title: str
    description: str
    achieved_at: Optional[datetime] = None
    target_date: Optional[datetime] = None
    is_required: bool = True
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SectionProgress:
    """Progress tracking for form section"""
    section_id: str
    section_title: str
    total_fields: int
    completed_fields: int
    required_fields: int
    completed_required_fields: int
    validation_status: str  # 'valid', 'invalid', 'warning', 'pending'
    confidence_score: float
    completion_percentage: float
    time_spent_seconds: int
    last_updated: datetime
    field_progress: Dict[str, Dict[str, Any]]


@dataclass
class FormProgress:
    """Overall form progress tracking"""
    form_id: str
    application_id: UUID
    user_id: UUID
    status: ProgressStatus
    overall_completion_percentage: float
    validation_score: float
    confidence_score: float
    estimated_time_remaining_minutes: int
    time_spent_seconds: int
    sections_progress: List[SectionProgress]
    milestones: List[ProgressMilestone]
    started_at: datetime
    last_activity: datetime
    target_completion_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None


@dataclass
class UserEngagementMetrics:
    """User engagement tracking metrics"""
    user_id: UUID
    session_count: int
    total_time_spent_seconds: int
    average_session_duration_seconds: float
    forms_started: int
    forms_completed: int
    completion_rate: float
    engagement_level: EngagementLevel
    last_activity: datetime
    activity_streak_days: int
    preferred_work_hours: List[int]  # Hours of day (0-23)
    productivity_score: float


@dataclass
class CollectionAnalytics:
    """Analytics for collection performance"""
    total_applications: int
    applications_by_status: Dict[ProgressStatus, int]
    average_completion_time_hours: float
    average_confidence_score: float
    completion_rate: float
    abandonment_rate: float
    most_challenging_sections: List[Tuple[str, float]]  # (section_id, abandonment_rate)
    user_engagement_distribution: Dict[EngagementLevel, int]
    time_to_completion_distribution: Dict[str, int]  # time_range -> count


class ProgressTrackingService:
    """Service for tracking manual collection progress and user engagement"""
    
    # Time thresholds for engagement classification (in hours)
    ENGAGEMENT_THRESHOLDS = {
        'session_duration': {
            'high': 30,      # 30+ minutes
            'medium': 10,    # 10-30 minutes
            'low': 5         # 5-10 minutes
        },
        'inactivity': {
            'disengaged': 72,  # 3+ days
            'low': 24,         # 1+ day
            'medium': 8        # 8+ hours
        }
    }
    
    # Milestone definitions for different form types
    STANDARD_MILESTONES = [
        {
            'type': MilestoneType.FORM_STARTED,
            'title': 'Form Started',
            'description': 'User has begun filling out the form',
            'weight': 0.1,
            'required': True
        },
        {
            'type': MilestoneType.SECTION_COMPLETED,
            'title': 'Infrastructure Section Complete',
            'description': 'Infrastructure details section completed',
            'weight': 0.2,
            'required': True
        },
        {
            'type': MilestoneType.SECTION_COMPLETED,
            'title': 'Application Section Complete',
            'description': 'Application details section completed',
            'weight': 0.3,
            'required': True
        },
        {
            'type': MilestoneType.VALIDATION_PASSED,
            'title': 'Validation Passed',
            'description': 'All required fields pass validation',
            'weight': 0.2,
            'required': True
        },
        {
            'type': MilestoneType.CONFIDENCE_THRESHOLD,
            'title': '70% Confidence Achieved',
            'description': 'Data quality sufficient for preliminary 6R recommendation',
            'weight': 0.1,
            'required': False
        },
        {
            'type': MilestoneType.FORM_SUBMITTED,
            'title': 'Form Submitted',
            'description': 'Form successfully submitted',
            'weight': 0.1,
            'required': True
        }
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._form_progress = {}  # form_id -> FormProgress
        self._user_metrics = {}   # user_id -> UserEngagementMetrics
        self._session_data = defaultdict(list)  # user_id -> session events

    async def initialize_form_progress(
        self,
        form: AdaptiveForm,
        user_id: UUID,
        target_completion_hours: Optional[int] = None
    ) -> FormProgress:
        """
        Initialize progress tracking for a new form.
        
        Core implementation of B3.5 - progress tracking for manual collection.
        Sets up tracking structure for form completion monitoring.
        """
        self.logger.info(f"Initializing progress tracking for form {form.id}")
        
        # Initialize section progress
        sections_progress = []
        for section in form.sections:
            section_progress = SectionProgress(
                section_id=section.id,
                section_title=section.title,
                total_fields=len(section.fields),
                completed_fields=0,
                required_fields=sum(1 for field in section.fields if self._is_field_required(field)),
                completed_required_fields=0,
                validation_status='pending',
                confidence_score=0.0,
                completion_percentage=0.0,
                time_spent_seconds=0,
                last_updated=datetime.now(),
                field_progress={}
            )
            sections_progress.append(section_progress)
        
        # Generate milestones
        milestones = await self._generate_form_milestones(form)
        
        # Calculate target completion date
        target_date = None
        if target_completion_hours:
            target_date = datetime.now() + timedelta(hours=target_completion_hours)
        
        form_progress = FormProgress(
            form_id=form.id,
            application_id=form.application_id,
            user_id=user_id,
            status=ProgressStatus.NOT_STARTED,
            overall_completion_percentage=0.0,
            validation_score=0.0,
            confidence_score=0.0,
            estimated_time_remaining_minutes=form.estimated_completion_time,
            time_spent_seconds=0,
            sections_progress=sections_progress,
            milestones=milestones,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            target_completion_date=target_date
        )
        
        self._form_progress[form.id] = form_progress
        await self._initialize_user_metrics(user_id)
        
        return form_progress

    async def update_field_progress(
        self,
        form_id: str,
        field_id: str,
        field_value: Any,
        validation_result: FieldValidationResult,
        time_spent_seconds: int = 0
    ) -> FormProgress:
        """Update progress when a field is modified"""
        
        progress = self._form_progress.get(form_id)
        if not progress:
            raise ValueError(f"Progress tracking not found for form {form_id}")
        
        # Update field progress
        section_id = self._get_field_section(field_id, progress.sections_progress)
        if section_id:
            section_progress = next(s for s in progress.sections_progress if s.section_id == section_id)
            
            # Update field-level progress
            section_progress.field_progress[field_id] = {
                'value': field_value,
                'is_valid': validation_result.is_valid,
                'confidence_score': validation_result.confidence_score,
                'last_updated': datetime.now(),
                'time_spent_seconds': time_spent_seconds
            }
            
            # Recalculate section progress
            await self._recalculate_section_progress(section_progress, progress)
        
        # Update overall progress
        await self._recalculate_overall_progress(progress)
        
        # Update user engagement
        await self._update_user_engagement(progress.user_id, time_spent_seconds)
        
        # Check milestones
        await self._check_milestones(progress)
        
        return progress

    async def update_bulk_progress(
        self,
        form_id: str,
        bulk_data: Dict[str, Any],
        processing_result: Any  # BulkDataProcessingResult
    ) -> FormProgress:
        """Update progress from bulk data upload"""
        
        progress = self._form_progress.get(form_id)
        if not progress:
            raise ValueError(f"Progress tracking not found for form {form_id}")
        
        # Mark form as started if not already
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.status = ProgressStatus.IN_PROGRESS
            await self._achieve_milestone(progress, MilestoneType.FORM_STARTED)
        
        # Update field progress for bulk data
        for field_id, value in bulk_data.items():
            section_id = self._get_field_section(field_id, progress.sections_progress)
            if section_id:
                section_progress = next(s for s in progress.sections_progress if s.section_id == section_id)
                section_progress.field_progress[field_id] = {
                    'value': value,
                    'is_valid': True,  # Assume bulk data is validated
                    'confidence_score': 0.8,  # Default confidence for bulk data
                    'last_updated': datetime.now(),
                    'time_spent_seconds': 0,
                    'source': 'bulk_upload'
                }
        
        # Recalculate progress
        for section_progress in progress.sections_progress:
            await self._recalculate_section_progress(section_progress, progress)
        
        await self._recalculate_overall_progress(progress)
        
        # Mark bulk upload milestone
        await self._achieve_milestone(progress, MilestoneType.BULK_UPLOAD)
        
        return progress

    async def get_form_progress(self, form_id: str) -> Optional[FormProgress]:
        """Get current progress for a form"""
        return self._form_progress.get(form_id)

    async def get_user_engagement_metrics(self, user_id: UUID) -> Optional[UserEngagementMetrics]:
        """Get engagement metrics for a user"""
        return self._user_metrics.get(str(user_id))

    async def get_collection_analytics(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> CollectionAnalytics:
        """Get analytics for collection performance"""
        
        # Filter progress data by date range if specified
        progress_data = list(self._form_progress.values())
        if date_range:
            start_date, end_date = date_range
            progress_data = [
                p for p in progress_data 
                if start_date <= p.started_at <= end_date
            ]
        
        if not progress_data:
            return self._empty_analytics()
        
        # Calculate analytics
        total_applications = len(progress_data)
        
        # Status distribution
        status_counts = defaultdict(int)
        for progress in progress_data:
            status_counts[progress.status] += 1
        
        # Completion metrics
        completed_forms = [p for p in progress_data if p.status == ProgressStatus.COMPLETED]
        completion_rate = len(completed_forms) / total_applications if total_applications > 0 else 0.0
        
        abandoned_forms = [p for p in progress_data if p.status == ProgressStatus.ABANDONED]
        abandonment_rate = len(abandoned_forms) / total_applications if total_applications > 0 else 0.0
        
        # Average completion time
        avg_completion_time = 0.0
        if completed_forms:
            completion_times = [
                (p.completion_date - p.started_at).total_seconds() / 3600 
                for p in completed_forms if p.completion_date
            ]
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0.0
        
        # Average confidence score
        avg_confidence = sum(p.confidence_score for p in progress_data) / len(progress_data)
        
        # Most challenging sections
        section_challenges = defaultdict(list)
        for progress in progress_data:
            for section in progress.sections_progress:
                if section.completion_percentage < 50:  # Consider <50% completion as challenging
                    section_challenges[section.section_id].append(section.completion_percentage)
        
        challenging_sections = []
        for section_id, completion_rates in section_challenges.items():
            avg_completion = sum(completion_rates) / len(completion_rates)
            challenging_sections.append((section_id, 1.0 - avg_completion))  # Invert for challenge score
        
        challenging_sections.sort(key=lambda x: x[1], reverse=True)
        
        # User engagement distribution
        engagement_counts = defaultdict(int)
        for metrics in self._user_metrics.values():
            engagement_counts[metrics.engagement_level] += 1
        
        # Time to completion distribution
        time_distribution = defaultdict(int)
        for progress in completed_forms:
            if progress.completion_date:
                hours = (progress.completion_date - progress.started_at).total_seconds() / 3600
                if hours <= 1:
                    time_distribution['< 1 hour'] += 1
                elif hours <= 4:
                    time_distribution['1-4 hours'] += 1
                elif hours <= 24:
                    time_distribution['4-24 hours'] += 1
                elif hours <= 168:  # 1 week
                    time_distribution['1-7 days'] += 1
                else:
                    time_distribution['> 1 week'] += 1
        
        return CollectionAnalytics(
            total_applications=total_applications,
            applications_by_status=dict(status_counts),
            average_completion_time_hours=avg_completion_time,
            average_confidence_score=avg_confidence,
            completion_rate=completion_rate,
            abandonment_rate=abandonment_rate,
            most_challenging_sections=challenging_sections[:5],
            user_engagement_distribution=dict(engagement_counts),
            time_to_completion_distribution=dict(time_distribution)
        )

    async def pause_form_progress(self, form_id: str, reason: Optional[str] = None) -> bool:
        """Pause form progress"""
        progress = self._form_progress.get(form_id)
        if progress and progress.status == ProgressStatus.IN_PROGRESS:
            progress.status = ProgressStatus.PAUSED
            progress.last_activity = datetime.now()
            self.logger.info(f"Paused form {form_id}: {reason}")
            return True
        return False

    async def resume_form_progress(self, form_id: str) -> bool:
        """Resume paused form progress"""
        progress = self._form_progress.get(form_id)
        if progress and progress.status == ProgressStatus.PAUSED:
            progress.status = ProgressStatus.IN_PROGRESS
            progress.last_activity = datetime.now()
            self.logger.info(f"Resumed form {form_id}")
            return True
        return False

    async def abandon_form_progress(self, form_id: str, reason: Optional[str] = None) -> bool:
        """Mark form as abandoned"""
        progress = self._form_progress.get(form_id)
        if progress and progress.status in [ProgressStatus.IN_PROGRESS, ProgressStatus.PAUSED]:
            progress.status = ProgressStatus.ABANDONED
            progress.last_activity = datetime.now()
            self.logger.info(f"Abandoned form {form_id}: {reason}")
            return True
        return False

    def _is_field_required(self, field: FormField) -> bool:
        """Check if field is required"""
        return field.validation and any(rule.name == 'REQUIRED' for rule in (field.validation.rules or []))

    async def _generate_form_milestones(self, form: AdaptiveForm) -> List[ProgressMilestone]:
        """Generate milestones for form based on its structure"""
        milestones = []
        
        # Add standard milestones
        for milestone_config in self.STANDARD_MILESTONES:
            milestone = ProgressMilestone(
                milestone_id=f"{form.id}_{milestone_config['type'].value}",
                milestone_type=milestone_config['type'],
                title=milestone_config['title'],
                description=milestone_config['description'],
                is_required=milestone_config['required'],
                weight=milestone_config['weight']
            )
            milestones.append(milestone)
        
        # Add section-specific milestones
        for section in form.sections:
            milestone = ProgressMilestone(
                milestone_id=f"{form.id}_section_{section.id}",
                milestone_type=MilestoneType.SECTION_COMPLETED,
                title=f"{section.title} Complete",
                description=f"Completed {section.title} section",
                is_required=True,
                weight=0.3 / len(form.sections),  # Distribute 30% across sections
                metadata={'section_id': section.id}
            )
            milestones.append(milestone)
        
        return milestones

    async def _initialize_user_metrics(self, user_id: UUID) -> None:
        """Initialize user engagement metrics if not exists"""
        user_key = str(user_id)
        if user_key not in self._user_metrics:
            self._user_metrics[user_key] = UserEngagementMetrics(
                user_id=user_id,
                session_count=0,
                total_time_spent_seconds=0,
                average_session_duration_seconds=0.0,
                forms_started=0,
                forms_completed=0,
                completion_rate=0.0,
                engagement_level=EngagementLevel.MEDIUM,
                last_activity=datetime.now(),
                activity_streak_days=0,
                preferred_work_hours=[],
                productivity_score=0.5
            )

    def _get_field_section(self, field_id: str, sections: List[SectionProgress]) -> Optional[str]:
        """Get section ID for a field"""
        # This would typically check form definition, for now use heuristics
        if 'os_version' in field_id or 'specifications' in field_id or 'network' in field_id:
            return 'infrastructure'
        elif 'business' in field_id or 'compliance' in field_id or 'stakeholder' in field_id:
            return 'business'
        else:
            return 'application'

    async def _recalculate_section_progress(self, section: SectionProgress, form_progress: FormProgress) -> None:
        """Recalculate progress for a section"""
        completed_fields = len([f for f in section.field_progress.values() if f.get('value')])
        completed_required = len([f for f in section.field_progress.values() if f.get('value') and f.get('is_valid')])
        
        section.completed_fields = completed_fields
        section.completed_required_fields = completed_required
        section.completion_percentage = (completed_fields / section.total_fields * 100) if section.total_fields > 0 else 0
        
        # Calculate section confidence
        if section.field_progress:
            confidence_scores = [f.get('confidence_score', 0) for f in section.field_progress.values() if f.get('value')]
            section.confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Update validation status
        if completed_required >= section.required_fields:
            section.validation_status = 'valid'
        elif completed_fields > 0:
            section.validation_status = 'warning'
        else:
            section.validation_status = 'pending'
        
        section.last_updated = datetime.now()

    async def _recalculate_overall_progress(self, progress: FormProgress) -> None:
        """Recalculate overall form progress"""
        total_fields = sum(s.total_fields for s in progress.sections_progress)
        completed_fields = sum(s.completed_fields for s in progress.sections_progress)
        
        progress.overall_completion_percentage = (completed_fields / total_fields * 100) if total_fields > 0 else 0
        
        # Calculate overall confidence
        if progress.sections_progress:
            confidence_scores = [s.confidence_score for s in progress.sections_progress if s.confidence_score > 0]
            progress.confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Update status
        if progress.overall_completion_percentage >= 100:
            progress.status = ProgressStatus.COMPLETED
            progress.completion_date = datetime.now()
        elif progress.overall_completion_percentage > 0:
            progress.status = ProgressStatus.IN_PROGRESS
        
        progress.last_activity = datetime.now()

    async def _update_user_engagement(self, user_id: UUID, time_spent_seconds: int) -> None:
        """Update user engagement metrics"""
        metrics = self._user_metrics.get(str(user_id))
        if metrics:
            metrics.total_time_spent_seconds += time_spent_seconds
            metrics.last_activity = datetime.now()
            
            # Recalculate engagement level
            await self._recalculate_engagement_level(metrics)

    async def _check_milestones(self, progress: FormProgress) -> None:
        """Check and update milestone achievements"""
        for milestone in progress.milestones:
            if milestone.achieved_at:
                continue  # Already achieved
            
            achieved = False
            
            if milestone.milestone_type == MilestoneType.FORM_STARTED:
                achieved = progress.overall_completion_percentage > 0
            elif milestone.milestone_type == MilestoneType.SECTION_COMPLETED:
                section_id = milestone.metadata.get('section_id') if milestone.metadata else None
                if section_id:
                    section = next((s for s in progress.sections_progress if s.section_id == section_id), None)
                    achieved = section and section.completion_percentage >= 100
            elif milestone.milestone_type == MilestoneType.VALIDATION_PASSED:
                achieved = all(s.validation_status == 'valid' for s in progress.sections_progress)
            elif milestone.milestone_type == MilestoneType.CONFIDENCE_THRESHOLD:
                achieved = progress.confidence_score >= 0.7
            elif milestone.milestone_type == MilestoneType.FORM_SUBMITTED:
                achieved = progress.status == ProgressStatus.COMPLETED
            
            if achieved:
                await self._achieve_milestone(progress, milestone.milestone_type)

    async def _achieve_milestone(self, progress: FormProgress, milestone_type: MilestoneType) -> None:
        """Mark milestone as achieved"""
        for milestone in progress.milestones:
            if milestone.milestone_type == milestone_type and not milestone.achieved_at:
                milestone.achieved_at = datetime.now()
                self.logger.info(f"Milestone achieved: {milestone.title} for form {progress.form_id}")
                break

    async def _recalculate_engagement_level(self, metrics: UserEngagementMetrics) -> None:
        """Recalculate user engagement level"""
        # Calculate based on recent activity, session duration, and completion rate
        hours_since_last_activity = (datetime.now() - metrics.last_activity).total_seconds() / 3600
        
        if hours_since_last_activity > self.ENGAGEMENT_THRESHOLDS['inactivity']['disengaged']:
            metrics.engagement_level = EngagementLevel.DISENGAGED
        elif metrics.completion_rate >= 0.8 and metrics.average_session_duration_seconds >= 1800:  # 30 min
            metrics.engagement_level = EngagementLevel.HIGH
        elif metrics.completion_rate >= 0.5 or metrics.average_session_duration_seconds >= 600:  # 10 min
            metrics.engagement_level = EngagementLevel.MEDIUM
        else:
            metrics.engagement_level = EngagementLevel.LOW

    def _empty_analytics(self) -> CollectionAnalytics:
        """Return empty analytics structure"""
        return CollectionAnalytics(
            total_applications=0,
            applications_by_status={},
            average_completion_time_hours=0.0,
            average_confidence_score=0.0,
            completion_rate=0.0,
            abandonment_rate=0.0,
            most_challenging_sections=[],
            user_engagement_distribution={},
            time_to_completion_distribution={}
        )