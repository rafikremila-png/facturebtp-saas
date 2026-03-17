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
    const [isYearly, setIsYearly] = useState(false);
    const [checkoutLoading, setCheckoutLoading] = useState(null);
    const { user, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Plans définis statiquement - UNIQUEMENT Essai, 29€ et 49€
    const trialPlan = {
        id: 'trial',
        name: 'Essai',
        description: 'Testez gratuitement pendant 14 jours',
        price_monthly: 0,
        price_yearly: 0,
        features: ['5 devis/mois', '5 factures/mois', 'Export PDF', 'Support email']
    };
    
    const paidPlans = [
        {
            id: 'essentiel',
            name: 'Essentiel',
            description: 'Pour les artisans indépendants',
            price_monthly: 29,
            price_yearly: 290,
            features: ['Devis illimités', 'Factures illimitées', 'Export PDF', 'Bibliothèque articles', 'Support email', 'Relances automatiques'],
            popular: false
        },
        {
            id: 'pro',
            name: 'Pro',
            description: 'Pour les entreprises en croissance',
            price_monthly: 49,
            price_yearly: 490,
            features: ['Tout Essentiel +', 'Export CSV', 'Support prioritaire', 'Personnalisation marque', 'Accès API'],
            popular: true
        }
    ];
    // Note: Le plan Business à 99€ est supprimé selon la demande

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
                {/* Trial Plan - Centered alone at top */}
                <div className="flex justify-center mb-12">
                    <Card 
                        className="relative flex flex-col w-full max-w-md border-slate-200 shadow-lg"
                        data-testid="plan-card-trial"
                    >
                        <CardHeader className="text-center pb-2">
                            <CardTitle className="text-2xl">{trialPlan.name}</CardTitle>
                            <CardDescription>{trialPlan.description}</CardDescription>
                        </CardHeader>
                        
                        <CardContent className="flex-1">
                            <div className="text-center mb-6">
                                <div className="flex items-baseline justify-center gap-1">
                                    <span className="text-4xl font-bold text-slate-900">0€</span>
                                    <span className="text-slate-500">/mois</span>
                                </div>
                                <p className="text-sm text-green-600 mt-2 font-medium">
                                    Gratuit pendant 14 jours
                                </p>
                            </div>
                            
                            <div className="space-y-3 mb-6">
                                {trialPlan.features.map((feature, idx) => (
                                    <div key={idx} className="flex items-center gap-3">
                                        <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                                            <Check className="w-4 h-4 text-green-600" />
                                        </div>
                                        <span className="text-slate-700">{feature}</span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                        
                        <CardFooter>
                            <Button 
                                className="w-full bg-slate-600 hover:bg-slate-700"
                                onClick={() => handleSelectPlan('trial')}
                                disabled={checkoutLoading === 'trial'}
                                data-testid="select-plan-trial"
                            >
                                {checkoutLoading === 'trial' ? "Chargement..." : "Commencer l'essai gratuit"}
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
                
                {/* Paid Plans - 29€ and 49€ ONLY - Grid below */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {paidPlans.map((plan) => (
                        <Card 
                            key={plan.id}
                            className={`relative flex flex-col ${
                                plan.popular 
                                    ? 'border-orange-500 border-2 shadow-xl' 
                                    : 'border-slate-200 shadow-lg'
                            }`}
                            data-testid={`plan-card-${plan.id}`}
                        >
                            {plan.popular && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                                    <Badge className="bg-orange-600 text-white px-4 py-1">
                                        Le plus populaire
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
                                            {isYearly ? Math.round(plan.price_yearly / 12) : plan.price_monthly}€
                                        </span>
                                        <span className="text-slate-500">/mois</span>
                                    </div>
                                    {isYearly && (
                                        <p className="text-sm text-slate-500 mt-1">
                                            Facturé {plan.price_yearly}€/an
                                        </p>
                                    )}
                                </div>

                                {/* Features */}
                                <div className="space-y-3">
                                    {plan.features.map((feature, idx) => (
                                        <div key={idx} className="flex items-center gap-3">
                                            <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                                                <Check className="w-4 h-4 text-green-600" />
                                            </div>
                                            <span className="text-slate-700">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                            
                            <CardFooter>
                                <Button 
                                    className={`w-full ${
                                        plan.popular 
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
                                        <>Choisir {plan.name}</>
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
