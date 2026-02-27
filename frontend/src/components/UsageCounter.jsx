import { useState, useEffect } from "react";
import { getUsageStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileText, TrendingUp, AlertTriangle, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function UsageCounter({ onUpgradeClick }) {
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchUsage();
    }, []);

    const fetchUsage = async () => {
        try {
            const response = await getUsageStats();
            setUsage(response.data);
        } catch (error) {
            console.error("Error fetching usage:", error);
        } finally {
            setLoading(false);
        }
    };

    const getProgressColor = (current, limit) => {
        if (limit === -1) return "bg-green-500"; // Unlimited
        const percentage = (current / limit) * 100;
        if (percentage >= 100) return "bg-red-500";
        if (percentage >= 70) return "bg-orange-500";
        return "bg-green-500";
    };

    const getProgressPercentage = (current, limit) => {
        if (limit === -1) return 10; // Show small bar for unlimited
        return Math.min(100, (current / limit) * 100);
    };

    const formatLimit = (limit) => {
        return limit === -1 ? "∞" : limit;
    };

    const handleUpgrade = () => {
        if (onUpgradeClick) {
            onUpgradeClick();
        } else {
            navigate("/tarifs");
        }
    };

    if (loading) {
        return (
            <Card className="animate-pulse">
                <CardContent className="py-6">
                    <div className="h-20 bg-slate-200 rounded" />
                </CardContent>
            </Card>
        );
    }

    if (!usage) {
        return null;
    }

    const quotePercentage = getProgressPercentage(usage.quote_usage, usage.quote_limit);
    const invoicePercentage = getProgressPercentage(usage.invoice_usage, usage.invoice_limit);
    const isQuoteLimitReached = usage.quote_limit !== -1 && usage.quote_usage >= usage.quote_limit;
    const isInvoiceLimitReached = usage.invoice_limit !== -1 && usage.invoice_usage >= usage.invoice_limit;
    const showUpgrade = isQuoteLimitReached || isInvoiceLimitReached || usage.is_trial;

    return (
        <Card className="border-slate-200" data-testid="usage-counter">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-slate-600" />
                        Utilisation ce mois
                    </CardTitle>
                    {usage.is_trial && usage.trial_days_remaining !== null && (
                        <Badge 
                            variant="outline" 
                            className="border-orange-300 text-orange-700 bg-orange-50"
                            data-testid="trial-badge"
                        >
                            <Clock className="w-3 h-3 mr-1" />
                            Essai : {usage.trial_days_remaining} jours restants
                        </Badge>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Quotes Usage */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-slate-600">
                            <FileText className="w-4 h-4" />
                            Devis utilisés
                        </span>
                        <span className={`font-medium ${isQuoteLimitReached ? 'text-red-600' : 'text-slate-900'}`}>
                            {usage.quote_usage} / {formatLimit(usage.quote_limit)}
                        </span>
                    </div>
                    <div className="relative">
                        <Progress 
                            value={quotePercentage} 
                            className="h-2"
                        />
                        <div 
                            className={`absolute top-0 left-0 h-2 rounded-full transition-all ${getProgressColor(usage.quote_usage, usage.quote_limit)}`}
                            style={{ width: `${quotePercentage}%` }}
                        />
                    </div>
                    {isQuoteLimitReached && (
                        <p className="text-xs text-red-600 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Limite atteinte
                        </p>
                    )}
                </div>

                {/* Invoices Usage */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-slate-600">
                            <FileText className="w-4 h-4" />
                            Factures utilisées
                        </span>
                        <span className={`font-medium ${isInvoiceLimitReached ? 'text-red-600' : 'text-slate-900'}`}>
                            {usage.invoice_usage} / {formatLimit(usage.invoice_limit)}
                        </span>
                    </div>
                    <div className="relative">
                        <Progress 
                            value={invoicePercentage} 
                            className="h-2"
                        />
                        <div 
                            className={`absolute top-0 left-0 h-2 rounded-full transition-all ${getProgressColor(usage.invoice_usage, usage.invoice_limit)}`}
                            style={{ width: `${invoicePercentage}%` }}
                        />
                    </div>
                    {isInvoiceLimitReached && (
                        <p className="text-xs text-red-600 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Limite atteinte
                        </p>
                    )}
                </div>

                {/* Upgrade CTA */}
                {showUpgrade && (
                    <div className="pt-2 border-t">
                        <Button 
                            className="w-full bg-orange-600 hover:bg-orange-700"
                            size="sm"
                            onClick={handleUpgrade}
                            data-testid="upgrade-btn"
                        >
                            {usage.is_trial ? "Passer au plan payant" : "Passer au plan supérieur"}
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
