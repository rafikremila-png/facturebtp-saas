import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import ErrorBoundary from "@/components/ErrorBoundary";
import ImpersonationBanner from "@/components/ImpersonationBanner";

// Pages
import LoginPage from "@/pages/LoginPage";
import LandingPage from "@/pages/LandingPage";
import PricingPage from "@/pages/PricingPage";
import DashboardPage from "@/pages/DashboardPage";
import ClientsPage from "@/pages/ClientsPage";
import ClientFormPage from "@/pages/ClientFormPage";
import QuotesPage from "@/pages/QuotesPage";
import QuoteFormPage from "@/pages/QuoteFormPage";
import QuoteDetailPage from "@/pages/QuoteDetailPage";
import InvoicesPage from "@/pages/InvoicesPage";
import InvoiceFormPage from "@/pages/InvoiceFormPage";
import InvoiceDetailPage from "@/pages/InvoiceViewPage";
import SettingsPage from "@/pages/SettingsPage";
import ClientViewPage from "@/pages/ClientViewPage";
import UsersPage from "@/pages/UsersPage";
import ProfilePage from "@/pages/ProfilePage";
import ServicesPage from "@/pages/ServicesPage";
import ServiceRequestsPage from "@/pages/ServiceRequestsPage";
import BillingPage from "@/pages/BillingPage";
import AdminMetricsPage from "@/pages/AdminMetricsPage";
import AdminAnalyticsPage from "@/pages/AdminAnalyticsPage";
import AIAssistantPage from "@/pages/AIAssistantPage";
import SignaturePage from "@/pages/SignaturePage";
import WorkLibraryPage from "@/pages/WorkLibraryPage";
import ProjectsPage from "@/pages/ProjectsPage";
import FinancialDashboardPage from "@/pages/FinancialDashboardPage";
import ClientPortalPage from "@/pages/ClientPortalPage";
import Layout from "@/components/Layout";

// Loading component with timeout indication
const LoadingScreen = ({ message = "Chargement..." }) => (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-4">
        <div className="spinner"></div>
        <p className="text-sm text-slate-500">{message}</p>
    </div>
);

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading, authReady, error } = useAuth();
    
    // Show error if auth failed
    if (error && !loading) {
        console.log('[ProtectedRoute] Auth error:', error);
    }
    
    // Show loading only while actually loading
    if (loading && !authReady) {
        return <LoadingScreen message="Vérification de l'authentification..." />;
    }
    
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    
    return children;
};

// Admin-only protected route
const AdminRoute = ({ children }) => {
    const { isAuthenticated, loading, authReady, isAdmin } = useAuth();
    
    if (loading && !authReady) {
        return <LoadingScreen message="Vérification des droits..." />;
    }
    
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    
    if (!isAdmin()) {
        return <Navigate to="/" replace />;
    }
    
    return children;
};

const PublicRoute = ({ children }) => {
    const { isAuthenticated, loading, authReady } = useAuth();
    
    if (loading && !authReady) {
        return <LoadingScreen />;
    }
    
    if (isAuthenticated) {
        return <Navigate to="/" replace />;
    }
    
    return children;
};

function AppRoutes() {
    return (
        <Routes>
            {/* Public Landing Pages */}
            <Route path="/accueil" element={<LandingPage businessType="general" />} />
            <Route path="/logiciel-facturation-electricien" element={<LandingPage businessType="electrician" />} />
            <Route path="/logiciel-facturation-plombier" element={<LandingPage businessType="plumber" />} />
            <Route path="/logiciel-facturation-peintre" element={<LandingPage businessType="painter" />} />
            <Route path="/logiciel-facturation-installateur-reseau" element={<LandingPage businessType="it_installer" />} />
            
            {/* Public Pricing Page */}
            <Route path="/tarifs" element={<PricingPage />} />
            
            {/* Public client view - no auth required */}
            <Route path="/client/:type/:token" element={<ClientViewPage />} />
            
            {/* Public signature page - no auth required */}
            <Route path="/signer/:token" element={<SignaturePage />} />
            
            {/* Public client portal - no auth required */}
            <Route path="/portal/:token" element={<ClientPortalPage />} />
            
            <Route path="/login" element={
                <PublicRoute>
                    <LoginPage />
                </PublicRoute>
            } />
            
            <Route path="/" element={
                <ProtectedRoute>
                    <Layout />
                </ProtectedRoute>
            }>
                <Route index element={<DashboardPage />} />
                <Route path="clients" element={<ClientsPage />} />
                <Route path="clients/new" element={<ClientFormPage />} />
                <Route path="clients/:id/edit" element={<ClientFormPage />} />
                <Route path="devis" element={<QuotesPage />} />
                <Route path="devis/new" element={<QuoteFormPage />} />
                <Route path="devis/:id" element={<QuoteDetailPage />} />
                <Route path="devis/:id/edit" element={<QuoteFormPage />} />
                <Route path="factures" element={<InvoicesPage />} />
                <Route path="factures/new" element={<InvoiceFormPage />} />
                <Route path="factures/:id" element={<InvoiceDetailPage />} />
                <Route path="factures/:id/edit" element={<InvoiceFormPage />} />
                <Route path="parametres" element={<SettingsPage />} />
                <Route path="services" element={<ServicesPage />} />
                <Route path="facturation" element={<BillingPage />} />
                <Route path="finances" element={<FinancialDashboardPage />} />
                <Route path="ai-assistant" element={<AIAssistantPage />} />
                <Route path="bibliotheque" element={<WorkLibraryPage />} />
                <Route path="chantiers" element={<ProjectsPage />} />
                <Route path="utilisateurs" element={<UsersPage />} />
                <Route path="demandes-services" element={
                    <AdminRoute>
                        <ServiceRequestsPage />
                    </AdminRoute>
                } />
                <Route path="admin/metrics" element={
                    <AdminRoute>
                        <AdminMetricsPage />
                    </AdminRoute>
                } />
                <Route path="admin/analytics" element={
                    <AdminRoute>
                        <AdminAnalyticsPage />
                    </AdminRoute>
                } />
                <Route path="profil" element={<ProfilePage />} />
            </Route>
        </Routes>
    );
}

function App() {
    return (
        <ErrorBoundary>
            <AuthProvider>
                <BrowserRouter>
                    <ImpersonationBanner />
                    <AppRoutes />
                    <Toaster position="top-right" richColors />
                </BrowserRouter>
            </AuthProvider>
        </ErrorBoundary>
    );
}

export default App;
