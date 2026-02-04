import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
    Euro, TrendingUp, Receipt, Shield, FileText, 
    CheckCircle, Clock, AlertCircle, Calendar,
    PiggyBank, HardHat, Building2, ArrowRight, Download, Loader2
} from "lucide-react";
import { downloadFinancialSummaryPdf } from "@/lib/api";
import { toast } from "sonner";

const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', { 
        style: 'currency', 
        currency: 'EUR' 
    }).format(amount || 0);
};

const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR');
};

const StatusBadge = ({ status }) => {
    const statusConfig = {
        paye: { label: "Payé", className: "bg-green-100 text-green-700" },
        impaye: { label: "En attente", className: "bg-amber-100 text-amber-700" },
        partiel: { label: "Partiel", className: "bg-blue-100 text-blue-700" }
    };
    const config = statusConfig[status] || statusConfig.impaye;
    return <span className={`text-xs px-2 py-1 rounded font-medium ${config.className}`}>{config.label}</span>;
};

export default function ProjectFinancialSummary({ summary, isPublic = false }) {
    if (!summary) return null;

    const { 
        quote_number, client_name, status,
        project_total_ht, project_total_vat, project_total_ttc,
        progress_percentage,
        acomptes, situations, retenue_garantie, totals, invoices
    } = summary;

    return (
        <div className="space-y-6" data-testid="financial-summary">
            {/* Header Card */}
            <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-white">
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <Building2 className="w-5 h-5 text-slate-400" />
                                <span className="text-slate-400 text-sm">Projet {quote_number}</span>
                            </div>
                            <h2 className="text-2xl font-bold">{client_name}</h2>
                        </div>
                        <div className="text-right">
                            <p className="text-slate-400 text-sm">Montant total du projet</p>
                            <p className="text-3xl font-bold text-emerald-400">{formatCurrency(project_total_ttc)}</p>
                            {project_total_vat > 0 && (
                                <p className="text-xs text-slate-400">
                                    {formatCurrency(project_total_ht)} HT + {formatCurrency(project_total_vat)} TVA
                                </p>
                            )}
                        </div>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="mt-6">
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-400">Progression des paiements</span>
                            <span className="font-medium">{totals.percentage_paid}% encaissé</span>
                        </div>
                        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
                                style={{ width: `${totals.percentage_paid}%` }}
                            />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Invoiced */}
                <Card>
                    <CardContent className="pt-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                <FileText className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">Facturé</p>
                                <p className="text-xl font-bold">{formatCurrency(totals.total_invoiced)}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Total Paid */}
                <Card>
                    <CardContent className="pt-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-green-600" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">Encaissé</p>
                                <p className="text-xl font-bold text-green-600">{formatCurrency(totals.total_paid)}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Remaining to Pay */}
                <Card>
                    <CardContent className="pt-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                <Clock className="w-5 h-5 text-amber-600" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">Reste à payer</p>
                                <p className="text-xl font-bold text-amber-600">{formatCurrency(totals.remaining_to_pay)}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Remaining to Invoice */}
                <Card>
                    <CardContent className="pt-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                <Receipt className="w-5 h-5 text-purple-600" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wide">Reste à facturer</p>
                                <p className="text-xl font-bold text-purple-600">{formatCurrency(totals.remaining_to_invoice)}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Acomptes */}
                <Card className={acomptes.count > 0 ? "border-purple-200" : ""}>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-base flex items-center gap-2">
                            <PiggyBank className="w-4 h-4 text-purple-600" />
                            Acomptes
                            {acomptes.count > 0 && (
                                <Badge variant="secondary" className="ml-auto">{acomptes.count}</Badge>
                            )}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {acomptes.count > 0 ? (
                            <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Facturé</span>
                                    <span className="font-medium">{formatCurrency(acomptes.total_invoiced)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Encaissé</span>
                                    <span className="font-medium text-green-600">{formatCurrency(acomptes.total_paid)}</span>
                                </div>
                                {acomptes.pending > 0 && (
                                    <div className="flex justify-between text-sm pt-2 border-t">
                                        <span className="text-slate-500">En attente</span>
                                        <span className="font-medium text-amber-600">{formatCurrency(acomptes.pending)}</span>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <p className="text-sm text-slate-400 italic">Aucun acompte</p>
                        )}
                    </CardContent>
                </Card>

                {/* Situations */}
                <Card className={situations.count > 0 ? "border-emerald-200" : ""}>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-base flex items-center gap-2">
                            <HardHat className="w-4 h-4 text-emerald-600" />
                            Situations
                            {situations.count > 0 && (
                                <Badge variant="secondary" className="ml-auto">{situations.count}</Badge>
                            )}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {situations.count > 0 ? (
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>Avancement chantier</span>
                                        <span>{situations.progress_percentage}%</span>
                                    </div>
                                    <Progress value={situations.progress_percentage} className="h-2" />
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Facturé</span>
                                    <span className="font-medium">{formatCurrency(situations.total_invoiced)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Encaissé</span>
                                    <span className="font-medium text-green-600">{formatCurrency(situations.total_paid)}</span>
                                </div>
                                {situations.pending > 0 && (
                                    <div className="flex justify-between text-sm pt-2 border-t">
                                        <span className="text-slate-500">En attente</span>
                                        <span className="font-medium text-amber-600">{formatCurrency(situations.pending)}</span>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <p className="text-sm text-slate-400 italic">Aucune situation</p>
                        )}
                    </CardContent>
                </Card>

                {/* Retenue de garantie */}
                <Card className={retenue_garantie.total_retained > 0 ? "border-amber-200" : ""}>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-base flex items-center gap-2">
                            <Shield className="w-4 h-4 text-amber-600" />
                            Retenue de garantie
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {retenue_garantie.total_retained > 0 ? (
                            <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Total retenu</span>
                                    <span className="font-medium">{formatCurrency(retenue_garantie.total_retained)}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Libéré</span>
                                    <span className="font-medium text-green-600">{formatCurrency(retenue_garantie.total_released)}</span>
                                </div>
                                {retenue_garantie.pending_release > 0 && (
                                    <>
                                        <div className="flex justify-between text-sm pt-2 border-t">
                                            <span className="text-slate-500">En attente</span>
                                            <span className="font-medium text-amber-600">{formatCurrency(retenue_garantie.pending_release)}</span>
                                        </div>
                                        {retenue_garantie.next_release_date && (
                                            <div className="flex items-center gap-1 text-xs text-slate-500">
                                                <Calendar className="w-3 h-3" />
                                                Prochaine libération: {formatDate(retenue_garantie.next_release_date)}
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        ) : (
                            <p className="text-sm text-slate-400 italic">Aucune retenue appliquée</p>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Invoice List */}
            {invoices && invoices.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            Historique des factures
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {invoices.map((inv) => (
                                <div 
                                    key={inv.id}
                                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                                            inv.payment_status === 'paye' 
                                                ? 'bg-green-100 text-green-700' 
                                                : 'bg-amber-100 text-amber-700'
                                        }`}>
                                            {inv.payment_status === 'paye' ? '✓' : '⏱'}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                {!isPublic ? (
                                                    <Link 
                                                        to={`/factures/${inv.id}`}
                                                        className="font-medium text-slate-900 hover:text-blue-600"
                                                    >
                                                        {inv.invoice_number}
                                                    </Link>
                                                ) : (
                                                    <span className="font-medium text-slate-900">{inv.invoice_number}</span>
                                                )}
                                                {inv.has_retenue && !inv.retenue_released && (
                                                    <Shield className="w-3 h-3 text-amber-500" title="Retenue de garantie" />
                                                )}
                                            </div>
                                            <p className="text-xs text-slate-500">{inv.type} • {inv.date}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold">{formatCurrency(inv.total_ttc)}</p>
                                        <StatusBadge status={inv.payment_status} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
