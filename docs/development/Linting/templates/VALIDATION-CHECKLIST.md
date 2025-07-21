# AI Agent Validation Checklist

## Overview
This checklist ensures all AI agents maintain quality standards and avoid breaking changes while eliminating ESLint errors. Each agent must complete all applicable checklist items before marking their work as complete.

## Pre-Task Setup Validation

### Environment Setup
- [ ] **Git branch created**: Agent has dedicated branch (`lint/agent-[A-H]-[task-description]`)
- [ ] **Dependencies current**: `npm install` completed successfully
- [ ] **Baseline established**: Initial ESLint error count documented
- [ ] **Shared types available**: Access to `/docs/development/Linting/artifacts/SHARED-TYPE-DEFINITIONS.ts`
- [ ] **Target files identified**: All files in scope are accessible and readable

### Task Understanding
- [ ] **Template reviewed**: Agent-specific template from AGENT-TASK-TEMPLATES.md understood
- [ ] **Success criteria clear**: Specific error count reduction target identified
- [ ] **Scope defined**: Exact files and patterns to address documented
- [ ] **Dependencies mapped**: Understanding of which other agents' work may be needed
- [ ] **Escalation path**: Know when and how to escalate issues

## During-Task Validation (Per File)

### Before Making Changes
- [ ] **File analysis**: Understand current usage patterns of any-type in file
- [ ] **Impact assessment**: Identify all code that uses the types being modified
- [ ] **Import review**: Check existing imports and determine new import needs
- [ ] **Backup created**: Git commit with current state before changes

### Type Implementation
- [ ] **Shared types used**: Prefer shared types from artifacts/ over creating new ones
- [ ] **Proper imports**: All new type imports are correctly specified
- [ ] **Naming consistency**: New interfaces follow existing naming conventions
- [ ] **Generic constraints**: Generic types have appropriate constraints where needed
- [ ] **Documentation added**: Complex types have JSDoc comments

### Code Quality
- [ ] **No hardcoded values**: Avoid magic strings/numbers in type definitions
- [ ] **Union types**: Use union types for known value sets instead of string
- [ ] **Optional vs required**: Carefully consider which properties should be optional
- [ ] **Backwards compatibility**: Existing code using these types still compiles

## Compilation Validation

### TypeScript Compilation
- [ ] **Clean build**: `npm run typecheck` passes without errors
- [ ] **No new errors**: TypeScript compilation doesn't introduce new issues
- [ ] **Generic resolution**: Generic types resolve correctly in all usage contexts
- [ ] **Import resolution**: All new imports resolve successfully
- [ ] **Type inference**: TypeScript can properly infer types where expected

### ESLint Validation
- [ ] **Target errors reduced**: Specific any-type errors in scope are eliminated
- [ ] **No new violations**: No new ESLint errors introduced
- [ ] **Rule compliance**: Changes follow all other ESLint rules
- [ ] **Import organization**: Imports follow project import ordering rules

## Functional Validation

### Runtime Behavior
- [ ] **No breaking changes**: Existing functionality works as before
- [ ] **API compatibility**: API endpoints continue to accept/return expected data
- [ ] **Form handling**: Form submissions and validation work correctly
- [ ] **Event handlers**: Component event handlers function properly
- [ ] **State management**: Hook state updates work as expected

### Development Experience  
- [ ] **IntelliSense improved**: Better autocomplete and type hints
- [ ] **Error messaging**: Clear TypeScript errors when types are misused
- [ ] **Refactoring safety**: Types prevent common refactoring errors
- [ ] **Documentation clarity**: Type definitions are self-documenting

## Cross-Agent Compatibility

### Type Consistency
- [ ] **Interface alignment**: Types align with other agents' work where they intersect
- [ ] **Import coordination**: No conflicting type definitions across agents
- [ ] **Naming conflicts**: No type name collisions with other agents
- [ ] **Shared type usage**: Consistent use of shared types across agents

### Merge Preparation
- [ ] **Conflict resolution**: Any merge conflicts resolved before completion
- [ ] **Branch updated**: Branch rebased on latest main if needed
- [ ] **Commit organization**: Clean, logical commit structure
- [ ] **Branch naming**: Follows naming convention for easy identification

## Testing Validation

### Automated Tests
- [ ] **Test compilation**: All test files compile without TypeScript errors
- [ ] **Test execution**: Full test suite runs successfully (`npm run test:run`)
- [ ] **Type safety**: Tests properly use new type definitions
- [ ] **Mock compatibility**: Mocked objects conform to new interfaces

### Manual Verification
- [ ] **Critical paths**: Key user workflows tested manually
- [ ] **Form submissions**: Forms using updated types work correctly
- [ ] **API interactions**: API calls with new types function properly
- [ ] **Error handling**: Error scenarios handle new types correctly

## Performance Validation

### Build Performance
- [ ] **Compilation time**: TypeScript compilation time not significantly increased
- [ ] **Bundle size**: No unexpected increases in bundle size
- [ ] **Memory usage**: TypeScript compilation memory usage within limits
- [ ] **IDE performance**: No noticeable degradation in IDE responsiveness

### Runtime Performance
- [ ] **No runtime overhead**: Type changes don't affect runtime performance  
- [ ] **Memory leaks**: No new memory leaks introduced
- [ ] **Rendering speed**: Component rendering speed maintained
- [ ] **API response time**: No degradation in API response handling speed

## Documentation & Communication

### Code Documentation
- [ ] **Type documentation**: Complex types have clear JSDoc comments
- [ ] **Usage examples**: Non-obvious type usage documented with examples
- [ ] **Migration notes**: Breaking changes documented with migration guidance
- [ ] **Rationale captured**: Reasons for type design decisions documented

### Progress Communication
- [ ] **Tracker updated**: Progress tracker reflects current status
- [ ] **Issues logged**: Any issues encountered documented in tracker
- [ ] **Dependencies noted**: Dependencies on other agents' work documented
- [ ] **Completion reported**: Final status reported with metrics

## Final Validation

### Quality Assurance
- [ ] **All files processed**: Every file in scope has been addressed
- [ ] **Error count verified**: Actual error reduction matches target
- [ ] **Regression testing**: No functionality regressions identified
- [ ] **Security implications**: No security vulnerabilities introduced

### Handoff Preparation
- [ ] **Work summary**: Clear summary of changes made prepared
- [ ] **Known issues**: Any remaining issues or limitations documented
- [ ] **Follow-up tasks**: Any needed follow-up work identified
- [ ] **Review readiness**: Code ready for peer review

## Escalation Triggers

### When to Escalate
Immediately escalate to project coordination if:
- TypeScript compilation fails and can't be resolved within 30 minutes
- Breaking changes to existing functionality discovered
- Conflicts with other agents' work that can't be resolved
- Target error count can't be achieved due to complex type requirements
- Performance degradation beyond acceptable limits
- Security concerns identified during type implementation

### Escalation Process
1. **Stop work**: Pause current task to avoid making situation worse
2. **Document issue**: Clearly describe the problem and attempted solutions
3. **Update tracker**: Mark task as blocked with issue description
4. **Notify coordinator**: Send escalation notification with details
5. **Await guidance**: Don't proceed until receiving guidance from coordinator

## Success Criteria

### Quantitative Measures
- [ ] **Target error reduction**: Achieved specific any-type error reduction target
- [ ] **No regressions**: Zero new TypeScript or ESLint errors introduced
- [ ] **Performance maintained**: No significant degradation in build or runtime performance
- [ ] **Test coverage**: All tests pass with new type definitions

### Qualitative Measures
- [ ] **Type safety improved**: Better compile-time error detection
- [ ] **Developer experience**: Improved IntelliSense and type hints
- [ ] **Code maintainability**: More self-documenting and refactoring-safe code
- [ ] **Standards compliance**: Consistent with project TypeScript patterns

---

## Checklist Usage Instructions

### For Individual Agents
1. Print or bookmark this checklist for reference
2. Complete each applicable section in order
3. Check off items as you complete them
4. Don't skip validation steps even if they seem minor
5. Escalate immediately if you encounter blocking issues

### For Project Coordinators
1. Review completed checklists before approving agent work
2. Use checklist as basis for code review
3. Verify quantitative targets are met
4. Ensure proper escalation process followed when needed

### For Quality Assurance
1. Use checklist as validation framework
2. Spot-check completed items during reviews
3. Verify testing procedures were followed
4. Confirm documentation standards met

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-21  
**Next Review**: After Phase 1 completion  
**Approval Required**: Project Lead, Technical Lead