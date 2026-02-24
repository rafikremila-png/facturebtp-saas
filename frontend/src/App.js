import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import ErrorBoundary from "@/components/ErrorBoundary";
import ImpersonationBanner from "@/components/ImpersonationBanner";

// Pages
import LoginPage from "@/pages/LoginPage";
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
import Layout from "@/components/Layout";

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="spinner"></div>
            </div>
        );
    }
    
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }
    
    return children;
};

// Admin-only protected route
const AdminRoute = ({ children }) => {
    const { isAuthenticated, loading, isAdmin } = useAuth();
    
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="spinner"></div>
            </div>
        );
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
    const { isAuthenticated, loading } = useAuth();
    
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="spinner"></div>
            </div>
        );
    }
    
    if (isAuthenticated) {
        return <Navigate to="/" replace />;
    }
    
    return children;
};

function AppRoutes() {
    return (
        <Routes>
            {/* Public client view - no auth required */}
            <Route path="/client/:type/:token" element={<ClientViewPage />} />
            
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
                <Route path="utilisateurs" element={<UsersPage />} />
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
