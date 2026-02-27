import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Check, X, Zap, Building2, Users, FileText, Mail, Download, Bell, Palette, Code, ArrowRight } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Feature icons mapping
const FEATURE_ICONS = {
    pdf_export: FileText,
    full_article_library: FileText,
    email_support: Mail,
    automatic_reminders: Bell,
    csv_export: Download,
    priority_support: Zap,
    branding_customization: Palette,
    api_access: Code,
};

export default function PricingPage() {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isYearly, setIsYearly] = useState(false);
    const [checkoutLoading, setCheckoutLoading] = useState(null);
    const { user, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchPlans();
    }, []);

    const fetchPlans = async () => {
        try {
            const response = await axios.get(`${API}/saas/plans`);
            setPlans(response.data);
        } catch (error) {
            console.error("Error fetching plans:", error);
            toast.error("Erreur lors du chargement des plans");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectPlan = async (planId) => {
        if (!isAuthenticated) {
            navigate("/login?mode=register");
            return;
        }

        setCheckoutLoading(planId);
        
        try {
            const token = localStorage.getItem("token");
            const response = await axios.post(
                `${API}/saas/checkout`,
                {
                    plan_id: planId,
                    billing_period: isYearly ? "yearly" : "monthly",
                    origin_url: window.location.origin
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            if (response.data.checkout_url) {
                window.location.href = response.data.checkout_url;
            }
        } catch (error) {
            console.error("Checkout error:", error);
            toast.error("Erreur lors de la création du paiement");
        } finally {
            setCheckoutLoading(null);
        }
    };

    const getPrice = (plan) => {
        return isYearly ? plan.price_yearly : plan.price_monthly;
    };

    const getMonthlyEquivalent = (plan) => {
        if (isYearly) {
            return (plan.price_yearly / 12).toFixed(2);
        }
        return plan.price_monthly;
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-slate-100">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-orange-50 to-amber-50 opacity-50" />
                <div className="relative max-w-7xl mx-auto px-4 py-16 sm:py-24">
                    <div className="text-center">
                        <Badge className="mb-4 bg-orange-100 text-orange-800 border-orange-200">
                            🎉 Offre fondateur – -20% à vie pour les 50 premiers clients
                        </Badge>
                        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-6">
                            Le logiciel de devis et facturation
                            <span className="text-orange-600"> pensé pour les artisans du BTP</span>
                        </h1>
                        <p className="text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto mb-8">
                            Créez vos devis et factures en quelques clics. 
                            Suivez vos paiements. Développez votre activité.
                        </p>
                        <Button 
                            size="lg" 
                            className="bg-orange-600 hover:bg-orange-700 text-lg px-8"
                            onClick={() => navigate("/login?mode=register")}
                            data-testid="hero-cta-btn"
                        >
                            Essai gratuit 14 jours
                            <ArrowRight className="ml-2 w-5 h-5" />
                        </Button>
                        <p className="text-sm text-slate-500 mt-4">
                            Sans carte bancaire • Annulation à tout moment
                        </p>
                    </div>
                </div>
            </div>

            {/* Pricing Toggle */}
            <div className="max-w-7xl mx-auto px-4 py-8">
                <div className="flex items-center justify-center gap-4">
                    <span className={`text-sm font-medium ${!isYearly ? 'text-slate-900' : 'text-slate-500'}`}>
                        Mensuel
                    </span>
                    <Switch 
                        checked={isYearly} 
                        onCheckedChange={setIsYearly}
                        data-testid="billing-toggle"
                    />
                    <span className={`text-sm font-medium ${isYearly ? 'text-slate-900' : 'text-slate-500'}`}>
                        Annuel
                    </span>
                    {isYearly && (
                        <Badge className="bg-green-100 text-green-800 border-green-200">
                            -20% d'économie
                        </Badge>
                    )}
                </div>
            </div>

            {/* Pricing Cards */}
            <div className="max-w-7xl mx-auto px-4 pb-16">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {plans.map((plan) => (
                        <Card 
                            key={plan.id}
                            className={`relative flex flex-col ${
                                plan.highlight 
                                    ? 'border-orange-500 border-2 shadow-xl scale-105' 
                                    : 'border-slate-200'
                            }`}
                            data-testid={`plan-card-${plan.id}`}
                        >
                            {plan.badge && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                                    <Badge className="bg-orange-600 text-white px-4 py-1">
                                        {plan.badge}
                                    </Badge>
                                </div>
                            )}
                            
                            <CardHeader className="text-center pb-2">
                                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                                <CardDescription>{plan.description}</CardDescription>
                            </CardHeader>
                            
                            <CardContent className="flex-1">
                                {/* Pricing */}
                                <div className="text-center mb-6">
                                    <div className="flex items-baseline justify-center gap-1">
                                        <span className="text-4xl font-bold text-slate-900">
                                            {getMonthlyEquivalent(plan)}€
                                        </span>
                                        <span className="text-slate-500">/mois</span>
                                    </div>
                                    {isYearly && (
                                        <p className="text-sm text-slate-500 mt-1">
                                            Facturé {getPrice(plan)}€/an
                                        </p>
                                    )}
                                    {isYearly && plan.yearly_savings > 0 && (
                                        <Badge variant="outline" className="mt-2 text-green-600 border-green-300">
                                            Économisez {plan.yearly_savings}€
                                        </Badge>
                                    )}
                                </div>

                                {/* Limits */}
                                <div className="space-y-3 mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                                            <FileText className="w-4 h-4 text-orange-600" />
                                        </div>
                                        <span className="text-slate-700">
                                            {plan.limits.quotes_per_month === -1 
                                                ? "Devis illimités" 
                                                : `${plan.limits.quotes_per_month} devis/mois`
                                            }
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                                            <FileText className="w-4 h-4 text-orange-600" />
                                        </div>
                                        <span className="text-slate-700">
                                            {plan.limits.invoices_per_month === -1 
                                                ? "Factures illimitées" 
                                                : `${plan.limits.invoices_per_month} factures/mois`
                                            }
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                                            <Users className="w-4 h-4 text-orange-600" />
                                        </div>
                                        <span className="text-slate-700">
                                            {plan.limits.max_users === 1 
                                                ? "1 utilisateur" 
                                                : plan.limits.max_users >= 10 
                                                    ? "5+ utilisateurs"
                                                    : `${plan.limits.max_users} utilisateurs`
                                            }
                                        </span>
                                    </div>
                                </div>

                                {/* Features */}
                                <div className="border-t pt-4">
                                    <p className="text-sm font-medium text-slate-700 mb-3">Fonctionnalités incluses :</p>
                                    <div className="space-y-2">
                                        {Object.entries(plan.features).map(([key, enabled]) => {
                                            const Icon = FEATURE_ICONS[key] || Check;
                                            const labels = {
                                                pdf_export: "Export PDF",
                                                full_article_library: "Bibliothèque complète",
                                                email_support: "Support email",
                                                automatic_reminders: "Relances automatiques",
                                                csv_export: "Export comptable CSV",
                                                priority_support: "Support prioritaire",
                                                branding_customization: "Personnalisation marque",
                                                api_access: "Accès API (bientôt)",
                                            };
                                            
                                            return (
                                                <div 
                                                    key={key} 
                                                    className={`flex items-center gap-2 text-sm ${
                                                        enabled ? 'text-slate-700' : 'text-slate-400'
                                                    }`}
                                                >
                                                    {enabled ? (
                                                        <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                                                    ) : (
                                                        <X className="w-4 h-4 text-slate-300 flex-shrink-0" />
                                                    )}
                                                    <span>{labels[key] || key}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </CardContent>
                            
                            <CardFooter>
                                <Button 
                                    className={`w-full ${
                                        plan.highlight 
                                            ? 'bg-orange-600 hover:bg-orange-700' 
                                            : 'bg-slate-900 hover:bg-slate-800'
                                    }`}
                                    size="lg"
                                    onClick={() => handleSelectPlan(plan.id)}
                                    disabled={checkoutLoading === plan.id}
                                    data-testid={`select-plan-${plan.id}`}
                                >
                                    {checkoutLoading === plan.id ? (
                                        <span className="animate-pulse">Chargement...</span>
                                    ) : (
                                        <>Démarrer maintenant</>
                                    )}
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            </div>

            {/* Urgency Banner */}
            <div className="bg-gradient-to-r from-orange-600 to-amber-600 py-8">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
                        🚀 Offre de lancement limitée
                    </h3>
                    <p className="text-orange-100 mb-4">
                        Bénéficiez de -20% à vie en vous inscrivant maintenant. 
                        Plus que <span className="font-bold text-white">47 places</span> disponibles.
                    </p>
                    <Button 
                        size="lg" 
                        variant="secondary"
                        className="bg-white text-orange-600 hover:bg-orange-50"
                        onClick={() => navigate("/login?mode=register")}
                    >
                        Profiter de l'offre
                    </Button>
                </div>
            </div>

            {/* FAQ Section */}
            <div className="max-w-4xl mx-auto px-4 py-16">
                <h2 className="text-3xl font-bold text-center text-slate-900 mb-12">
                    Questions fréquentes
                </h2>
                <div className="space-y-6">
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                        <h3 className="font-semibold text-slate-900 mb-2">
                            Puis-je changer de plan à tout moment ?
                        </h3>
                        <p className="text-slate-600">
                            Oui, vous pouvez upgrader ou downgrader votre plan à tout moment. 
                            Les changements prennent effet immédiatement.
                        </p>
                    </div>
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                        <h3 className="font-semibold text-slate-900 mb-2">
                            L'essai gratuit nécessite-t-il une carte bancaire ?
                        </h3>
                        <p className="text-slate-600">
                            Non, aucune carte bancaire n'est requise pour l'essai gratuit de 14 jours. 
                            Vous pourrez ajouter vos informations de paiement uniquement si vous décidez de continuer.
                        </p>
                    </div>
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                        <h3 className="font-semibold text-slate-900 mb-2">
                            Mes données sont-elles sécurisées ?
                        </h3>
                        <p className="text-slate-600">
                            Absolument. Nous utilisons un cryptage SSL de bout en bout et vos données 
                            sont hébergées sur des serveurs sécurisés conformes au RGPD.
                        </p>
                    </div>
                    <div className="bg-white rounded-lg p-6 shadow-sm border border-slate-200">
                        <h3 className="font-semibold text-slate-900 mb-2">
                            Puis-je annuler mon abonnement ?
                        </h3>
                        <p className="text-slate-600">
                            Oui, vous pouvez annuler à tout moment. Vous conserverez l'accès jusqu'à 
                            la fin de votre période de facturation en cours.
                        </p>
                    </div>
                </div>
            </div>

            {/* Footer CTA */}
            <div className="bg-slate-900 py-16">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <h2 className="text-3xl font-bold text-white mb-4">
                        Prêt à simplifier votre facturation ?
                    </h2>
                    <p className="text-slate-400 mb-8">
                        Rejoignez des centaines d'artisans qui gagnent du temps chaque jour.
                    </p>
                    <Button 
                        size="lg" 
                        className="bg-orange-600 hover:bg-orange-700 text-lg px-8"
                        onClick={() => navigate("/login?mode=register")}
                    >
                        Commencer gratuitement
                    </Button>
                </div>
            </div>
        </div>
    );
}
