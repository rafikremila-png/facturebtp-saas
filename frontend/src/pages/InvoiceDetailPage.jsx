import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getInvoice, updateInvoice, downloadInvoicePdf } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Download, Calendar, User, CreditCard, CheckCircle } from "lucide-react";
import { toast } from "sonner";

const statusLabels = { impaye: "Impayé", paye: "Payé", partiel: "Partiellement payé" };

export default function InvoiceDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [invoice, setInvoice] = useState(null);
    const [loading, setLoading] = useState(true);
    const [paidAmount, setPaidAmount] = useState("");
    const [updating, setUpdating] = useState(false);

    useEffect(() => {
        const loadInvoice = async () => {
            try {
                const response = await getInvoice(id);
                setInvoice(response.data);
                setPaidAmount(response.data.paid_amount?.toString() || "0");
            } catch (error) {
                toast.error("Erreur lors du chargement de la facture");
                navigate("/factures");
            } finally {
                setLoading(false);
            }
        };
        loadInvoice();
    }, [id, navigate]);

    const handleStatusChange = async (newStatus) => {
        setUpdating(true);
        try {
            await updateInvoice(id, { payment_status: newStatus });
            setInvoice(prev => ({ ...prev, payment_status: newStatus }));
            toast.success("Statut mis à jour");
        } catch (error) {
            toast.error("Erreur lors de la mise à jour du statut");
        } finally {
            setUpdating(false);
        }
    };

    const handlePaymentMethodChange = async (newMethod) => {
        setUpdating(true);
        try {
            await updateInvoice(id, { payment_method: newMethod });
            setInvoice(prev => ({ ...prev, payment_method: newMethod }));
            toast.success("Mode de paiement mis à jour");
        } catch (error) {
            toast.error("Erreur lors de la mise à jour");
        } finally {
            setUpdating(false);
        }
    };

    const handlePaidAmountUpdate = async () => {
        const amount = parseFloat(paidAmount) || 0;
        setUpdating(true);
        try {
            const response = await updateInvoice(id, { paid_amount: amount });
            setInvoice(response.data);
            toast.success("Montant payé mis à jour");
        } catch (error) {
            toast.error("Erreur lors de la mise à jour");
        } finally {
            setUpdating(false);
        }
    };

    const handleMarkAsPaid = async () => {
        if (!invoice) return;
        setUpdating(true);
        try {
            await updateInvoice(id, { payment_status: "paye", paid_amount: invoice.total_ttc });
            setInvoice(prev => ({ ...prev, payment_status: "paye", paid_amount: prev.total_ttc }));
            setPaidAmount(invoice.total_ttc.toString());
            toast.success("Facture marquée comme payée");
        } catch (error) {
            toast.error("Erreur lors de la mise à jour");
        } finally {
            setUpdating(false);
        }
    };

    const handleDownloadPdf = async () => {
        if (!invoice) return;
        try {
            await downloadInvoicePdf(invoice.id, invoice.invoice_number);
            toast.success("PDF téléchargé");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du PDF");
        }
    };

    const formatDate = (dateString) => new Date(dateString).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
    const formatCurrency = (amount) => amount.toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €';

    if (loading) return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
    if (!invoice) return null;

    const remainingAmount = invoice.total_ttc - (invoice.paid_amount || 0);

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-detail-page">
            <div className="flex items-center justify-between">
                <Button variant="ghost" onClick={() => navigate("/factures")} data-testid="back-btn">
                    <ArrowLeft className="w-4 h-4 mr-2" />Retour
                </Button>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={handleDownloadPdf} data-testid="download-pdf-btn">
                        <Download className="w-4 h-4 mr-2" />Télécharger PDF
                    </Button>
                    {invoice.payment_status !== "paye" && (
                        <Button className="bg-green-600 hover:bg-green-700" onClick={handleMarkAsPaid} disabled={updating} data-testid="mark-paid-btn">
                            <CheckCircle className="w-4 h-4 mr-2" />Marquer comme payée
                        </Button>
                    )}
                </div>
            </div>

            <Card>
                <CardHeader className="border-b">
                    <div className="flex items-start justify-between">
                        <div>
                            <CardTitle className="text-2xl font-['Barlow_Condensed'] font-mono">{invoice.invoice_number}</CardTitle>
                            <p className="text-slate-500 mt-1">Facture</p>
                        </div>
                        <span className={`status-badge status-${invoice.payment_status}`}>{statusLabels[invoice.payment_status]}</span>
                    </div>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center"><User className="w-5 h-5 text-blue-600" /></div>
                            <div><p className="text-sm text-slate-500">Client</p><p className="font-medium">{invoice.client_name}</p></div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center"><Calendar className="w-5 h-5 text-green-600" /></div>
                            <div><p className="text-sm text-slate-500">Date d'émission</p><p className="font-medium">{formatDate(invoice.issue_date)}</p></div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center"><CreditCard className="w-5 h-5 text-purple-600" /></div>
                            <div>
                                <p className="text-sm text-slate-500">Mode de paiement</p>
                                <Select value={invoice.payment_method} onValueChange={handlePaymentMethodChange}>
                                    <SelectTrigger className="w-40 mt-1" data-testid="payment-method-select"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="virement">Virement bancaire</SelectItem>
                                        <SelectItem value="cheque">Chèque</SelectItem>
                                        <SelectItem value="especes">Espèces</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle className="font-['Barlow_Condensed']">Gestion du paiement</CardTitle></CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                            <Label>Statut de paiement</Label>
                            <Select value={invoice.payment_status} onValueChange={handleStatusChange}>
                                <SelectTrigger data-testid="payment-status-select"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="impaye">Impayé</SelectItem>
                                    <SelectItem value="partiel">Partiellement payé</SelectItem>
                                    <SelectItem value="paye">Payé</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Montant payé (€)</Label>
                            <div className="flex gap-2">
                                <Input type="number" min="0" step="0.01" value={paidAmount} onChange={(e) => setPaidAmount(e.target.value)} data-testid="paid-amount-input" />
                                <Button onClick={handlePaidAmountUpdate} disabled={updating} variant="outline" data-testid="update-paid-btn">OK</Button>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Reste à payer</Label>
                            <p className={`text-2xl font-bold font-['Barlow_Condensed'] ${remainingAmount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                {formatCurrency(Math.max(0, remainingAmount))}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle className="font-['Barlow_Condensed']">Détail de la facture</CardTitle></CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-slate-900 hover:bg-slate-900">
                                <TableHead className="text-white font-semibold">Description</TableHead>
                                <TableHead className="text-white font-semibold text-right">Qté</TableHead>
                                <TableHead className="text-white font-semibold text-right">Prix unit. HT</TableHead>
                                <TableHead className="text-white font-semibold text-right">TVA</TableHead>
                                <TableHead className="text-white font-semibold text-right">Total HT</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {invoice.items.map((item, index) => (
                                <TableRow key={index} className="table-row-hover">
                                    <TableCell className="font-medium">{item.description}</TableCell>
                                    <TableCell className="text-right">{item.quantity}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                                    <TableCell className="text-right">{item.vat_rate}%</TableCell>
                                    <TableCell className="text-right font-medium">{formatCurrency(item.quantity * item.unit_price)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col items-end space-y-2">
                        <div className="flex gap-8 text-sm"><span className="text-slate-500">Total HT:</span><span className="font-medium w-28 text-right">{formatCurrency(invoice.total_ht)}</span></div>
                        <div className="flex gap-8 text-sm"><span className="text-slate-500">Total TVA:</span><span className="font-medium w-28 text-right">{formatCurrency(invoice.total_vat)}</span></div>
                        <div className="flex gap-8 text-xl font-bold pt-2 border-t"><span className="text-slate-900">Total TTC:</span><span className="text-orange-600 w-28 text-right">{formatCurrency(invoice.total_ttc)}</span></div>
                        {invoice.paid_amount > 0 && (
                            <>
                                <div className="flex gap-8 text-sm text-green-600"><span>Montant payé:</span><span className="font-medium w-28 text-right">-{formatCurrency(invoice.paid_amount)}</span></div>
                                <div className="flex gap-8 text-lg font-bold text-red-600"><span>Reste à payer:</span><span className="w-28 text-right">{formatCurrency(Math.max(0, remainingAmount))}</span></div>
                            </>
                        )}
                    </div>
                </CardContent>
            </Card>

            {invoice.notes && (
                <Card>
                    <CardHeader><CardTitle className="font-['Barlow_Condensed']">Notes</CardTitle></CardHeader>
                    <CardContent><p className="text-slate-600 whitespace-pre-wrap">{invoice.notes}</p></CardContent>
                </Card>
            )}
        </div>
    );
}
