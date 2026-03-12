import { useState, useEffect } from "react";
import { AlertTriangle, Clock, Zap, X, ChevronRight, FileText, Receipt } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import api from "@/lib/api";

export default function TrialBanner() {
    const [trialData, setTrialData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
        fetchTrialStatus();
    }, []);

    const fetchTrialStatus = async () => {
        try {
            const response = await api.get("/trial/status");
            setTrialData(response.data);
        } catch (error) {
            console.error("Error fetching trial status:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading || dismissed || !trialData) return null;

    // Don't show banner for super admin or active subscriptions
    if (trialData.user_role === "super_admin" || trialData.subscription_active) {
        return null;
    }

    const { 
        is_trial, 
        trial_days_remaining, 
        trial_expired,
        quotes_count,
        quote_limit,
        invoices_count,
        invoice_limit,
        banner 
    } = trialData;

    // Calculate percentages for progress bars
    const quotesPercent = Math.min(100, (quotes_count / quote_limit) * 100);
    const invoicesPercent = Math.min(100, (invoices_count / invoice_limit) * 100);

    // Determine banner style based on status
    const getBannerStyle = () => {
        if (trial_expired) {
            return "bg-red-50 border-red-200 text-red-800";
        }
        if (trial_days_remaining <= 2) {
            return "bg-amber-50 border-amber-200 text-amber-800";
        }
        return "bg-blue-50 border-blue-200 text-blue-800";
    };

    const getIconColor = () => {
        if (trial_expired) return "text-red-500";
        if (trial_days_remaining <= 2) return "text-amber-500";
        return "text-blue-500";
    };

    const getProgressColor = (percent) => {
        if (percent >= 100) return "bg-red-500";
        if (percent >= 80) return "bg-amber-500";
        return "bg-blue-500";
    };

    return (
        <div className="space-y-3 mb-6">
            {/* Trial Status Banner */}
            <div className={`relative rounded-lg border p-4 ${getBannerStyle()}`}>
                <button
                    onClick={() => setDismissed(true)}
                    className="absolute top-2 right-2 opacity-50 hover:opacity-100 transition-opacity"
                >
                    <X className="w-4 h-4" />
                </button>

                <div className="flex items-start gap-3">
                    <div className={`mt-0.5 ${getIconColor()}`}>
                        {trial_expired ? (
                            <AlertTriangle className="w-5 h-5" />
                        ) : trial_days_remaining <= 2 ? (
                            <Clock className="w-5 h-5" />
                        ) : (
                            <Zap className="w-5 h-5" />
                        )}
                    </div>

                    <div className="flex-1">
                        <h3 className="font-semibold text-sm">
                            {trial_expired 
                                ? "Période d'essai expirée" 
                                : `Essai gratuit - ${trial_days_remaining} jour${trial_days_remaining > 1 ? 's' : ''} restant${trial_days_remaining > 1 ? 's' : ''}`
                            }
                        </h3>
                        <p className="text-sm mt-1 opacity-90">
                            {trial_expired
                                ? "Votre période d'essai est terminée. Passez à un abonnement pour continuer à utiliser toutes les fonctionnalités."
                                : `Profitez de votre essai gratuit avec ${quote_limit} devis et ${invoice_limit} factures.`
                            }
                        </p>

                        {(trial_expired || trial_days_remaining <= 3) && (
                            <Button
                                size="sm"
                                className="mt-3 bg-orange-600 hover:bg-orange-700 text-white"
                                onClick={() => window.location.href = "/settings/subscription"}
                            >
                                Passer à l'abonnement
                                <ChevronRight className="w-4 h-4 ml-1" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            {/* Usage Limits Banner */}
            {is_trial && !trial_expired && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-700 mb-3">
                        Utilisation pendant l'essai
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Quotes Usage */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2 text-slate-600">
                                    <FileText className="w-4 h-4" />
                                    <span>Devis</span>
                                </div>
                                <span className={`font-medium ${quotesPercent >= 100 ? 'text-red-600' : 'text-slate-700'}`}>
                                    {quotes_count} / {quote_limit}
                                </span>
                            </div>
                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                <div 
                                    className={`h-full transition-all duration-300 ${getProgressColor(quotesPercent)}`}
                                    style={{ width: `${quotesPercent}%` }}
                                />
                            </div>
                            {quotesPercent >= 100 && (
                                <p className="text-xs text-red-600">Limite atteinte</p>
                            )}
                        </div>

                        {/* Invoices Usage */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2 text-slate-600">
                                    <Receipt className="w-4 h-4" />
                                    <span>Factures</span>
                                </div>
                                <span className={`font-medium ${invoicesPercent >= 100 ? 'text-red-600' : 'text-slate-700'}`}>
                                    {invoices_count} / {invoice_limit}
                                </span>
                            </div>
                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                                <div 
                                    className={`h-full transition-all duration-300 ${getProgressColor(invoicesPercent)}`}
                                    style={{ width: `${invoicesPercent}%` }}
                                />
                            </div>
                            {invoicesPercent >= 100 && (
                                <p className="text-xs text-red-600">Limite atteinte</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
