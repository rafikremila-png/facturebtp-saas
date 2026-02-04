import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getInvoice, updateInvoice, downloadInvoicePdf, createInvoiceShareLink, sendInvoiceEmail, applyRetenueGarantie, removeRetenueGarantie, releaseRetenueGarantie } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, Download, CheckCircle, Share2, Copy, Check, Mail, Send, Shield, ShieldCheck, Unlock, Calendar, Percent, AlertTriangle } from "lucide-react";
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
    // Retenue de garantie state
    var [showRetenueModal, setShowRetenueModal] = useState(false);
    var [retenueData, setRetenueData] = useState({ rate: 5, warranty_months: 12 });
    var [applyingRetenue, setApplyingRetenue] = useState(false);
    var [releasingRetenue, setReleasingRetenue] = useState(false);

    useEffect(function() {
        loadInvoice();
    }, [params.id]);

    function loadInvoice() {
        getInvoice(params.id).then(function(res) {
            setInvoice(res.data);
            setPaidAmount(String(res.data.paid_amount || 0));
            setLoading(false);
        }).catch(function() { toast.error("Erreur"); navigate("/factures"); });
    }

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
        const amount = invoice.has_retenue_garantie ? invoice.net_a_payer : invoice.total_ttc;
        updateInvoice(params.id, { payment_status: "paye", paid_amount: amount }).then(function() {
            setInvoice(function(p) { return { ...p, payment_status: "paye", paid_amount: amount }; });
            toast.success("Payée");
        }).catch(function() { toast.error("Erreur"); });
    }

    function downloadPdf() { downloadInvoicePdf(invoice.id, invoice.invoice_number).catch(function() { toast.error("Erreur"); }); }
    function fmt(n) { return n.toLocaleString("fr-FR", { minimumFractionDigits: 2 }) + " €"; }

    // Retenue de garantie functions
    async function handleApplyRetenue() {
        if (retenueData.rate <= 0 || retenueData.rate > 5) {
            toast.error("Le taux doit être entre 0 et 5%");
            return;
        }
        setApplyingRetenue(true);
        try {
            await applyRetenueGarantie(invoice.id, retenueData);
            toast.success("Retenue de garantie appliquée");
            setShowRetenueModal(false);
            loadInvoice();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur");
        } finally {
            setApplyingRetenue(false);
        }
    }

    async function handleRemoveRetenue() {
        try {
            await removeRetenueGarantie(invoice.id);
            toast.success("Retenue de garantie supprimée");
            loadInvoice();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur");
        }
    }

    async function handleReleaseRetenue() {
        setReleasingRetenue(true);
        try {
            await releaseRetenueGarantie(invoice.id);
            toast.success("Retenue de garantie libérée");
            loadInvoice();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur");
        } finally {
            setReleasingRetenue(false);
        }
    }

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
                    <Button variant="outline" onClick={() => setShowEmailModal(true)} className="bg-blue-50 hover:bg-blue-100 border-blue-200" data-testid="send-email-btn"><Mail className="w-4 h-4 mr-2 text-blue-600" />Envoyer par email</Button>
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
            
            {/* Totals Card with Retenue de Garantie */}
            <Card>
                <CardContent className="pt-6 space-y-4">
                    <div className="text-right space-y-1">
                        <p>Total HT: <strong>{fmt(invoice.total_ht)}</strong></p>
                        <p>TVA: <strong>{fmt(invoice.total_vat)}</strong></p>
                        <p className="text-xl">Total TTC: <strong className="text-orange-600">{fmt(invoice.total_ttc)}</strong></p>
                    </div>
                    
                    {/* Retenue de Garantie Section */}
                    {invoice.has_retenue_garantie && (
                        <div className={`border rounded-lg p-4 ${invoice.retenue_garantie_released ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    {invoice.retenue_garantie_released ? (
                                        <ShieldCheck className="w-5 h-5 text-green-600" />
                                    ) : (
                                        <Shield className="w-5 h-5 text-amber-600" />
                                    )}
                                    <span className="font-semibold">Retenue de garantie ({invoice.retenue_garantie_rate}%)</span>
                                </div>
                                {invoice.retenue_garantie_released ? (
                                    <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Libérée</span>
                                ) : (
                                    <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded">Retenue</span>
                                )}
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-slate-500">Montant retenu</p>
                                    <p className="font-bold text-lg">{fmt(invoice.retenue_garantie_amount)}</p>
                                </div>
                                <div>
                                    <p className="text-slate-500">Date de libération</p>
                                    <p className="font-medium flex items-center gap-1">
                                        <Calendar className="w-4 h-4" />
                                        {invoice.retenue_garantie_release_date ? new Date(invoice.retenue_garantie_release_date).toLocaleDateString('fr-FR') : '-'}
                                    </p>
                                </div>
                            </div>
                            
                            {!invoice.retenue_garantie_released && (
                                <div className="mt-4 pt-4 border-t border-amber-200">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm text-slate-500">Net à payer (après retenue)</p>
                                            <p className="text-xl font-bold text-emerald-600">{fmt(invoice.net_a_payer || (invoice.total_ttc - invoice.retenue_garantie_amount))}</p>
                                        </div>
                                        <Button 
                                            onClick={handleReleaseRetenue}
                                            disabled={releasingRetenue}
                                            className="bg-emerald-600 hover:bg-emerald-700"
                                            data-testid="release-retenue-btn"
                                        >
                                            {releasingRetenue ? (
                                                <><span className="spinner w-4 h-4 mr-2"></span>Libération...</>
                                            ) : (
                                                <><Unlock className="w-4 h-4 mr-2" />Libérer la retenue</>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                            )}
                            
                            {invoice.retenue_garantie_released && (
                                <div className="mt-3 p-2 bg-green-100 rounded text-sm text-green-800">
                                    ✓ Retenue libérée - Le montant de {fmt(invoice.retenue_garantie_amount)} est maintenant dû au prestataire.
                                </div>
                            )}
                        </div>
                    )}
                    
                    {/* Toggle to apply retenue */}
                    {!invoice.has_retenue_garantie && invoice.payment_status !== 'paye' && (
                        <div className="border rounded-lg p-4 bg-slate-50">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="font-medium">Retenue de garantie</p>
                                        <p className="text-xs text-slate-500">Max 5% - Libérable après garantie</p>
                                    </div>
                                </div>
                                <Button 
                                    variant="outline"
                                    onClick={() => setShowRetenueModal(true)}
                                    data-testid="add-retenue-btn"
                                >
                                    <Shield className="w-4 h-4 mr-2" />
                                    Appliquer
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Retenue de Garantie Modal */}
            <Dialog open={showRetenueModal} onOpenChange={setShowRetenueModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Shield className="w-5 h-5 text-amber-600" />
                            Appliquer une retenue de garantie
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
                            <div className="flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5" />
                                <div>
                                    <strong>Réglementation française (Loi n°75-1334)</strong>
                                    <p className="text-amber-700 mt-1">La retenue de garantie ne peut excéder 5% du montant TTC. Elle est libérable 1 an après la réception des travaux, sauf réserves.</p>
                                </div>
                            </div>
                        </div>
                        
                        <div className="space-y-3">
                            <Label>Taux de retenue (%)</Label>
                            <div className="flex items-center gap-4">
                                <Slider
                                    value={[retenueData.rate]}
                                    onValueChange={(v) => setRetenueData(prev => ({ ...prev, rate: v[0] }))}
                                    min={0.5}
                                    max={5}
                                    step={0.5}
                                    className="flex-1"
                                />
                                <div className="flex items-center gap-2 w-20">
                                    <Input
                                        type="number"
                                        min={0.5}
                                        max={5}
                                        step={0.5}
                                        value={retenueData.rate}
                                        onChange={(e) => setRetenueData(prev => ({ ...prev, rate: Math.min(5, parseFloat(e.target.value) || 0) }))}
                                        className="text-center"
                                    />
                                    <Percent className="w-4 h-4 text-slate-400" />
                                </div>
                            </div>
                        </div>
                        
                        <div className="space-y-2">
                            <Label>Durée de garantie (mois)</Label>
                            <Select
                                value={String(retenueData.warranty_months)}
                                onValueChange={(v) => setRetenueData(prev => ({ ...prev, warranty_months: parseInt(v) }))}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="6">6 mois</SelectItem>
                                    <SelectItem value="12">12 mois (1 an - standard)</SelectItem>
                                    <SelectItem value="24">24 mois (2 ans)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        
                        <div className="bg-slate-100 rounded-lg p-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Total TTC de la facture:</span>
                                <span className="font-medium">{fmt(invoice?.total_ttc || 0)}</span>
                            </div>
                            <div className="flex justify-between text-sm text-amber-700">
                                <span>Retenue de garantie ({retenueData.rate}%):</span>
                                <span className="font-medium">-{fmt((invoice?.total_ttc || 0) * retenueData.rate / 100)}</span>
                            </div>
                            <div className="flex justify-between text-lg font-bold border-t pt-2">
                                <span>Net à payer:</span>
                                <span className="text-emerald-600">{fmt((invoice?.total_ttc || 0) * (1 - retenueData.rate / 100))}</span>
                            </div>
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setShowRetenueModal(false)}>Annuler</Button>
                        <Button 
                            onClick={handleApplyRetenue} 
                            disabled={applyingRetenue}
                            className="bg-amber-600 hover:bg-amber-700"
                            data-testid="confirm-retenue-btn"
                        >
                            {applyingRetenue ? (
                                <><span className="spinner w-4 h-4 mr-2"></span>Application...</>
                            ) : (
                                <><Shield className="w-4 h-4 mr-2" />Appliquer la retenue</>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

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

            {/* Email Modal */}
            <Dialog open={showEmailModal} onOpenChange={setShowEmailModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Mail className="w-5 h-5 text-blue-600" />
                            Envoyer la facture par email
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <div className="space-y-2">
                            <Label>Adresse email du destinataire *</Label>
                            <Input
                                type="email"
                                placeholder="client@example.com"
                                value={emailData.recipient_email}
                                onChange={(e) => setEmailData(prev => ({ ...prev, recipient_email: e.target.value }))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Message personnalisé (optionnel)</Label>
                            <Textarea
                                placeholder="Un message à ajouter à l'email..."
                                value={emailData.custom_message}
                                onChange={(e) => setEmailData(prev => ({ ...prev, custom_message: e.target.value }))}
                                rows={3}
                            />
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                            <strong>Contenu :</strong> Facture n° {invoice?.invoice_number}, PDF joint, lien de consultation
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setShowEmailModal(false)}>Annuler</Button>
                        <Button onClick={handleSendEmail} disabled={sendingEmail} className="bg-blue-600 hover:bg-blue-700">
                            {sendingEmail ? <><span className="spinner w-4 h-4 mr-2"></span>Envoi...</> : <><Send className="w-4 h-4 mr-2" />Envoyer</>}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

export default InvoiceViewPage;
