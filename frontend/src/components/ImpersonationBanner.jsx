import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { X, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";
import { toast } from "sonner";

export default function ImpersonationBanner() {
    const { token, logout } = useAuth();
    const [impersonationStatus, setImpersonationStatus] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        checkImpersonationStatus();
    }, [token]);

    const checkImpersonationStatus = async () => {
        if (!token) return;
        
        try {
            const response = await api.get("/auth/impersonation-status");
            setImpersonationStatus(response.data);
        } catch (error) {
            // Not in impersonation mode or error
            setImpersonationStatus({ is_impersonated: false });
        }
    };

    const handleStopImpersonation = async () => {
        setLoading(true);
        try {
            const response = await api.post("/admin/stop-impersonation");
            
            // Update token with admin token
            localStorage.setItem("token", response.data.access_token);
            
            toast.success("Session d'usurpation terminée");
            
            // Reload page to refresh auth state
            window.location.reload();
        } catch (error) {
            toast.error("Erreur lors de la fin de session");
        } finally {
            setLoading(false);
        }
    };

    if (!impersonationStatus?.is_impersonated) {
        return null;
    }

    return (
        <div 
            className="fixed top-0 left-0 right-0 z-50 bg-amber-500 text-amber-950 py-2 px-4 flex items-center justify-center gap-4 shadow-lg"
            data-testid="impersonation-banner"
        >
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">
                Mode Support Actif - Vous êtes connecté en tant que{" "}
                <strong>{impersonationStatus.user_name}</strong> ({impersonationStatus.user_email})
            </span>
            <Button
                variant="outline"
                size="sm"
                onClick={handleStopImpersonation}
                disabled={loading}
                className="bg-white hover:bg-amber-100 text-amber-900 border-amber-700"
                data-testid="stop-impersonation-btn"
            >
                <X className="w-4 h-4 mr-1" />
                Quitter le mode
            </Button>
        </div>
    );
}
