import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { getSubscriptionPlans, getSubscriptionStatus, createCheckoutSession, checkCheckoutStatus, cancelSubscription } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { 
    CreditCard, Check, X, Crown, Zap, Building2, 
    AlertTriangle, Loader2, ArrowRight, Calendar,
    Users, Package, TrendingUp, Shield
} from "lucide-react";
import { toast } from "sonner";

const FEATURE_LABELS = {
    unlimited_quotes: "Devis illimités",
    max_invoices_per_month: "Factures par mois",
    basic_article_library: "Bibliothèque d'articles",
    manual_line_creation: "Création manuelle",
    max_users: "Utilisateurs",
    predefined_kits: "Kits prédéfinis",
    smart_pricing: "Prix intelligents",
    advanced_dashboard: "Statistiques avancées",
    priority_support: "Support prioritaire"
};

const PLAN_ICONS = {
    essentiel: Zap,
    pro: Crown,
    business: Building2
};

const PLAN_COLORS = {
    essentiel: "blue",
    pro: "orange",
    business: "purple"
};

export default function BillingPage() {
    const { user, refreshUser } = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    
    const [plans, setPlans] = useState([]);
    const [subscription, setSubscription] = useState(null);
    const [loading, setLoading] = useState(true);
    const [checkingPayment, setCheckingPayment] = useState(false);
    const [processingPlan, setProcessingPlan] = useState(null);
    const [showCancelDialog, setShowCancelDialog] = useState(false);
    const [canceling, setCanceling] = useState(false);

    useEffect(() => {
        loadData();
        checkPaymentReturn();
    }, []);

    const loadData = async () => {
        try {
            const [plansRes, statusRes] = await Promise.all([
                getSubscriptionPlans(),
                getSubscriptionStatus()
            ]);
            setPlans(plansRes.data);
            setSubscription(statusRes.data);
        } catch (error) {
            console.error("Error loading billing data:", error);
            toast.error("Erreur lors du chargement des données");
        } finally {
            setLoading(false);
        }
    };

    const checkPaymentReturn = async () => {
        const sessionId = searchParams.get("session_id");
        const success = searchParams.get("success");
        const canceled = searchParams.get("canceled");

        if (canceled) {
            toast.info("Paiement annulé");
            navigate("/facturation", { replace: true });
            return;
        }

        if (sessionId && success) {
            setCheckingPayment(true);
            try {
                // Poll for payment status
                let attempts = 0;
                const maxAttempts = 5;
                
                while (attempts < maxAttempts) {
                    const statusRes = await checkCheckoutStatus(sessionId);
                    
                    if (statusRes.data.payment_status === "paid") {
                        toast.success(`Abonnement ${statusRes.data.plan_name} activé !`);
                        await refreshUser();
                        await loadData();
                        navigate("/facturation", { replace: true });
                        return;
                    }
                    
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    attempts++;
                }
                
                toast.info("Paiement en cours de traitement...");
            } catch (error) {
                console.error("Payment check error:", error);
                toast.error("Erreur lors de la vérification du paiement");
            } finally {
                setCheckingPayment(false);
                navigate("/facturation", { replace: true });
            }
        }
    };

    const handleSelectPlan = async (planId) => {
        if (subscription?.plan === planId) {
            toast.info("Vous êtes déjà sur ce plan");
            return;
        }

        setProcessingPlan(planId);
        try {
            const originUrl = window.location.origin;
            const response = await createCheckoutSession(planId, originUrl);
            
            if (response.data.checkout_url) {
                window.location.href = response.data.checkout_url;
            }
        } catch (error) {
            console.error("Checkout error:", error);
            toast.error("Erreur lors de la création du paiement");
        } finally {
            setProcessingPlan(null);
        }
    };

    const handleCancelSubscription = async () => {
        setCanceling(true);
        try {
            await cancelSubscription();
            toast.success("Abonnement annulé");
            await loadData();
            await refreshUser();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de l'annulation");
        } finally {
            setCanceling(false);
            setShowCancelDialog(false);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleDateString("fr-FR", {
            day: "numeric",
            month: "long",
            year: "numeric"
        });
    };

    const renderFeatureValue = (key, value) => {
        if (typeof value === "boolean") {
            return value ? (
                <Check className="w-4 h-4 text-green-600" />
            ) : (
                <X className="w-4 h-4 text-slate-300" />
            );
        }
        if (key === "max_invoices_per_month") {
            return value === -1 ? "Illimité" : value;
        }
        if (key === "max_users") {
            return value === 1 ? "1 utilisateur" : `${value} utilisateurs`;
        }
        return value;
    };

    if (loading || checkingPayment) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
                <p className="text-slate-500">
                    {checkingPayment ? "Vérification du paiement..." : "Chargement..."}
                </p>
            </div>
        );
    }

    const currentPlan = subscription?.plan || "trial";
    const isTrialing = subscription?.is_trial;
    const isActive = subscription?.is_active;

    return (
        <div className="max-w-6xl mx-auto space-y-8" data-testid="billing-page">
            <div>
                <h1 className="font-['Barlow_Condensed'] text-3xl font-bold text-slate-900">
                    Facturation & Abonnement
                </h1>
                <p className="text-slate-500 mt-1">
                    Gérez votre abonnement et accédez à plus de fonctionnalités
                </p>
            </div>

            {/* Current Subscription Status */}
            <Card className={`border-2 ${isActive ? "border-green-200 bg-green-50/30" : "border-amber-200 bg-amber-50/30"}`}>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isActive ? "bg-green-100" : "bg-amber-100"}`}>
                                <CreditCard className={`w-5 h-5 ${isActive ? "text-green-600" : "text-amber-600"}`} />
                            </div>
                            <div>
                                <CardTitle className="font-['Barlow_Condensed']">
                                    Votre abonnement actuel
                                </CardTitle>
                                <CardDescription>
                                    {isTrialing ? "Période d'essai" : subscription?.plan_name || "Aucun abonnement"}
                                </CardDescription>
                            </div>
                        </div>
                        <Badge 
                            variant={isActive ? "default" : "destructive"}
                            className={isActive ? "bg-green-600" : ""}
                        >
                            {isActive ? "Actif" : "Inactif"}
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-slate-500">Plan</p>
                            <p className="font-medium">{subscription?.plan_name || "Essai"}</p>
                        </div>
                        {isTrialing && (
                            <div>
                                <p className="text-sm text-slate-500">Fin de l'essai</p>
                                <p className="font-medium">{formatDate(subscription?.trial_end_date)}</p>
                            </div>
                        )}
                        {isTrialing && subscription?.trial_days_remaining !== null && (
                            <div>
                                <p className="text-sm text-slate-500">Jours restants</p>
                                <p className="font-medium text-orange-600">{subscription?.trial_days_remaining} jours</p>
                            </div>
                        )}
                        {!isTrialing && subscription?.current_period_end && (
                            <div>
                                <p className="text-sm text-slate-500">Prochaine facturation</p>
                                <p className="font-medium">{formatDate(subscription?.current_period_end)}</p>
                            </div>
                        )}
                        <div>
                            <p className="text-sm text-slate-500">Factures ce mois</p>
                            <p className="font-medium">
                                {subscription?.invoices_this_month} / {subscription?.invoices_limit === -1 ? "∞" : subscription?.invoices_limit}
                            </p>
                        </div>
                    </div>
                    
                    {!isTrialing && subscription?.status !== "canceled" && currentPlan !== "trial" && (
                        <div className="mt-4 pt-4 border-t">
                            <Button 
                                variant="outline" 
                                size="sm"
                                className="text-red-600 border-red-200 hover:bg-red-50"
                                onClick={() => setShowCancelDialog(true)}
                            >
                                Annuler l'abonnement
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Trial Warning */}
            {isTrialing && subscription?.trial_days_remaining <= 3 && (
                <Card className="border-amber-300 bg-amber-50">
                    <CardContent className="flex items-center gap-4 py-4">
                        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                        <div className="flex-1">
                            <p className="font-medium text-amber-800">
                                Votre période d'essai se termine bientôt !
                            </p>
                            <p className="text-sm text-amber-700">
                                Choisissez un plan pour continuer à utiliser toutes les fonctionnalités.
                            </p>
                        </div>
                        <Button 
                            className="bg-amber-600 hover:bg-amber-700"
                            onClick={() => document.getElementById("plans-section").scrollIntoView({ behavior: "smooth" })}
                        >
                            Voir les plans
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Subscription Plans */}
            <div id="plans-section">
                <h2 className="font-['Barlow_Condensed'] text-2xl font-bold mb-6">
                    Choisissez votre plan
                </h2>
                
                <div className="grid md:grid-cols-3 gap-6">
                    {plans.map((plan) => {
                        const Icon = PLAN_ICONS[plan.id] || Zap;
                        const color = PLAN_COLORS[plan.id] || "blue";
                        const isCurrentPlan = currentPlan === plan.id;
                        const isPopular = plan.id === "pro";
                        
                        return (
                            <Card 
                                key={plan.id} 
                                className={`relative ${isCurrentPlan ? "border-2 border-green-500" : ""} ${isPopular ? "ring-2 ring-orange-500" : ""}`}
                            >
                                {isPopular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                        <Badge className="bg-orange-600">Le plus populaire</Badge>
                                    </div>
                                )}
                                
                                {isCurrentPlan && (
                                    <div className="absolute -top-3 right-4">
                                        <Badge className="bg-green-600">Plan actuel</Badge>
                                    </div>
                                )}
                                
                                <CardHeader className="text-center pb-2">
                                    <div className={`w-12 h-12 rounded-full bg-${color}-100 flex items-center justify-center mx-auto mb-3`}>
                                        <Icon className={`w-6 h-6 text-${color}-600`} />
                                    </div>
                                    <CardTitle className="font-['Barlow_Condensed'] text-xl">
                                        {plan.name}
                                    </CardTitle>
                                    <CardDescription>{plan.description}</CardDescription>
                                </CardHeader>
                                
                                <CardContent className="text-center">
                                    <div className="mb-6">
                                        <span className="text-4xl font-bold">{plan.price_monthly}€</span>
                                        <span className="text-slate-500">/mois</span>
                                    </div>
                                    
                                    <ul className="space-y-3 text-left">
                                        {Object.entries(plan.features).map(([key, value]) => (
                                            <li key={key} className="flex items-center gap-3">
                                                <span className="flex-shrink-0">
                                                    {renderFeatureValue(key, value)}
                                                </span>
                                                <span className="text-sm text-slate-600">
                                                    {FEATURE_LABELS[key] || key}
                                                    {typeof value !== "boolean" && `: ${renderFeatureValue(key, value)}`}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </CardContent>
                                
                                <CardFooter>
                                    <Button
                                        className={`w-full ${isCurrentPlan ? "bg-green-600" : `bg-${color}-600 hover:bg-${color}-700`}`}
                                        disabled={isCurrentPlan || processingPlan === plan.id}
                                        onClick={() => handleSelectPlan(plan.id)}
                                        data-testid={`select-plan-${plan.id}`}
                                    >
                                        {processingPlan === plan.id ? (
                                            <>
                                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                Redirection...
                                            </>
                                        ) : isCurrentPlan ? (
                                            "Plan actuel"
                                        ) : (
                                            <>
                                                Choisir ce plan
                                                <ArrowRight className="w-4 h-4 ml-2" />
                                            </>
                                        )}
                                    </Button>
                                </CardFooter>
                            </Card>
                        );
                    })}
                </div>
            </div>

            {/* Features Comparison */}
            <Card>
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed']">
                        Comparaison des fonctionnalités
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-3 px-4">Fonctionnalité</th>
                                    {plans.map(plan => (
                                        <th key={plan.id} className="text-center py-3 px-4">{plan.name}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {Object.keys(FEATURE_LABELS).map(featureKey => (
                                    <tr key={featureKey} className="border-b">
                                        <td className="py-3 px-4 text-sm">{FEATURE_LABELS[featureKey]}</td>
                                        {plans.map(plan => (
                                            <td key={plan.id} className="text-center py-3 px-4">
                                                {renderFeatureValue(featureKey, plan.features[featureKey])}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Cancel Subscription Dialog */}
            <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-red-600">
                            <AlertTriangle className="w-5 h-5" />
                            Annuler l'abonnement
                        </DialogTitle>
                        <DialogDescription>
                            Êtes-vous sûr de vouloir annuler votre abonnement ? Vous garderez l'accès jusqu'à la fin de la période en cours.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 my-4">
                        <p className="text-sm text-amber-800">
                            <strong>Attention :</strong> Après l'annulation, vous perdrez l'accès aux fonctionnalités premium et ne pourrez plus créer de nouveaux devis ou factures.
                        </p>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCancelDialog(false)}>
                            Garder mon abonnement
                        </Button>
                        <Button 
                            variant="destructive" 
                            onClick={handleCancelSubscription}
                            disabled={canceling}
                        >
                            {canceling ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Annulation...
                                </>
                            ) : (
                                "Confirmer l'annulation"
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
