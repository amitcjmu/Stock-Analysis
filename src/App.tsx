import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ChatFeedbackProvider } from "./contexts/ChatFeedbackContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ClientProvider, useClient } from "./contexts/ClientContext";
import GlobalChatFeedback from "./components/GlobalChatFeedback";
import { SessionProvider } from "./contexts/SessionContext";

// Layouts
import MainLayout from './components/MainLayout';

// Lazy-loaded components
const PageLoader = () => <div className="flex h-screen w-full items-center justify-center"><div className="text-xl font-semibold">Loading Platform...</div></div>;
const LoginPage = lazy(() => import("./pages/Login"));
const SessionSelectionPage = lazy(() => import("./components/session/SessionSelector"));
const AssetInventoryPage = lazy(() => import("./pages/discovery/Inventory"));
const CMDBImport = lazy(() => import("./pages/discovery/CMDBImport"));
const AttributeMappingPage = lazy(() => import("./pages/discovery/AttributeMapping"));
const DataCleansingPage = lazy(() => import("./pages/discovery/DataCleansing"));
const DependencyAnalysisPage = lazy(() => import("./pages/discovery/DependencyAnalysis"));
const TechDebtAnalysisPage = lazy(() => import("./pages/discovery/TechDebtAnalysis"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const UserApprovals = lazy(() => import("./pages/admin/UserApprovals"));
const ClientManagement = lazy(() => import("./pages/admin/ClientManagement"));
const EngagementManagement = lazy(() => import("./pages/admin/EngagementManagement"));
const EngagementCreation = lazy(() => import("./pages/admin/CreateEngagement"));
const SessionComparison = lazy(() => import("./components/admin/session-comparison/SessionComparisonMain"));
const PlatformAdmin = lazy(() => import("./pages/admin/PlatformAdmin"));
const NotFoundPage = lazy(() => import("./pages/NotFound"));
const DiscoveryDashboard = lazy(() => import("./pages/discovery/DiscoveryDashboard"));
const IndexPage = lazy(() => import("./pages/Index"));
const Assess = lazy(() => import("./pages/Assess"));
const Plan = lazy(() => import("./pages/Plan"));
const ExecuteIndex = lazy(() => import("./pages/execute/Index"));
const Replatform = lazy(() => import("./pages/execute/Replatform"));
const ModernizeIndex = lazy(() => import("./pages/modernize/Index"));
const Rearchitect = lazy(() => import("./pages/modernize/Rearchitect"));
const FinOps = lazy(() => import("./pages/FinOps"));
const DecommissionIndex = lazy(() => import("./pages/decommission/Index"));
const DecommissionPlanning = lazy(() => import("./pages/decommission/Planning"));
const DecommissionExecution = lazy(() => import("./pages/decommission/Execution"));

const ProtectedRoute = () => {
    const { user, isLoading: authLoading } = useAuth();
    const { currentClient, isLoading: clientLoading } = useClient();
    
    // First check if we're still loading
    if (authLoading || clientLoading) {
        return <PageLoader />;
    }
    
    // Then check authentication - this must be first!
    if (!user) {
        return <Navigate to="/login" replace />;
    }
    
    // Only check client context if user is authenticated
    if (user.role === 'admin' && !currentClient && !window.location.pathname.startsWith('/admin')) {
        return <Navigate to="/admin/dashboard" replace />;
    }
    
    if (user.role !== 'admin' && !currentClient) {
        return <Navigate to="/session/select" replace />;
    }
    
    return <Outlet />;
};

const AdminRoute = () => {
    const { user, isLoading } = useAuth();
    
    if (isLoading) {
        return <PageLoader />;
    }
    
    if (!user || user.role !== 'admin') {
        return <Navigate to="/" replace />;
    }
    
    return <Outlet />;
};

const DemoBanner = () => {
    const { isDemoMode } = useAuth();
    if (!isDemoMode) return null;
    return (
        <div style={{ background: '#ffecb3', color: '#b26a00', padding: '8px', textAlign: 'center', fontWeight: 'bold', zIndex: 1000 }}>
            <span>Demo Mode</span>: You are exploring the app with demo data. Some features may be read-only or simulated.
        </div>
    );
};

const App = () => {
    return (
        <AuthProvider>
            <ClientProvider>
                <SessionProvider>
                    <ChatFeedbackProvider>
                        <TooltipProvider>
                            <DemoBanner />
                            <Toaster />
                            <Sonner />
                            <Suspense fallback={<PageLoader />}>
                                <Routes>
                                    <Route path="/login" element={<LoginPage />} />
                                    <Route path="/session/select" element={<SessionSelectionPage />} />

                                    {/* Main application routes with sidebar and nav */}
                                    <Route element={<ProtectedRoute />}>
                                        <Route element={<MainLayout />}>
                                            <Route path="/" element={<IndexPage />} />
                                            
                                            {/* Discovery Module */}
                                            <Route path="/discovery" element={<Navigate to="/discovery/overview" replace />} />
                                            <Route path="/discovery/overview" element={<DiscoveryDashboard />} />
                                            <Route path="/discovery/import" element={<CMDBImport />} />
                                            <Route path="/discovery/inventory" element={<AssetInventoryPage />} />
                                            <Route path="/discovery/attribute-mapping" element={<AttributeMappingPage />} />
                                            <Route path="/discovery/data-cleansing" element={<DataCleansingPage />} />
                                            <Route path="/discovery/dependencies" element={<DependencyAnalysisPage />} />
                                            <Route path="/discovery/tech-debt" element={<TechDebtAnalysisPage />} />

                                            {/* Other Main Modules */}
                                            <Route path="/plan" element={<Plan />} />
                                            <Route path="/execute" element={<ExecuteIndex />} />
                                            <Route path="/execute/replatform" element={<Replatform />} />
                                            <Route path="/modernize" element={<ModernizeIndex />} />
                                            <Route path="/modernize/rearchitect" element={<Rearchitect />} />
                                            <Route path="/assess" element={<Assess />} />
                                            <Route path="/finops" element={<FinOps />} />
                                            <Route path="/decommission" element={<DecommissionIndex />} />
                                            <Route path="/decommission/planning" element={<DecommissionPlanning />} />
                                            <Route path="/decommission/execution" element={<DecommissionExecution />} />
                                        </Route>
                                    </Route>

                                    {/* Admin routes also use the main layout now */}
                                    <Route element={<AdminRoute />}>
                                        <Route element={<MainLayout />}>
                                            <Route path="/admin/dashboard" element={<AdminDashboard />} />
                                            <Route path="/admin/user-approvals" element={<UserApprovals />} />
                                            <Route path="/admin/client-management" element={<ClientManagement />} />
                                            <Route path="/admin/engagements" element={<EngagementManagement />} />
                                            <Route path="/admin/engagements/new" element={<EngagementCreation />} />
                                            <Route path="/admin/sessions" element={<SessionComparison />} />
                                            <Route path="/admin/platform" element={<PlatformAdmin />} />
                                        </Route>
                                    </Route>

                                    <Route path="*" element={<NotFoundPage />} />
                                </Routes>
                            </Suspense>
                            <GlobalChatFeedback />
                        </TooltipProvider>
                    </ChatFeedbackProvider>
                </SessionProvider>
            </ClientProvider>
        </AuthProvider>
    );
};

export default App;