import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
    Users, 
    UserCheck, 
    UserX,
    Building2,
    Landmark,
    CreditCard,
    AlertTriangle,
    CheckCircle2,
    RefreshCcw,
    BarChart3,
    FileText,
    Euro,
    TrendingUp
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";

export default function AdminAnalyticsPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        if (user && !["admin", "super_admin"].includes(user.role)) {
            toast.error("Accès refusé");
            navigate("/");
            return;
        }
        fetchDashboard();
    }, [user, navigate]);

    const fetchDashboard = async () => {
        try {
            setRefreshing(true);
            const response = await api.get('/admin/dashboard');
            setDashboardData(response.data);
        } catch (error) {
            console.error("Error fetching dashboard:", error);
            if (error.response?.status === 403) {
                toast.error("Accès refusé - Admin uniquement");
                navigate("/");
            } else {
                toast.error("Erreur lors du chargement du dashboard");
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

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600" />
            </div>
        );
    }

    if (!dashboardData) {
        return (
            <div className="text-center py-12">
                <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
                <p className="text-slate-600">Impossible de charger le dashboard</p>
                <Button onClick={fetchDashboard} className="mt-4">
                    Réessayer
                </Button>
            </div>
        );
    }

    const { user_statistics, profile_completion, business_metrics, alerts } = dashboardData;

    return (
        <div className="space-y-8" data-testid="admin-analytics-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                            Dashboard Admin
                        </h1>
                        <Badge className="bg-purple-100 text-purple-700 border-purple-200">
                            PostgreSQL
                        </Badge>
                    </div>
                    <p className="text-slate-500 mt-1">
                        Statistiques utilisateurs et taux de complétion
                    </p>
                </div>
                <Button 
                    variant="outline" 
                    onClick={fetchDashboard}
                    disabled={refreshing}
                    data-testid="refresh-btn"
                >
                    <RefreshCcw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                    {refreshing ? 'Actualisation...' : 'Actualiser'}
                </Button>
            </div>

            {/* User Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200" data-testid="total-users-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-blue-700">Total Utilisateurs</p>
                                <p className="text-3xl font-bold text-blue-900 mt-1">
                                    {user_statistics?.total_users || 0}
                                </p>
                                <p className="text-xs text-blue-600 mt-1">
                                    {user_statistics?.new_users_this_month || 0} nouveaux ce mois
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
                                <Users className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200" data-testid="active-users-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-green-700">Utilisateurs Actifs</p>
                                <p className="text-3xl font-bold text-green-900 mt-1">
                                    {user_statistics?.active_users || 0}
                                </p>
                                <p className="text-xs text-green-600 mt-1">
                                    {user_statistics?.email_verified || 0} vérifiés
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                                <UserCheck className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200" data-testid="inactive-users-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-amber-700">Inactifs / Non vérifiés</p>
                                <p className="text-3xl font-bold text-amber-900 mt-1">
                                    {user_statistics?.inactive_users || 0}
                                </p>
                                <p className="text-xs text-amber-600 mt-1">
                                    {user_statistics?.email_unverified || 0} emails non vérifiés
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center">
                                <UserX className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200" data-testid="avg-completion-card">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm font-medium text-purple-700">Complétion Moyenne</p>
                                <p className="text-3xl font-bold text-purple-900 mt-1">
                                    {profile_completion?.average_completion || 0}%
                                </p>
                                <p className="text-xs text-purple-600 mt-1">
                                    {profile_completion?.users_with_complete_profile || 0} profils complets
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
                                <CheckCircle2 className="w-6 h-6 text-white" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Alerts */}
            {alerts && (alerts.users_missing_company_info > 0 || alerts.users_missing_banking_info > 0 || alerts.users_missing_legal_info > 0) && (
                <Card className="border-orange-200 bg-orange-50" data-testid="alerts-card">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-orange-800">
                            <AlertTriangle className="w-5 h-5" />
                            Alertes - Informations Manquantes
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="flex items-center gap-3 p-3 bg-white rounded-lg">
                                <Building2 className="w-8 h-8 text-orange-500" />
                                <div>
                                    <p className="text-sm text-slate-600">Info entreprise manquante</p>
                                    <p className="text-xl font-bold text-slate-900">{alerts.users_missing_company_info}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 bg-white rounded-lg">
                                <Landmark className="w-8 h-8 text-orange-500" />
                                <div>
                                    <p className="text-sm text-slate-600">Info légale manquante</p>
                                    <p className="text-xl font-bold text-slate-900">{alerts.users_missing_legal_info}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 p-3 bg-white rounded-lg">
                                <CreditCard className="w-8 h-8 text-orange-500" />
                                <div>
                                    <p className="text-sm text-slate-600">Info bancaire manquante</p>
                                    <p className="text-xl font-bold text-slate-900">{alerts.users_missing_banking_info}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Profile Completion Distribution */}
            <Card data-testid="completion-distribution-card">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-slate-600" />
                        Distribution des Taux de Complétion
                    </CardTitle>
                    <CardDescription>Répartition des utilisateurs par niveau de complétion</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {profile_completion?.completion_distribution && Object.entries(profile_completion.completion_distribution).map(([range, count]) => {
                            const total = Object.values(profile_completion.completion_distribution).reduce((a, b) => a + b, 0);
                            const percent = total > 0 ? (count / total) * 100 : 0;
                            
                            return (
                                <div key={range} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium text-slate-700">{range}</span>
                                        <span className="text-slate-500">{count} utilisateurs ({percent.toFixed(1)}%)</span>
                                    </div>
                                    <Progress value={percent} className="h-3" />
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* Category Completion & Business Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Averages */}
                <Card data-testid="category-averages-card">
                    <CardHeader>
                        <CardTitle>Complétion par Catégorie</CardTitle>
                        <CardDescription>Moyenne de complétion pour chaque section du profil</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {profile_completion?.category_averages && (
                                <>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="flex items-center gap-2">
                                                <Users className="w-4 h-4 text-blue-500" />
                                                Profil
                                            </span>
                                            <span className="font-medium">{profile_completion.category_averages.profile || 0}%</span>
                                        </div>
                                        <Progress value={profile_completion.category_averages.profile || 0} className="h-2" />
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="flex items-center gap-2">
                                                <Building2 className="w-4 h-4 text-green-500" />
                                                Entreprise
                                            </span>
                                            <span className="font-medium">{profile_completion.category_averages.company || 0}%</span>
                                        </div>
                                        <Progress value={profile_completion.category_averages.company || 0} className="h-2" />
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="flex items-center gap-2">
                                                <Landmark className="w-4 h-4 text-purple-500" />
                                                Légal
                                            </span>
                                            <span className="font-medium">{profile_completion.category_averages.legal || 0}%</span>
                                        </div>
                                        <Progress value={profile_completion.category_averages.legal || 0} className="h-2" />
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="flex items-center gap-2">
                                                <CreditCard className="w-4 h-4 text-orange-500" />
                                                Bancaire
                                            </span>
                                            <span className="font-medium">{profile_completion.category_averages.banking || 0}%</span>
                                        </div>
                                        <Progress value={profile_completion.category_averages.banking || 0} className="h-2" />
                                    </div>
                                </>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Business Metrics */}
                <Card data-testid="business-metrics-card">
                    <CardHeader>
                        <CardTitle>Métriques Business</CardTitle>
                        <CardDescription>Statistiques globales de la plateforme</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-slate-50 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <FileText className="w-5 h-5 text-blue-500" />
                                    <span className="text-sm text-slate-600">Devis</span>
                                </div>
                                <p className="text-2xl font-bold text-slate-900">{business_metrics?.total_quotes || 0}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {formatCurrency(business_metrics?.total_quoted_amount || 0)}
                                </p>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <Euro className="w-5 h-5 text-green-500" />
                                    <span className="text-sm text-slate-600">Factures</span>
                                </div>
                                <p className="text-2xl font-bold text-slate-900">{business_metrics?.total_invoices || 0}</p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {formatCurrency(business_metrics?.total_invoiced_amount || 0)}
                                </p>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <Users className="w-5 h-5 text-purple-500" />
                                    <span className="text-sm text-slate-600">Clients</span>
                                </div>
                                <p className="text-2xl font-bold text-slate-900">{business_metrics?.total_clients || 0}</p>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-lg">
                                <div className="flex items-center gap-2 mb-2">
                                    <TrendingUp className="w-5 h-5 text-orange-500" />
                                    <span className="text-sm text-slate-600">Encaissé</span>
                                </div>
                                <p className="text-2xl font-bold text-slate-900">
                                    {formatCurrency(business_metrics?.total_paid_amount || 0)}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Users by Plan */}
            {user_statistics?.users_by_plan && Object.keys(user_statistics.users_by_plan).length > 0 && (
                <Card data-testid="users-by-plan-card">
                    <CardHeader>
                        <CardTitle>Utilisateurs par Abonnement</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(user_statistics.users_by_plan).map(([plan, count]) => (
                                <div key={plan} className="p-4 bg-slate-50 rounded-lg text-center">
                                    <p className="text-sm text-slate-600 capitalize">{plan.replace('_', ' ')}</p>
                                    <p className="text-2xl font-bold text-slate-900 mt-1">{count}</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Missing Fields Summary */}
            {profile_completion?.missing_fields_summary && Object.keys(profile_completion.missing_fields_summary).length > 0 && (
                <Card data-testid="missing-fields-card">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-orange-700">
                            <AlertTriangle className="w-5 h-5" />
                            Champs Manquants les Plus Fréquents
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {Object.entries(profile_completion.missing_fields_summary).slice(0, 8).map(([field, count]) => (
                                <div key={field} className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                                    <p className="text-sm text-orange-700 font-medium capitalize">
                                        {field.replace('_', ' ')}
                                    </p>
                                    <p className="text-lg font-bold text-orange-900">{count} utilisateurs</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
