# Task Brief: agile-velocity-optimizer

## Mission
Optimize team velocity and remove impediments to ensure the Redis caching implementation is delivered on schedule with maximum efficiency and quality across all participating teams.

## Context
This is a complex 6-week project involving 6 specialized agents working in parallel. Success requires careful coordination, proactive blocker resolution, and continuous optimization of team velocity.

## Primary Objectives

### 1. Sprint Planning Optimization (Week 1, ongoing)
- Design optimal sprint structure for 6-week timeline
- Balance workload across teams
- Identify and manage dependencies
- Create sprint goals and acceptance criteria

### 2. Impediment Resolution (Daily)
- Proactively identify blockers
- Facilitate cross-team communication
- Escalate issues appropriately
- Track resolution time

### 3. Velocity Tracking (Weekly)
- Measure team productivity
- Identify velocity trends
- Recommend process improvements
- Adjust timeline if needed

### 4. Resource Optimization (Ongoing)
- Ensure efficient resource allocation
- Identify skill gaps
- Coordinate knowledge sharing
- Optimize team composition

## Specific Deliverables

### Sprint Structure

```markdown
# File: docs/planning/caching/sprint-structure.md

## 6-Week Sprint Plan

### Sprint 0: Foundation (Week 1)
**Goal**: Set up infrastructure and foundational components
**Teams**: DevSecOps (lead), Backend Infrastructure, Product

**Key Deliverables**:
- Redis Docker configuration complete
- Monitoring infrastructure operational
- Cache schema designed
- Feature flags implemented
- Team onboarding complete

**Dependencies**: None
**Risks**: Environment setup delays

### Sprint 1: Backend Core (Weeks 2-3)
**Goal**: Implement core backend caching functionality
**Teams**: Backend (lead), QA, DevSecOps

**Key Deliverables**:
- User context caching live
- Cache invalidation service complete
- WebSocket events operational
- Security measures implemented
- Initial test suite ready

**Dependencies**: Sprint 0 completion
**Risks**: Complex invalidation logic

### Sprint 2: Frontend Integration (Week 4)
**Goal**: Optimize frontend and integrate with backend cache
**Teams**: Frontend (lead), QA

**Key Deliverables**:
- Custom cache removed
- React Query optimized
- API deduplication working
- WebSocket integration complete
- Performance tests passing

**Dependencies**: Sprint 1 WebSocket events
**Risks**: Legacy code removal

### Sprint 3: Architecture & Polish (Week 5)
**Goal**: Complete architectural improvements and testing
**Teams**: All teams

**Key Deliverables**:
- GlobalContext implemented
- Full integration testing complete
- Performance targets met
- Documentation finalized
- Canary deployment live

**Dependencies**: Sprint 2 completion
**Risks**: Integration complexity

### Sprint 4: Launch & Optimize (Week 6)
**Goal**: Full production rollout and optimization
**Teams**: All teams

**Key Deliverables**:
- Gradual rollout complete
- All metrics targets achieved
- Training delivered
- Retrospective completed
- Next phase planned

**Dependencies**: All previous sprints
**Risks**: Production issues
```

### Velocity Tracking Dashboard

```typescript
// File: src/dashboards/team-velocity.tsx
interface VelocityMetrics {
  team: string;
  plannedPoints: number;
  completedPoints: number;
  velocity: number;
  blockers: number;
  cycleTime: number; // hours
}

interface SprintMetrics {
  sprint: number;
  burndown: {
    ideal: number[];
    actual: number[];
  };
  teamMetrics: VelocityMetrics[];
  impediments: Impediment[];
}

export const VelocityDashboard: React.FC = () => {
  const metrics = useSprintMetrics();
  
  return (
    <Dashboard>
      <BurndownChart 
        ideal={metrics.burndown.ideal}
        actual={metrics.burndown.actual}
      />
      
      <TeamVelocityTable teams={metrics.teamMetrics} />
      
      <ImpedimentsList 
        impediments={metrics.impediments}
        onResolve={handleImpedimentResolve}
      />
      
      <VelocityTrends historicalData={metrics.historical} />
      
      <PredictiveAnalysis 
        currentVelocity={metrics.averageVelocity}
        remainingWork={metrics.remainingPoints}
        deadline={PROJECT_DEADLINE}
      />
    </Dashboard>
  );
};
```

### Dependency Management Matrix

```yaml
# File: docs/planning/caching/dependencies.yml
dependencies:
  backend_infrastructure:
    provides:
      - cache_schema
      - redis_connection
      - cache_keys
    requires: []
    critical_path: true
    
  backend_api:
    provides:
      - cache_endpoints
      - invalidation_service
      - websocket_events
    requires:
      - cache_schema
      - redis_connection
    critical_path: true
    
  frontend:
    provides:
      - ui_optimization
      - global_context
    requires:
      - cache_endpoints
      - websocket_events
    critical_path: true
    
  qa:
    provides:
      - test_coverage
      - performance_validation
    requires:
      - all_features
    critical_path: false
    
  devsecops:
    provides:
      - infrastructure
      - security_validation
    requires: []
    critical_path: true

coordination_points:
  daily_standup:
    time: "9:00 AM"
    duration: 15
    participants: all_teams
    
  dependency_sync:
    time: "2:00 PM"
    frequency: twice_weekly
    participants: [backend, frontend]
    
  blocker_resolution:
    time: "3:00 PM"
    frequency: daily
    participants: blocked_teams
```

### Impediment Resolution Process

```python
# File: scripts/impediment_tracker.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

class ImpedimentPriority(Enum):
    CRITICAL = "critical"  # Blocks multiple teams
    HIGH = "high"         # Blocks one team
    MEDIUM = "medium"     # Slows progress
    LOW = "low"          # Minor inconvenience

@dataclass
class Impediment:
    id: str
    description: str
    team_affected: List[str]
    priority: ImpedimentPriority
    identified_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    assigned_to: Optional[str] = None
    
    @property
    def resolution_time(self) -> Optional[timedelta]:
        if self.resolved_at:
            return self.resolved_at - self.identified_at
        return None
    
    @property
    def is_blocking_critical_path(self) -> bool:
        critical_teams = ['backend_infrastructure', 'backend_api', 'frontend']
        return any(team in critical_teams for team in self.team_affected)

class ImpedimentResolver:
    def __init__(self):
        self.impediments: List[Impediment] = []
        self.escalation_thresholds = {
            ImpedimentPriority.CRITICAL: timedelta(hours=2),
            ImpedimentPriority.HIGH: timedelta(hours=4),
            ImpedimentPriority.MEDIUM: timedelta(days=1),
            ImpedimentPriority.LOW: timedelta(days=2)
        }
    
    def add_impediment(self, impediment: Impediment):
        self.impediments.append(impediment)
        self._assign_resolver(impediment)
        self._notify_teams(impediment)
    
    def _assign_resolver(self, impediment: Impediment):
        if impediment.is_blocking_critical_path:
            impediment.assigned_to = "tech_lead"
        elif impediment.priority == ImpedimentPriority.HIGH:
            impediment.assigned_to = "scrum_master"
        else:
            impediment.assigned_to = "team_lead"
    
    def check_escalations(self):
        """Check if any impediments need escalation"""
        now = datetime.now()
        for imp in self.impediments:
            if imp.resolved_at:
                continue
                
            age = now - imp.identified_at
            threshold = self.escalation_thresholds[imp.priority]
            
            if age > threshold:
                self._escalate(imp)
    
    def _escalate(self, impediment: Impediment):
        """Escalate unresolved impediment"""
        escalation_path = {
            "team_lead": "scrum_master",
            "scrum_master": "tech_lead",
            "tech_lead": "engineering_manager",
            "engineering_manager": "vp_engineering"
        }
        
        current = impediment.assigned_to
        next_level = escalation_path.get(current, "vp_engineering")
        
        print(f"ESCALATION: Impediment {impediment.id} escalated to {next_level}")
        impediment.assigned_to = next_level
```

### Velocity Optimization Strategies

```markdown
# File: docs/planning/caching/velocity-optimization.md

## Velocity Improvement Tactics

### 1. Parallel Work Streams
- Backend and Frontend work in parallel after Sprint 0
- QA starts test creation in Sprint 1
- Documentation written alongside development

### 2. Dependency Minimization
- Mock interfaces for parallel development
- Feature flags enable independent deployment
- Shared contracts defined early

### 3. Knowledge Sharing
- Daily tech talks (15 min)
- Pair programming for complex tasks
- Shared documentation in real-time

### 4. Automation
- Automated testing reduces QA cycle
- CI/CD pipeline prevents integration delays
- Automated metrics collection

### 5. Communication Optimization
- Async updates via Slack
- Minimal meetings (15 min standups)
- Clear escalation paths

## Velocity Metrics

### Target Velocity by Team
- Backend Infrastructure: 40 points/sprint
- Backend API: 50 points/sprint
- Frontend: 45 points/sprint
- QA: 35 points/sprint
- DevSecOps: 30 points/sprint

### Velocity Improvement Goals
- Sprint 1: Baseline
- Sprint 2: +10% through process optimization
- Sprint 3: +20% through automation
- Sprint 4: Maintain peak velocity

## Risk Mitigation

### Velocity Risks
1. **Cross-team dependencies**
   - Mitigation: Daily dependency sync
   - Owner: Scrum Master

2. **Technical debt**
   - Mitigation: 20% time for refactoring
   - Owner: Tech Leads

3. **Scope creep**
   - Mitigation: Strict change control
   - Owner: Product Owner

4. **Team burnout**
   - Mitigation: Sustainable pace, no overtime
   - Owner: Engineering Manager
```

## Success Criteria

### Daily
- All teams have clear tasks
- No blocker > 4 hours old
- Dependencies identified early
- Progress visible to all

### Weekly
- Sprint goals on track
- Velocity within 10% of target
- Impediments decreasing
- Team morale high

### Project End
- Delivered on time
- All acceptance criteria met
- Team velocity improved
- Process improvements documented

## Communication

### Daily
- 9 AM: Team standup facilitation
- 2 PM: Dependency check
- 3 PM: Blocker resolution
- 5 PM: Progress update

### Weekly
- Monday: Sprint planning
- Wednesday: Velocity review
- Friday: Retrospective

### Escalation
- Blocked > 4 hours: Scrum Master
- Blocked > 8 hours: Tech Lead
- Blocked > 1 day: Engineering Manager
- Critical path risk: VP Engineering

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Immediate
**Priority**: Critical for project success