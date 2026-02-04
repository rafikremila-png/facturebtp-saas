import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getQuote, updateQuote, convertQuoteToInvoice, downloadQuotePdf, createQuoteShareLink, sendQuoteEmail, createAcompte, getAcomptesSummary, createFinalInvoice } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ArrowLeft, Download, Pencil, FileCheck, Calendar, User, Euro, Share2, Copy, Check, Mail, Send, CreditCard, Receipt, Percent, PiggyBank, FileText } from "lucide-react";
import { toast } from "sonner";

const statusLabels = {
    brouillon: "Brouillon",
    envoye: "Envoyé",
    accepte: "Accepté",
    refuse: "Refusé",
    facture: "Facturé"
};

const statusOptions = ["brouillon", "envoye", "accepte", "refuse"];

export default function QuoteDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    
    const [quote, setQuote] = useState(null);
    const [loading, setLoading] = useState(true);
    const [converting, setConverting] = useState(false);
    const [showShareModal, setShowShareModal] = useState(false);
    const [shareUrl, setShareUrl] = useState("");
    const [copied, setCopied] = useState(false);
    const [showEmailModal, setShowEmailModal] = useState(false);
    const [emailData, setEmailData] = useState({ recipient_email: "", custom_message: "" });
    const [sendingEmail, setSendingEmail] = useState(false);
    // Acompte state
    const [acomptesSummary, setAcomptesSummary] = useState(null);
    const [showAcompteModal, setShowAcompteModal] = useState(false);
    const [acompteData, setAcompteData] = useState({ acompte_type: "percentage", value: 30, notes: "" });
    const [creatingAcompte, setCreatingAcompte] = useState(false);
    const [creatingFinal, setCreatingFinal] = useState(false);

    useEffect(() => {
        loadQuote();
    }, [id]);

    useEffect(() => {
        if (quote && quote.status !== 'brouillon') {
            loadAcomptesSummary();
        }
    }, [quote]);

    const loadQuote = async () => {
        try {
            const response = await getQuote(id);
            setQuote(response.data);
        } catch (error) {
            toast.error("Erreur lors du chargement du devis");
            navigate("/devis");
        } finally {
            setLoading(false);
        }
    };

    const loadAcomptesSummary = async () => {
        try {
            const response = await getAcomptesSummary(id);
            setAcomptesSummary(response.data);
        } catch (error) {
            console.error("Error loading acomptes summary:", error);
        }
    };

    const handleStatusChange = async (newStatus) => {
        try {
            await updateQuote(id, { status: newStatus });
            setQuote(prev => ({ ...prev, status: newStatus }));
            toast.success("Statut mis à jour");
        } catch (error) {
            toast.error("Erreur lors de la mise à jour du statut");
        }
    };

    const handleConvertToInvoice = async () => {
        setConverting(true);
        try {
            const response = await convertQuoteToInvoice(id);
            toast.success("Facture créée avec succès");
            navigate(`/factures/${response.data.id}`);
        } catch (error) {
            const message = error.response?.data?.detail || "Erreur lors de la conversion";
            toast.error(message);
        } finally {
            setConverting(false);
        }
    };

    const handleCreateAcompte = async () => {
        if (acompteData.value <= 0) {
            toast.error("Veuillez saisir une valeur positive");
            return;
        }
        
        setCreatingAcompte(true);
        try {
            const response = await createAcompte(id, {
                quote_id: id,
                acompte_type: acompteData.acompte_type,
                value: parseFloat(acompteData.value),
                notes: acompteData.notes
            });
            toast.success(`Facture d'acompte ${response.data.invoice_number} créée`);
            setShowAcompteModal(false);
            setAcompteData({ acompte_type: "percentage", value: 30, notes: "" });
            loadAcomptesSummary();
            navigate(`/factures/${response.data.id}`);
        } catch (error) {
            const message = error.response?.data?.detail || "Erreur lors de la création de l'acompte";
            toast.error(message);
        } finally {
            setCreatingAcompte(false);
        }
    };

    const handleCreateFinalInvoice = async () => {
        setCreatingFinal(true);
        try {
            const response = await createFinalInvoice(id);
            toast.success("Facture de solde créée avec succès");
            navigate(`/factures/${response.data.id}`);
        } catch (error) {
            const message = error.response?.data?.detail || "Erreur lors de la création de la facture";
            toast.error(message);
        } finally {
            setCreatingFinal(false);
        }
    };

    const handleDownloadPdf = async () => {
        try {
            await downloadQuotePdf(quote.id, quote.quote_number);
            toast.success("PDF téléchargé");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du PDF");
        }
    };

    const handleShare = async () => {
        try {
            const response = await createQuoteShareLink(quote.id);
            const baseUrl = window.location.origin;
            const fullUrl = `${baseUrl}/client/devis/${response.data.share_token}`;
            setShareUrl(fullUrl);
            setShowShareModal(true);
        } catch (error) {
            toast.error("Erreur lors de la création du lien de partage");
        }
    };

    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            toast.success("Lien copié dans le presse-papiers");
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            toast.error("Erreur lors de la copie");
        }
    };

    const handleSendEmail = async () => {
        if (!emailData.recipient_email) {
            toast.error("Veuillez saisir une adresse email");
            return;
        }
        
        setSendingEmail(true);
        try {
            await sendQuoteEmail(quote.id, emailData);
            toast.success("Devis envoyé par email");
            setShowEmailModal(false);
            setEmailData({ recipient_email: "", custom_message: "" });
            // Refresh quote to get updated status
            const response = await getQuote(id);
            setQuote(response.data);
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de l'envoi");
        } finally {
            setSendingEmail(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('fr-FR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    };

    const formatCurrency = (amount) => {
        return amount.toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    if (!quote) return null;

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="quote-detail-page">
            {/* Header */}
            <div className="flex items-center justify-between">
                <Button 
                    variant="ghost" 
                    onClick={() => navigate("/devis")}
                    data-testid="back-btn"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Retour
                </Button>
                <div className="flex gap-2">
                    <Button 
                        variant="outline"
                        onClick={() => setShowEmailModal(true)}
                        className="bg-blue-50 hover:bg-blue-100 border-blue-200"
                        data-testid="send-email-btn"
                    >
                        <Mail className="w-4 h-4 mr-2 text-blue-600" />
                        Envoyer par email
                    </Button>
                    <Button 
                        variant="outline"
                        onClick={handleShare}
                        data-testid="share-btn"
                    >
                        <Share2 className="w-4 h-4 mr-2" />
                        Partager
                    </Button>
                    <Button 
                        variant="outline"
                        onClick={handleDownloadPdf}
                        data-testid="download-pdf-btn"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Télécharger PDF
                    </Button>
                    <Link to={`/devis/${id}/edit`}>
                        <Button variant="outline" data-testid="edit-btn">
                            <Pencil className="w-4 h-4 mr-2" />
                            Modifier
                        </Button>
                    </Link>
                    {quote.status === "accepte" && (
                        <Button 
                            className="bg-green-600 hover:bg-green-700"
                            onClick={handleConvertToInvoice}
                            disabled={converting}
                            data-testid="convert-btn"
                        >
                            {converting ? (
                                <span className="flex items-center gap-2">
                                    <span className="spinner w-4 h-4"></span>
                                    Conversion...
                                </span>
                            ) : (
                                <>
                                    <FileCheck className="w-4 h-4 mr-2" />
                                    Convertir en facture
                                </>
                            )}
                        </Button>
                    )}
                </div>
            </div>

            {/* Main Info */}
            <Card>
                <CardHeader className="border-b">
                    <div className="flex items-start justify-between">
                        <div>
                            <CardTitle className="text-2xl font-['Barlow_Condensed'] font-mono">
                                {quote.quote_number}
                            </CardTitle>
                            <p className="text-slate-500 mt-1">Devis</p>
                        </div>
                        <div className="text-right">
                            {quote.status === "facture" ? (
                                <span className={`status-badge status-${quote.status}`}>
                                    {statusLabels[quote.status]}
                                </span>
                            ) : (
                                <Select value={quote.status} onValueChange={handleStatusChange}>
                                    <SelectTrigger className="w-40" data-testid="status-select">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {statusOptions.map(status => (
                                            <SelectItem key={status} value={status}>
                                                {statusLabels[status]}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <User className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">Client</p>
                                <p className="font-medium">{quote.client_name}</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                                <Calendar className="w-5 h-5 text-green-600" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">Date d'émission</p>
                                <p className="font-medium">{formatDate(quote.issue_date)}</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                                <Calendar className="w-5 h-5 text-amber-600" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">Validité jusqu'au</p>
                                <p className="font-medium">{formatDate(quote.validity_date)}</p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Line Items */}
            <Card>
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed']">Détail du devis</CardTitle>
                </CardHeader>
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
                            {quote.items.map((item, index) => (
                                <TableRow key={index} className="table-row-hover">
                                    <TableCell className="font-medium">{item.description}</TableCell>
                                    <TableCell className="text-right">{item.quantity}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                                    <TableCell className="text-right">{item.vat_rate}%</TableCell>
                                    <TableCell className="text-right font-medium">
                                        {formatCurrency(item.quantity * item.unit_price)}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Totals */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col items-end space-y-2">
                        <div className="flex gap-8 text-sm">
                            <span className="text-slate-500">Total HT:</span>
                            <span className="font-medium w-28 text-right">{formatCurrency(quote.total_ht)}</span>
                        </div>
                        <div className="flex gap-8 text-sm">
                            <span className="text-slate-500">Total TVA:</span>
                            <span className="font-medium w-28 text-right">{formatCurrency(quote.total_vat)}</span>
                        </div>
                        <div className="flex gap-8 text-xl font-bold pt-2 border-t">
                            <span className="text-slate-900">Total TTC:</span>
                            <span className="text-orange-600 w-28 text-right">{formatCurrency(quote.total_ttc)}</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Notes */}
            {quote.notes && (
                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed']">Notes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-slate-600 whitespace-pre-wrap">{quote.notes}</p>
                    </CardContent>
                </Card>
            )}

            {/* Share Modal */}
            <Dialog open={showShareModal} onOpenChange={setShowShareModal}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Share2 className="w-5 h-5 text-orange-600" />
                            Partager le devis
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <p className="text-sm text-slate-600">
                            Envoyez ce lien à votre client. Il pourra consulter et télécharger le devis sans créer de compte.
                        </p>
                        <div className="flex gap-2">
                            <Input 
                                value={shareUrl} 
                                readOnly 
                                className="flex-1 font-mono text-sm"
                                data-testid="share-url-input"
                            />
                            <Button onClick={copyToClipboard} variant="outline" data-testid="copy-btn">
                                {copied ? (
                                    <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                    <Copy className="w-4 h-4" />
                                )}
                            </Button>
                        </div>
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                            <strong>Note :</strong> Ce lien reste valide tant que vous ne le révoquez pas.
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
                            Envoyer le devis par email
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
                                data-testid="email-input"
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
                            <strong>Contenu de l'email :</strong>
                            <ul className="list-disc list-inside mt-1">
                                <li>Devis n° {quote?.quote_number}</li>
                                <li>PDF en pièce jointe</li>
                                <li>Lien pour consulter en ligne</li>
                            </ul>
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setShowEmailModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleSendEmail}
                            disabled={sendingEmail}
                            className="bg-blue-600 hover:bg-blue-700"
                            data-testid="confirm-send-email-btn"
                        >
                            {sendingEmail ? (
                                <>
                                    <span className="spinner w-4 h-4 mr-2"></span>
                                    Envoi...
                                </>
                            ) : (
                                <>
                                    <Send className="w-4 h-4 mr-2" />
                                    Envoyer
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
