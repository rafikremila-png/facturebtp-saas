import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { getDashboard } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
    Euro, 
    AlertCircle, 
    Clock, 
    Users, 
    FileText, 
    Receipt,
    Plus,
    TrendingUp,
    Gift,
    Calendar
} from "lucide-react";
import { toast } from "sonner";

export default function DashboardPage() {
    const { user } = useAuth();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    // Debug: Log trial status
    useEffect(() => {
        if (user) {
            console.log('[TRIAL DEBUG] User trial info:', {
                trial_status: user.trial_status,
                trial_started_at: user.trial_started_at,
                trial_ends_at: user.trial_ends_at,
                invoice_limit: user.invoice_limit
            });
        }
    }, [user]);

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            const response = await getDashboard();
            setStats(response.data);
        } catch (error) {
            toast.error("Erreur lors du chargement du tableau de bord");
        } finally {
            setLoading(false);
        }
    };

    // Calculate days remaining in trial
    const getTrialDaysRemaining = () => {
        if (!user?.trial_ends_at) return null;
        const endDate = new Date(user.trial_ends_at);
        const now = new Date();
        const diffTime = endDate - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays > 0 ? diffDays : 0;
    };

    const trialDaysRemaining = getTrialDaysRemaining();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    const statCards = [
        {
            title: "Chiffre d'affaires",
            value: `${stats?.total_turnover?.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €`,
            icon: Euro,
            color: "bg-green-500",
            description: "Total factures payées"
        },
        {
            title: "Factures impayées",
            value: stats?.unpaid_invoices_count || 0,
            icon: AlertCircle,
            color: "bg-red-500",
            description: `${stats?.unpaid_invoices_amount?.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} € en attente`
        },
        {
            title: "Devis en attente",
            value: stats?.pending_quotes_count || 0,
            icon: Clock,
            color: "bg-amber-500",
            description: "En attente de réponse"
        },
        {
            title: "Clients",
            value: stats?.total_clients || 0,
            icon: Users,
            color: "bg-blue-500",
            description: "Total clients enregistrés"
        }
    ];

    return (
        <div className="space-y-8" data-testid="dashboard-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                        Tableau de bord
                    </h1>
                    <p className="text-slate-500 mt-1">Vue d'ensemble de votre activité</p>
                </div>
                <div className="flex gap-3">
                    <Link to="/devis/new">
                        <Button className="bg-orange-600 hover:bg-orange-700" data-testid="new-quote-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Nouveau devis
                        </Button>
                    </Link>
                    <Link to="/factures/new">
                        <Button variant="outline" data-testid="new-invoice-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Nouvelle facture
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((card, index) => (
                    <Card 
                        key={card.title} 
                        className="card-hover animate-fade-in"
                        style={{ animationDelay: `${index * 0.1}s` }}
                        data-testid={`stat-card-${index}`}
                    >
                        <CardContent className="p-6">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm font-medium text-slate-500">{card.title}</p>
                                    <p className="text-2xl font-bold text-slate-900 mt-1 font-['Barlow_Condensed']">
                                        {card.value}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">{card.description}</p>
                                </div>
                                <div className={`w-10 h-10 ${card.color} rounded-lg flex items-center justify-center`}>
                                    <card.icon className="w-5 h-5 text-white" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="card-hover" data-testid="total-quotes-card">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            Total Devis
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                            {stats?.total_quotes || 0}
                        </p>
                        <Link to="/devis" className="text-sm text-orange-600 hover:underline mt-2 inline-block">
                            Voir tous les devis →
                        </Link>
                    </CardContent>
                </Card>

                <Card className="card-hover" data-testid="total-invoices-card">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
                            <Receipt className="w-4 h-4" />
                            Total Factures
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                            {stats?.total_invoices || 0}
                        </p>
                        <Link to="/factures" className="text-sm text-orange-600 hover:underline mt-2 inline-block">
                            Voir toutes les factures →
                        </Link>
                    </CardContent>
                </Card>

                <Card className="card-hover" data-testid="performance-card">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Performance
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                            {stats?.total_invoices > 0 
                                ? Math.round((stats?.total_turnover / (stats?.total_turnover + stats?.unpaid_invoices_amount || 1)) * 100)
                                : 0}%
                        </p>
                        <p className="text-sm text-slate-400 mt-2">Taux de recouvrement</p>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Actions */}
            <Card data-testid="quick-actions-card">
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed']">Actions rapides</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Link to="/clients/new">
                            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2" data-testid="quick-add-client">
                                <Users className="w-5 h-5 text-orange-600" />
                                <span>Ajouter un client</span>
                            </Button>
                        </Link>
                        <Link to="/devis/new">
                            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2" data-testid="quick-add-quote">
                                <FileText className="w-5 h-5 text-orange-600" />
                                <span>Créer un devis</span>
                            </Button>
                        </Link>
                        <Link to="/factures/new">
                            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2" data-testid="quick-add-invoice">
                                <Receipt className="w-5 h-5 text-orange-600" />
                                <span>Créer une facture</span>
                            </Button>
                        </Link>
                        <Link to="/parametres">
                            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2" data-testid="quick-settings">
                                <TrendingUp className="w-5 h-5 text-orange-600" />
                                <span>Paramètres</span>
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
