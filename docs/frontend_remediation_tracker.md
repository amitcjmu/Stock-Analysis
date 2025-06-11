# Frontend Remediation Plan & Progress Tracker

_Last updated: 2025-06-11 10:30 EDT_

## Main Remediation Tasks
1. **Replace useEffect API fetching with TanStack Query hooks**
2. **Move server state from useState to React Query**
3. **Replace direct localStorage access for context/session/engagement IDs with useAuth functions**
4. **Refactor/remove all useAppContext usage in components**

## Cleanup Progress (2025-06-11)
- ✅ Removed legacy files:
  - `/src/pages/discovery/AssessmentReadiness.old.tsx`
  - `/src/pages/discovery/DataCleansing.legacy.tsx`
  - `/src/pages/discovery/Scan.legacy.tsx`
  - `/src/pages/discovery/TechDebtAnalysis.legacy.tsx`
  - `/src/hooks/useDataCleansing.legacy.ts`
- ✅ Removed duplicate files:
  - `/src/api/hooks/useInventory.ts`
  - `/src/hooks/useInventoryData.ts`
- ✅ Removed old directory structure:
  - `/src/pages/discovery/assessment-readiness/` (entire directory)
  - `/src/api/hooks/` (consolidated into `/src/hooks/`)
- ✅ Kept complementary files that work together:
  - `useApplication.ts` and `useApplications.ts` (serve different purposes)

---

## Progress Table (Exhaustive)

| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/admin/AdminDashboard.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/admin/EngagementDetails.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/admin/ClientDetails.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/admin/CreateClient.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/admin/CreateUser.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/admin/UserProfile.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/discovery/Dependencies.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/discovery/Inventory.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/discovery/DiscoveryDashboard.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/discovery/AttributeMapping.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/AssetInventoryRedesigned.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/CMDBImport.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/DataCleansing.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/Scan.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/TechDebtAnalysis.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/AssessmentReadiness.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/discovery/inventory/hooks/useInventory.ts` | ✅ | ✅ | N/A | N/A | Complete |
| `/src/pages/assess/Index.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
### Group 1 – Assess
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/assess/Treatment.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/assess/Editor.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/assess/Roadmap.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/assess/WavePlanning.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

### Group 2 – Decommission
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/decommission/DataRetention.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/decommission/Archival.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/decommission/Compliance.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/decommission/Verification.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

### Group 3 – Execute
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/execute/Cutovers.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/execute/Rehost.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/execute/Replatform.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/execute/Reports.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

### Group 4 – FinOps
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/finops/Overview.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/BudgetAlerts.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/CloudComparison.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/CostAnalysis.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/CostTrends.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/LLMCosts.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/SavingsAnalysis.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/finops/WaveBreakdown.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

All pages in Group 4 (FinOps) have been successfully modernized with TanStack Query, proper authentication, and removal of useAppContext.

### Group 5 – Modernize
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/modernize/Progress.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/modernize/Rearchitect.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/pages/modernize/Refactor.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/modernize/Rewrite.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

### Group 6 – Plan
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/pages/plan/Resource.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/plan/Target.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/pages/plan/Timeline.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |

### Shared Components
| File | useEffect→Query | useState→Query | localStorage→useAuth | Remove useAppContext | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| `/src/components/AgentMonitor.tsx` | ✅ | ✅ | N/A | ✅ | Complete |
| `/src/components/FeedbackWidget.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/components/GlobalChatFeedback.tsx` | ✅ | ✅ | ✅ | ✅ | Complete |
| `/src/contexts/AuthContext.tsx` | N/A | N/A | ⬜ | ⬜ | Pending |
| `/src/contexts/SessionContext.tsx` | N/A | N/A | ⬜ | ⬜ | Pending |
| `/src/contexts/ClientContext.tsx` | N/A | N/A | ⬜ | ⬜ | Pending |
| `/src/contexts/EngagementContext.tsx` | N/A | N/A | ⬜ | ⬜ | Pending |
| `/src/hooks/useContext.tsx` | N/A | N/A | ✅ | ✅ | Complete |

Legend: ✅ = Complete, ⬜ = Pending, N/A = Not Applicable

---

## Next Steps
- Continue remediation in the specified group and file order:
  1. Assess
  2. Decommission
  3. Execute
  4. FinOps
  5. Modernize
  6. Plan
  7. Shared Components
  8. Context Cleanup
- This tracker will be updated as each file is refactored.
- See codebase and commit history for detailed changes per file.

---

If you have questions or want to prioritize a specific file, please comment here or in the main audit report.
