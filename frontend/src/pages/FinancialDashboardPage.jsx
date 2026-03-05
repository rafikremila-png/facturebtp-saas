import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Euro,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  CheckCircle,
  Download,
  FileSpreadsheet,
  FileText,
  RefreshCw,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  PieChart,
  BarChart3,
  Calendar
} from 'lucide-react';

// Status labels in French
const STATUS_LABELS = {
  brouillon: "Brouillon",
  envoyée: "Envoyée",
  en_attente: "En attente",
  partiellement_payée: "Partiellement payée",
  payée: "Payée",
  annulée: "Annulée"
};

const STATUS_COLORS = {
  brouillon: "bg-slate-100 text-slate-800",
  envoyée: "bg-blue-100 text-blue-800",
  en_attente: "bg-orange-100 text-orange-800",
  partiellement_payée: "bg-yellow-100 text-yellow-800",
  payée: "bg-green-100 text-green-800",
  annulée: "bg-red-100 text-red-800"
};

export default function FinancialDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('year');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadData();
  }, [period]);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await api.get('/reports/financial', {
        params: { period }
      });
      setData(response.data);
    } catch (error) {
      console.error('Error loading financial data:', error);
      toast.error('Erreur lors du chargement des données financières');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const endpoint = format === 'csv' 
        ? `/reports/financial/export/csv`
        : `/reports/financial/export/excel`;
      
      const response = await api.get(endpoint, {
        params: { period },
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = format === 'csv' 
        ? `factures_${period}_${new Date().toISOString().split('T')[0]}.csv`
        : `factures_${period}_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Export ${format.toUpperCase()} téléchargé`);
    } catch (error) {
      console.error('Error exporting:', error);
      toast.error(`Erreur lors de l'export ${format.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short'
    });
  };

  // Calculate max for chart scaling
  const maxMonthlyValue = data?.monthly_revenue 
    ? Math.max(...data.monthly_revenue.map(m => m.total), 1)
    : 1;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="financial-dashboard-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-orange-600" />
            Dashboard Financier
          </h1>
          <p className="text-slate-500 mt-1">
            Suivez vos revenus, paiements et créances
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-40" data-testid="period-filter">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="month">Ce mois</SelectItem>
              <SelectItem value="quarter">Ce trimestre</SelectItem>
              <SelectItem value="year">Cette année</SelectItem>
              <SelectItem value="all">Tout</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualiser
          </Button>
          
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={() => handleExport('csv')}
              disabled={exporting}
              data-testid="export-csv-btn"
            >
              <FileText className="w-4 h-4 mr-2" />
              CSV
            </Button>
            <Button 
              variant="outline" 
              onClick={() => handleExport('excel')}
              disabled={exporting}
              data-testid="export-excel-btn"
            >
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Excel
            </Button>
          </div>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total facturé</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(data?.total_revenue)}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Euro className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total encaissé</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(data?.total_paid)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
            {data?.collection_rate > 0 && (
              <p className="text-xs text-green-600 mt-2">
                Taux d'encaissement: {data.collection_rate}%
              </p>
            )}
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">En attente</p>
                <p className="text-2xl font-bold text-orange-600">
                  {formatCurrency(data?.total_pending)}
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">En retard</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(data?.total_overdue)}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Revenue Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-600" />
              Évolution mensuelle
            </CardTitle>
            <CardDescription>
              Revenus facturés et encaissés par mois
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-end gap-2">
              {data?.monthly_revenue?.slice(-12).map((month, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex flex-col gap-0.5" style={{ height: '200px' }}>
                    {/* Total bar */}
                    <div 
                      className="w-full bg-blue-200 rounded-t transition-all"
                      style={{ 
                        height: `${(month.total / maxMonthlyValue) * 100}%`,
                        minHeight: month.total > 0 ? '4px' : '0'
                      }}
                      title={`Total: ${formatCurrency(month.total)}`}
                    />
                    {/* Paid overlay */}
                    <div 
                      className="w-full bg-green-500 rounded-b transition-all -mt-1"
                      style={{ 
                        height: `${(month.paid / maxMonthlyValue) * 100}%`,
                        minHeight: month.paid > 0 ? '4px' : '0'
                      }}
                      title={`Encaissé: ${formatCurrency(month.paid)}`}
                    />
                  </div>
                  <span className="text-xs text-slate-500 whitespace-nowrap">
                    {month.month_label?.split(' ')[0]}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-6 mt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-200 rounded" />
                <span className="text-sm text-slate-500">Facturé</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded" />
                <span className="text-sm text-slate-500">Encaissé</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invoices by Status */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
              <PieChart className="w-5 h-5 text-orange-600" />
              Factures par statut
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.invoices_by_status && Object.entries(data.invoices_by_status).map(([status, count]) => {
                const total = Object.values(data.invoices_by_status).reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
                
                return (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={STATUS_COLORS[status] || 'bg-slate-100'}>
                        {STATUS_LABELS[status] || status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{count}</span>
                      <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-orange-500 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Payments */}
      <Card>
        <CardHeader>
          <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
            <ArrowUpRight className="w-5 h-5 text-green-600" />
            Paiements récents
          </CardTitle>
          <CardDescription>
            Les derniers encaissements enregistrés
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data?.recent_payments?.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Euro className="w-12 h-12 mx-auto mb-4 text-slate-300" />
              <p>Aucun paiement récent</p>
            </div>
          ) : (
            <div className="space-y-3">
              {data?.recent_payments?.map((payment) => (
                <div 
                  key={payment.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <ArrowUpRight className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">
                        {payment.invoice_number}
                      </p>
                      <p className="text-sm text-slate-500">
                        {formatDate(payment.date)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">
                      +{formatCurrency(payment.amount)}
                    </p>
                    <p className="text-xs text-slate-500">
                      sur {formatCurrency(payment.total)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
