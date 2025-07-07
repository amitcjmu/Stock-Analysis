# Team Coordination Briefing - July 2025 Revamp

## Overview
This document coordinates the work of all six Sonnet 4 teams working on the July 2025 platform revamp. Each team has specific responsibilities but must coordinate to ensure successful integration.

## Team Dependencies and Coordination

### Dependency Chain
```
Alpha (API) → Beta (Hooks) → Gamma (Components) → Delta (State) → Epsilon (CrewAI) → Zeta (E2E)
    ↓           ↓              ↓                 ↓              ↓              ↓
    APIs    →   Hooks     →   Components   →   State     →   AI Logic   →   Tests
```

### Critical Path
1. **Alpha** must complete API consolidation first
2. **Beta** depends on Alpha's consolidated APIs
3. **Gamma** depends on Beta's consolidated hooks
4. **Delta** can work in parallel with Gamma on state management
5. **Epsilon** depends on consolidated APIs and state management
6. **Zeta** tests integration of all teams' work

## Inter-Team Communication

### Daily Sync Schedule
- **9:00 AM EST** - Alpha & Beta sync (API → Hooks)
- **11:00 AM EST** - Beta & Gamma sync (Hooks → Components)
- **1:00 PM EST** - Gamma & Delta sync (Components → State)
- **3:00 PM EST** - Delta & Epsilon sync (State → CrewAI)
- **5:00 PM EST** - All teams status report to Zeta

### Weekly Coordination Meeting
- **Fridays 2:00 PM EST** - All teams
- Review progress, blockers, and next week's priorities
- Demo integrated features
- Plan integration testing

## Shared Resources

### Common Files (Coordinate Changes)
```
/src/types/          - TypeScript definitions (All teams)
/src/services/       - API services (Alpha, Beta, Gamma)
/src/hooks/          - React hooks (Beta, Gamma)
/src/contexts/       - React contexts (Beta, Delta, Gamma)
/src/components/     - UI components (Gamma, Delta)
/backend/app/api/    - API endpoints (Alpha, Epsilon)
/backend/app/services/ - Backend services (Alpha, Epsilon)
```

### Shared Standards
- **TypeScript**: Strict mode, proper typing
- **Error Handling**: Consistent error boundaries and API responses
- **Testing**: 80% coverage minimum
- **Code Style**: Prettier + ESLint configurations
- **Git**: Feature branch naming: `team-name/feature-description`

## Integration Milestones

### Week 1: Foundation
- **Alpha**: API v1 consolidation complete
- **Beta**: Begin hook migration using Alpha's APIs
- **Gamma**: Plan component updates
- **Delta**: Start state management fixes
- **Epsilon**: Set up CrewAI infrastructure
- **Zeta**: Set up E2E testing framework

### Week 2: Core Integration
- **Alpha**: API testing and documentation
- **Beta**: Hook consolidation 70% complete
- **Gamma**: Begin component updates using Beta's hooks
- **Delta**: Multi-tenant context fixes complete
- **Epsilon**: First CrewAI agents implemented
- **Zeta**: Authentication and basic flow tests

### Week 3: Advanced Features
- **Alpha**: Performance optimization
- **Beta**: Specialized hooks complete
- **Gamma**: Component migration 80% complete
- **Delta**: Global state management complete
- **Epsilon**: Discovery crew integration
- **Zeta**: Full flow testing

### Week 4: Polish and Testing
- **Alpha**: Final API optimizations
- **Beta**: Hook testing and documentation
- **Gamma**: Component testing and accessibility
- **Delta**: State recovery and persistence
- **Epsilon**: Agent monitoring and learning
- **Zeta**: Performance and visual testing

## Risk Management

### High-Risk Integration Points
1. **API Changes Breaking Frontend**: Alpha → Beta → Gamma
2. **State Management Conflicts**: Delta → Gamma
3. **CrewAI Integration**: Epsilon → Alpha
4. **Test Data Conflicts**: Zeta → All teams

### Mitigation Strategies
1. **Feature Flags**: Enable/disable new features
2. **Backward Compatibility**: Maintain old patterns during migration
3. **Staged Rollouts**: Team-by-team integration
4. **Rollback Plans**: Each team maintains rollback procedures

## Communication Protocols

### Slack Channels
- **#revamp-coordination** - Cross-team communication
- **#revamp-blockers** - Urgent issues requiring help
- **#revamp-demos** - Feature demonstrations
- **#revamp-testing** - Testing coordination

### Status Updates
Each team provides daily updates in the following format:
```markdown
## [Team Name] - [Date]
**Completed**: What was finished
**In Progress**: Current work
**Blockers**: Issues needing help
**Next**: Tomorrow's priorities
**Dependencies**: Waiting for other teams
```

### Emergency Escalation
1. **Slack mention**: @channel in #revamp-blockers
2. **Email**: Team leads mailing list
3. **Emergency call**: Scheduled within 1 hour

## Quality Gates

### Before Integration
Each team must complete:
- [ ] Unit tests passing (80% coverage)
- [ ] Integration tests with dependencies
- [ ] Code review by another team member
- [ ] Documentation updated
- [ ] Performance impact assessed

### Integration Testing
- [ ] Cross-team integration tests
- [ ] API contract validation
- [ ] State management consistency
- [ ] Error handling verification
- [ ] Performance benchmarks met

## Rollback Procedures

### Individual Team Rollback
1. Team identifies issue
2. Notifies dependent teams
3. Executes rollback plan
4. Updates integration status

### Full Rollback
1. Any team can trigger full rollback
2. All teams revert to last stable state
3. Emergency meeting scheduled
4. Issue analysis and resolution plan

## Success Metrics

### Technical Metrics
- [ ] All API calls use v1 endpoints
- [ ] No hook duplication
- [ ] Components use consolidated hooks
- [ ] State management working correctly
- [ ] CrewAI agents operational
- [ ] E2E tests passing

### Performance Metrics
- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms
- [ ] Memory usage optimized
- [ ] No memory leaks
- [ ] Bundle size maintained or reduced

### Quality Metrics
- [ ] Test coverage > 80%
- [ ] No critical bugs
- [ ] Accessibility compliance
- [ ] Cross-browser compatibility
- [ ] Mobile responsiveness

## Tools and Infrastructure

### Development Tools
- **Git**: Feature branches, pull requests
- **Docker**: Consistent development environment
- **Playwright**: E2E testing
- **Jest**: Unit testing
- **Storybook**: Component documentation

### Monitoring
- **Sentry**: Error tracking
- **Prometheus**: Metrics collection
- **Grafana**: Performance dashboards
- **Lighthouse**: Performance audits

## Documentation Requirements

### Each Team Must Provide
1. **API Documentation**: Endpoints, parameters, responses
2. **Component Documentation**: Props, usage examples
3. **Testing Documentation**: Test cases, coverage reports
4. **Deployment Guide**: Environment setup, configuration
5. **Troubleshooting Guide**: Common issues and solutions

### Shared Documentation
- **Integration Guide**: How teams work together
- **Architecture Overview**: System design
- **Migration Guide**: Upgrading from old system
- **User Guide**: Feature documentation

## Final Integration Checklist

### Pre-Production
- [ ] All team milestones complete
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Rollback procedures tested

### Production Deployment
- [ ] Feature flags configured
- [ ] Monitoring enabled
- [ ] Support team trained
- [ ] Rollback plan ready
- [ ] Success metrics defined

### Post-Deployment
- [ ] Performance monitoring
- [ ] Error rate tracking
- [ ] User feedback collection
- [ ] Issue resolution process
- [ ] Continuous improvement plan

## Contact Information

### Team Leads
- **Alpha Team**: alpha-lead@company.com
- **Beta Team**: beta-lead@company.com
- **Gamma Team**: gamma-lead@company.com
- **Delta Team**: delta-lead@company.com
- **Epsilon Team**: epsilon-lead@company.com
- **Zeta Team**: zeta-lead@company.com

### Project Management
- **Project Manager**: pm-revamp@company.com
- **Technical Lead**: tech-lead@company.com
- **QA Lead**: qa-lead@company.com

### Support
- **DevOps**: devops-team@company.com
- **Security**: security-team@company.com
- **Infrastructure**: infra-team@company.com

---

**Remember**: This is a coordinated effort. Success depends on clear communication, adherence to standards, and mutual support between teams. When in doubt, ask for help!