import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider } from "./contexts/AuthContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import { SessionProvider } from "./contexts/SessionContext";
import { useAuth } from "./contexts/AuthContext";

// Lazy-loaded components
const PageLoader = () => <div>Loading...</div>;
const LoginPage = lazy(() => import('./pages/Login'));
const SessionSelectionPage = lazy(() => import('./components/session/SessionSelector'));
const AssetInventoryPage = lazy(() => import('./pages/discovery/Inventory'));
const CMDBImport = lazy(() => import('./pages/discovery/CMDBImport'));
const AttributeMappingPage = lazy(() => import('./pages/discovery/AttributeMapping'));
const AssessmentReadinessPage = lazy(() => import('./pages/discovery/AssessmentReadiness'));
const DataCleansingPage = lazy(() => import('./pages/discovery/DataCleansing'));
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const UserApprovals = lazy(() => import('./pages/admin/UserApprovals'));
const ClientManagement = lazy(() => import('./pages/admin/ClientManagement'));
const EngagementManagement = lazy(() => import('./pages/admin/EngagementManagement'));
const EngagementCreation = lazy(() => import('./pages/admin/CreateEngagement'));
const SessionComparison = lazy(() => import('./components/admin/session-comparison/SessionComparisonMain'));
const PlatformAdmin = lazy(() => import('./pages/admin/PlatformAdmin'));
const NotFoundPage = lazy(() => import('./pages/NotFound'));
const DiscoveryDashboard = lazy(() => import('./pages/discovery/DiscoveryDashboard'));
const IndexPage = lazy(() => import('./pages/Index'));
const ProtectedRoute = () => {
    const { isAuthenticated, isLoading } = useAuth();
    if (isLoading) {
        return <div>Loading...</div>;
    }
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    return <Outlet />;
};

const App = () => (
    <AuthProvider>
        <SessionProvider>
            <ChatFeedbackProvider>
                <TooltipProvider>
                    <Toaster />
                    <Sonner />
                    <Suspense fallback={<PageLoader />}>
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/session/select" element={<SessionSelectionPage />} />

                            <Route element={<ProtectedRoute />}>
                                <Route path="/" element={<IndexPage />} />
                                
                                <Route path="/discovery" element={<DiscoveryDashboard />} />
                                <Route path="/discovery/assessment" element={<AssessmentReadinessPage />} />
                                <Route path="/discovery/asset-inventory" element={<AssetInventoryPage />} />
                                <Route path="/discovery/inventory" element={<AssetInventoryPage />} />
                                <Route path="/discovery/import" element={<CMDBImport />} />
                                <Route path="/discovery/attribute-mapping" element={<AttributeMappingPage />} />
                                <Route path="/discovery/assessment-readiness" element={<AssessmentReadinessPage />} />
                                <Route path="/discovery/data-cleansing/:fileId" element={<DataCleansingPage />} />

                                <Route path="/admin/dashboard" element={<AdminDashboard />} />
                                <Route path="/admin/user-approvals" element={<UserApprovals />} />
                                <Route path="/admin/client-management" element={<ClientManagement />} />
                                <Route path="/admin/engagements" element={<EngagementManagement />} />
                                <Route path="/admin/engagements/new" element={<EngagementCreation />} />
                                <Route path="/admin/sessions" element={<SessionComparison />} />
                                <Route path="/admin/platform" element={<PlatformAdmin />} />
                                
                                <Route path="/plan/*" element={<div>Plan Section</div>} />
                                <Route path="/execute/*" element={<div>Execute Section</div>} />
                                <Route path="/modernize/*" element={<div>Modernize Section</div>} />
                                <Route path="/assess/*" element={<div>Assess Section</div>} />
                                <Route path="/finops/*" element={<div>FinOps Section</div>} />
                                <Route path="/decommission/*" element={<div>Decommission Section</div>} />
                            </Route>

                            <Route path="*" element={<NotFoundPage />} />
                        </Routes>
                    </Suspense>
                    <GlobalChatFeedback />
                </TooltipProvider>
            </ChatFeedbackProvider>
        </SessionProvider>
    </AuthProvider>
);

export default App;
