import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getInvoice, updateInvoice, downloadInvoicePdf, createInvoiceShareLink, sendInvoiceEmail } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ArrowLeft, Download, CheckCircle, Share2, Copy, Check, Mail, Send } from "lucide-react";
import { toast } from "sonner";

function InvoiceViewPage() {
    var params = useParams();
    var navigate = useNavigate();
    var [invoice, setInvoice] = useState(null);
    var [loading, setLoading] = useState(true);
    var [paidAmount, setPaidAmount] = useState("0");
    var [showShareModal, setShowShareModal] = useState(false);
    var [shareUrl, setShareUrl] = useState("");
    var [copied, setCopied] = useState(false);
    var [showEmailModal, setShowEmailModal] = useState(false);
    var [emailData, setEmailData] = useState({ recipient_email: "", custom_message: "" });
    var [sendingEmail, setSendingEmail] = useState(false);

    useEffect(function() {
        getInvoice(params.id).then(function(res) {
            setInvoice(res.data);
            setPaidAmount(String(res.data.paid_amount || 0));
            setLoading(false);
        }).catch(function() { toast.error("Erreur"); navigate("/factures"); });
    }, [params.id, navigate]);

    function updateStatus(s) {
        updateInvoice(params.id, { payment_status: s }).then(function() {
            setInvoice(function(p) { return { ...p, payment_status: s }; });
            toast.success("Mis à jour");
        }).catch(function() { toast.error("Erreur"); });
    }

    function updatePaid() {
        updateInvoice(params.id, { paid_amount: parseFloat(paidAmount) || 0 }).then(function(r) {
            setInvoice(r.data);
            toast.success("Mis à jour");
        }).catch(function() { toast.error("Erreur"); });
    }

    function markPaid() {
        updateInvoice(params.id, { payment_status: "paye", paid_amount: invoice.total_ttc }).then(function() {
            setInvoice(function(p) { return { ...p, payment_status: "paye", paid_amount: p.total_ttc }; });
            toast.success("Payée");
        }).catch(function() { toast.error("Erreur"); });
    }

    function downloadPdf() { downloadInvoicePdf(invoice.id, invoice.invoice_number).catch(function() { toast.error("Erreur"); }); }
    function fmt(n) { return n.toLocaleString("fr-FR", { minimumFractionDigits: 2 }) + " €"; }

    async function handleShare() {
        try {
            const response = await createInvoiceShareLink(invoice.id);
            const baseUrl = window.location.origin;
            const fullUrl = `${baseUrl}/client/facture/${response.data.share_token}`;
            setShareUrl(fullUrl);
            setShowShareModal(true);
        } catch (error) {
            toast.error("Erreur lors de la création du lien de partage");
        }
    }

    async function copyToClipboard() {
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            toast.success("Lien copié");
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            toast.error("Erreur lors de la copie");
        }
    }

    async function handleSendEmail() {
        if (!emailData.recipient_email) {
            toast.error("Veuillez saisir une adresse email");
            return;
        }
        
        setSendingEmail(true);
        try {
            await sendInvoiceEmail(invoice.id, emailData);
            toast.success("Facture envoyée par email");
            setShowEmailModal(false);
            setEmailData({ recipient_email: "", custom_message: "" });
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de l'envoi");
        } finally {
            setSendingEmail(false);
        }
    }

    if (loading) return <div className="flex justify-center py-20"><div className="spinner"></div></div>;
    if (!invoice) return null;

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-detail-page">
            <div className="flex justify-between">
                <Button variant="ghost" onClick={function() { navigate("/factures"); }} data-testid="back-btn"><ArrowLeft className="w-4 h-4 mr-2" />Retour</Button>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={handleShare} data-testid="share-btn"><Share2 className="w-4 h-4 mr-2" />Partager</Button>
                    <Button variant="outline" onClick={downloadPdf} data-testid="download-pdf-btn"><Download className="w-4 h-4 mr-2" />PDF</Button>
                    {invoice.payment_status !== "paye" && <Button className="bg-green-600" onClick={markPaid} data-testid="mark-paid-btn"><CheckCircle className="w-4 h-4 mr-2" />Payée</Button>}
                </div>
            </div>
            <Card><CardHeader><CardTitle className="font-mono">{invoice.invoice_number}</CardTitle></CardHeader>
                <CardContent><p><strong>Client:</strong> {invoice.client_name}</p><p><strong>Date:</strong> {new Date(invoice.issue_date).toLocaleDateString("fr-FR")}</p></CardContent></Card>
            <Card><CardHeader><CardTitle>Paiement</CardTitle></CardHeader>
                <CardContent className="grid grid-cols-3 gap-4">
                    <div><Label>Statut</Label><Select value={invoice.payment_status} onValueChange={updateStatus}><SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="impaye">Impayé</SelectItem><SelectItem value="partiel">Partiel</SelectItem><SelectItem value="paye">Payé</SelectItem></SelectContent></Select></div>
                    <div><Label>Payé (€)</Label><div className="flex gap-2"><Input type="number" value={paidAmount} onChange={function(e) { setPaidAmount(e.target.value); }} /><Button variant="outline" onClick={updatePaid}>OK</Button></div></div>
                    <div><Label>Reste</Label><p className="text-xl font-bold text-red-600">{fmt(Math.max(0, invoice.total_ttc - (invoice.paid_amount || 0)))}</p></div>
                </CardContent></Card>
            <Card><CardContent className="p-0">
                <Table><TableHeader><TableRow className="bg-slate-900"><TableHead className="text-white">Description</TableHead><TableHead className="text-white text-right">Qté</TableHead><TableHead className="text-white text-right">Prix HT</TableHead><TableHead className="text-white text-right">TVA</TableHead><TableHead className="text-white text-right">Total</TableHead></TableRow></TableHeader>
                    <TableBody>{invoice.items.map(function(it, i) { return <TableRow key={i}><TableCell>{it.description}</TableCell><TableCell className="text-right">{it.quantity}</TableCell><TableCell className="text-right">{fmt(it.unit_price)}</TableCell><TableCell className="text-right">{it.vat_rate}%</TableCell><TableCell className="text-right">{fmt(it.quantity * it.unit_price)}</TableCell></TableRow>; })}</TableBody></Table>
            </CardContent></Card>
            <Card><CardContent className="pt-6 text-right space-y-1"><p>Total HT: <strong>{fmt(invoice.total_ht)}</strong></p><p>TVA: <strong>{fmt(invoice.total_vat)}</strong></p><p className="text-xl">Total TTC: <strong className="text-orange-600">{fmt(invoice.total_ttc)}</strong></p></CardContent></Card>

            {/* Share Modal */}
            <Dialog open={showShareModal} onOpenChange={setShowShareModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Share2 className="w-5 h-5 text-orange-600" />
                            Partager la facture
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <p className="text-sm text-slate-600">
                            Envoyez ce lien à votre client pour qu'il puisse consulter et télécharger la facture.
                        </p>
                        <div className="flex gap-2">
                            <Input value={shareUrl} readOnly className="flex-1 font-mono text-sm" />
                            <Button onClick={copyToClipboard} variant="outline">
                                {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default InvoiceViewPage;
