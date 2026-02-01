import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getInvoice, updateInvoice, downloadInvoicePdf } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Download, CheckCircle } from "lucide-react";
import { toast } from "sonner";

export default function InvoiceDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [invoice, setInvoice] = useState(null);
    const [loading, setLoading] = useState(true);
    const [paidAmount, setPaidAmount] = useState("0");

    useEffect(() => {
        getInvoice(id).then(res => {
            setInvoice(res.data);
            setPaidAmount(String(res.data.paid_amount || 0));
            setLoading(false);
        }).catch(() => {
            toast.error("Erreur");
            navigate("/factures");
        });
    }, [id, navigate]);

    const updateStatus = async (s) => {
        try {
            await updateInvoice(id, { payment_status: s });
            setInvoice(p => ({ ...p, payment_status: s }));
            toast.success("Mis à jour");
        } catch { toast.error("Erreur"); }
    };

    const updatePaid = async () => {
        try {
            const r = await updateInvoice(id, { paid_amount: parseFloat(paidAmount) || 0 });
            setInvoice(r.data);
            toast.success("Mis à jour");
        } catch { toast.error("Erreur"); }
    };

    const markPaid = async () => {
        try {
            await updateInvoice(id, { payment_status: "paye", paid_amount: invoice.total_ttc });
            setInvoice(p => ({ ...p, payment_status: "paye", paid_amount: p.total_ttc }));
            toast.success("Payée");
        } catch { toast.error("Erreur"); }
    };

    const downloadPdf = async () => {
        try {
            await downloadInvoicePdf(invoice.id, invoice.invoice_number);
        } catch { toast.error("Erreur"); }
    };

    const fmt = (n) => n.toLocaleString("fr-FR", { minimumFractionDigits: 2 }) + " €";

    if (loading) return <div className="flex justify-center py-20"><div className="spinner" /></div>;
    if (!invoice) return null;

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-detail-page">
            <div className="flex justify-between">
                <Button variant="ghost" onClick={() => navigate("/factures")} data-testid="back-btn">
                    <ArrowLeft className="w-4 h-4 mr-2" />Retour
                </Button>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={downloadPdf} data-testid="download-pdf-btn">
                        <Download className="w-4 h-4 mr-2" />PDF
                    </Button>
                    {invoice.payment_status !== "paye" && (
                        <Button className="bg-green-600" onClick={markPaid} data-testid="mark-paid-btn">
                            <CheckCircle className="w-4 h-4 mr-2" />Payée
                        </Button>
                    )}
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="font-mono">{invoice.invoice_number}</CardTitle>
                </CardHeader>
                <CardContent>
                    <p><strong>Client:</strong> {invoice.client_name}</p>
                    <p><strong>Date:</strong> {new Date(invoice.issue_date).toLocaleDateString("fr-FR")}</p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>Paiement</CardTitle></CardHeader>
                <CardContent className="grid grid-cols-3 gap-4">
                    <div>
                        <Label>Statut</Label>
                        <Select value={invoice.payment_status} onValueChange={updateStatus}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="impaye">Impayé</SelectItem>
                                <SelectItem value="partiel">Partiel</SelectItem>
                                <SelectItem value="paye">Payé</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Payé (€)</Label>
                        <div className="flex gap-2">
                            <Input type="number" value={paidAmount} onChange={e => setPaidAmount(e.target.value)} />
                            <Button variant="outline" onClick={updatePaid}>OK</Button>
                        </div>
                    </div>
                    <div>
                        <Label>Reste</Label>
                        <p className="text-xl font-bold text-red-600">{fmt(Math.max(0, invoice.total_ttc - (invoice.paid_amount || 0)))}</p>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-slate-900">
                                <TableHead className="text-white">Description</TableHead>
                                <TableHead className="text-white text-right">Qté</TableHead>
                                <TableHead className="text-white text-right">Prix HT</TableHead>
                                <TableHead className="text-white text-right">TVA</TableHead>
                                <TableHead className="text-white text-right">Total</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {invoice.items.map((it, i) => (
                                <TableRow key={i}>
                                    <TableCell>{it.description}</TableCell>
                                    <TableCell className="text-right">{it.quantity}</TableCell>
                                    <TableCell className="text-right">{fmt(it.unit_price)}</TableCell>
                                    <TableCell className="text-right">{it.vat_rate}%</TableCell>
                                    <TableCell className="text-right">{fmt(it.quantity * it.unit_price)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6 text-right space-y-1">
                    <p>Total HT: <strong>{fmt(invoice.total_ht)}</strong></p>
                    <p>TVA: <strong>{fmt(invoice.total_vat)}</strong></p>
                    <p className="text-xl">Total TTC: <strong className="text-orange-600">{fmt(invoice.total_ttc)}</strong></p>
                </CardContent>
            </Card>
        </div>
    );
}
