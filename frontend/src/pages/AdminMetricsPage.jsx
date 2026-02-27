import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
    Euro, 
    Users, 
    TrendingUp, 
    TrendingDown, 
    Clock, 
    AlertTriangle,
    RefreshCcw,
    BarChart3,
    Crown
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminMetricsPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        // Check if user is super_admin
        if (user && user.role !== "super_admin") {
            toast.error("Accès refusé");
            navigate("/");
            return;
        }
        fetchMetrics();
    }, [user, navigate]);

    const fetchMetrics = async (forceRefresh = false) => {
        try {
            if (forceRefresh) setRefreshing(true);
            
            const token = localStorage.getItem("token");
            const response = await axios.get(
                `${API}/admin/metrics?force_refresh=${forceRefresh}`,
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setMetrics(response.data);
        } catch (error) {
            console.error("Error fetching metrics:", error);
            if (error.response?.status === 403) {
                toast.error("Accès refusé - Admin uniquement");
                navigate("/");
            } else {
                toast.error("Erreur lors du chargement des métriques");
            }
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value || 0);
    };

    const formatPercent = (value) => {
        return `${(value || 0).toFixed(1)}%`;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600" />
            </div>
        );
    }

    if (!metrics) {
        return (
            <div className="text-center py-12">
                <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
                <p className="text-slate-600">Impossible de charger les métriques</p>
                <Button onClick={() => fetchMetrics(true)} className="mt-4">
                    Réessayer
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-8" data-testid="admin-metrics-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                            Métriques SaaS
                        </h1>
                        <Badge className="bg-purple-100 text-purple-700 border-purple-200">
                            Admin
                        </Badge>
                    </div>
                    <p className="text-slate-500 mt-1">
                        Vue d'ensemble des revenus et abonnements
                    </p>
                </div>
                <Button 
                    variant="outline" 
                    onClick={() => fetchMetrics(true)}
                    disabled={refreshing}
                    data-testid="refresh-metrics-btn"
                >
                    <RefreshCcw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                    {refreshing ? 'Actualisation...' : 'Actualiser'}
                </Button>
            </div>

            {/* Main Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* MRR */}
                <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200" data-testid="mrr-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-green-700">MRR</p>
                                <p className="text-3xl font-bold text-green-900 mt-1">
                                    {formatCurrency(metrics.mrr)}
                                </p>
                                <p className="text-xs text-green-600 mt-1">Revenu mensuel récurrent</p>
                            </div>
                            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                                <Euro className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* ARR */}
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200" data-testid="arr-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-blue-700">ARR</p>
                                <p className="text-3xl font-bold text-blue-900 mt-1">
                                    {formatCurrency(metrics.arr)}
                                </p>
                                <p className="text-xs text-blue-600 mt-1">Revenu annuel récurrent</p>
                            </div>
                            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Active Subscribers */}
                <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200" data-testid="active-subscribers-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-purple-700">Abonnés actifs</p>
                                <p className="text-3xl font-bold text-purple-900 mt-1">
                                    {metrics.active_subscribers}
                                </p>
                                <p className="text-xs text-purple-600 mt-1">Plans payants actifs</p>
                            </div>
                            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
                                <Crown className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Churn Rate */}
                <Card className={`bg-gradient-to-br ${
                    metrics.churn_rate > 5 
                        ? 'from-red-50 to-orange-50 border-red-200' 
                        : 'from-amber-50 to-yellow-50 border-amber-200'
                }`} data-testid="churn-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className={`text-sm font-medium ${metrics.churn_rate > 5 ? 'text-red-700' : 'text-amber-700'}`}>
                                    Churn Rate
                                </p>
                                <p className={`text-3xl font-bold mt-1 ${metrics.churn_rate > 5 ? 'text-red-900' : 'text-amber-900'}`}>
                                    {formatPercent(metrics.churn_rate)}
                                </p>
                                <p className={`text-xs mt-1 ${metrics.churn_rate > 5 ? 'text-red-600' : 'text-amber-600'}`}>
                                    {metrics.churn_count} annulation(s) ce mois
                                </p>
                            </div>
                            <div className={`w-12 h-12 ${metrics.churn_rate > 5 ? 'bg-red-500' : 'bg-amber-500'} rounded-xl flex items-center justify-center`}>
                                <TrendingDown className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Secondary Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Trial Users */}
                <Card data-testid="trial-users-card">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                    <Clock className="w-5 h-5 text-orange-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500">Utilisateurs en essai</p>
                                    <p className="text-2xl font-bold text-slate-900">{metrics.trial_users}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Expired Users */}
                <Card data-testid="expired-users-card">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                                    <AlertTriangle className="w-5 h-5 text-red-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500">Comptes expirés</p>
                                    <p className="text-2xl font-bold text-slate-900">{metrics.expired_users}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* New This Month */}
                <Card data-testid="new-subscribers-card">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                                    <Users className="w-5 h-5 text-green-600" />
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500">Nouveaux ce mois</p>
                                    <p className="text-2xl font-bold text-slate-900">{metrics.new_subscribers_this_month}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Plan Breakdown */}
            <Card data-testid="plan-breakdown-card">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-slate-600" />
                        Répartition par plan
                    </CardTitle>
                    <CardDescription>Distribution des utilisateurs et contribution au MRR</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {metrics.plan_breakdown?.map((plan) => (
                            <div 
                                key={plan.plan}
                                className="p-4 rounded-lg border bg-slate-50"
                                data-testid={`plan-${plan.plan}`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold capitalize text-slate-900">
                                        {plan.plan === "trial" ? "Essai" : plan.plan}
                                    </span>
                                    <Badge variant="outline" className="text-xs">
                                        {plan.price}€/mois
                                    </Badge>
                                </div>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Actifs</span>
                                        <span className="font-medium">{plan.active}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">En essai</span>
                                        <span className="font-medium">{plan.trial}</span>
                                    </div>
                                    <div className="flex justify-between border-t pt-1 mt-1">
                                        <span className="text-slate-500">MRR</span>
                                        <span className="font-semibold text-green-600">
                                            {formatCurrency(plan.mrr_contribution)}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* MRR History Chart (Simple Version) */}
            <Card data-testid="mrr-history-card">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-slate-600" />
                        Évolution du MRR
                    </CardTitle>
                    <CardDescription>Revenu mensuel récurrent sur les 6 derniers mois</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-64 flex items-end justify-around gap-4 pt-8">
                        {metrics.mrr_history?.map((month, index) => {
                            const maxMrr = Math.max(...metrics.mrr_history.map(m => m.mrr), 100);
                            const heightPercent = maxMrr > 0 ? (month.mrr / maxMrr) * 100 : 0;
                            
                            return (
                                <div 
                                    key={month.month}
                                    className="flex flex-col items-center flex-1"
                                    data-testid={`mrr-bar-${index}`}
                                >
                                    <span className="text-sm font-medium text-slate-700 mb-2">
                                        {formatCurrency(month.mrr)}
                                    </span>
                                    <div 
                                        className="w-full max-w-[60px] bg-gradient-to-t from-orange-500 to-amber-400 rounded-t-lg transition-all duration-500"
                                        style={{ 
                                            height: `${Math.max(heightPercent, 5)}%`,
                                            minHeight: '20px'
                                        }}
                                    />
                                    <span className="text-xs text-slate-500 mt-2">
                                        {month.month_label}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* Last Updated */}
            {metrics.calculated_at && (
                <p className="text-xs text-slate-400 text-center">
                    Dernière mise à jour : {new Date(metrics.calculated_at).toLocaleString('fr-FR')}
                </p>
            )}
        </div>
    );
}
