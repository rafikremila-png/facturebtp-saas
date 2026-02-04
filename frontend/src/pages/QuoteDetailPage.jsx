import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getQuote, updateQuote, convertQuoteToInvoice, downloadQuotePdf, createQuoteShareLink, sendQuoteEmail, createAcompte, getAcomptesSummary, createFinalInvoice, createSituation, getSituationsSummary, createSituationFinalInvoice, getProjectFinancialSummary } from "@/lib/api";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { ArrowLeft, Download, Pencil, FileCheck, Calendar, User, Euro, Share2, Copy, Check, Mail, Send, CreditCard, Receipt, Percent, PiggyBank, FileText, HardHat, TrendingUp, ClipboardList, BarChart3 } from "lucide-react";
import { toast } from "sonner";
import ProjectFinancialSummary from "@/components/ProjectFinancialSummary";

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
    
    // Situation state
    const [situationsSummary, setSituationsSummary] = useState(null);
    const [showSituationModal, setShowSituationModal] = useState(false);
    const [situationData, setSituationData] = useState({ 
        situation_type: "global", 
        global_percentage: 30, 
        line_items: [],
        notes: "",
        chantier_ref: ""
    });
    const [creatingSituation, setCreatingSituation] = useState(false);
    const [creatingSituationFinal, setCreatingSituationFinal] = useState(false);
    
    // Financial summary state
    const [financialSummary, setFinancialSummary] = useState(null);
    const [showFinancialSummary, setShowFinancialSummary] = useState(false);
    const [loadingFinancialSummary, setLoadingFinancialSummary] = useState(false);

    useEffect(() => {
        loadQuote();
    }, [id]);

    useEffect(() => {
        if (quote && quote.status !== 'brouillon') {
            loadAcomptesSummary();
            loadSituationsSummary();
            loadFinancialSummary();
        }
    }, [quote]);

    // Initialize line_items when quote loads and modal opens
    useEffect(() => {
        if (quote && showSituationModal && situationData.situation_type === 'per_line') {
            initializeLineItems();
        }
    }, [quote, showSituationModal, situationData.situation_type]);
    
    const loadFinancialSummary = async () => {
        setLoadingFinancialSummary(true);
        try {
            const response = await getProjectFinancialSummary(id);
            setFinancialSummary(response.data);
        } catch (error) {
            console.error("Error loading financial summary:", error);
        } finally {
            setLoadingFinancialSummary(false);
        }
    };

    const initializeLineItems = () => {
        if (!quote) return;
        const previousProgress = situationsSummary?.line_progress || [];
        const lineItems = quote.items.map((item, index) => {
            const prevPct = previousProgress[index]?.cumulative_percent || 0;
            return {
                description: item.description,
                quantity: item.quantity,
                unit_price: item.unit_price,
                vat_rate: item.vat_rate,
                progress_percent: prevPct // Start at previous cumulative
            };
        });
        setSituationData(prev => ({ ...prev, line_items: lineItems }));
    };

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

    const loadSituationsSummary = async () => {
        try {
            const response = await getSituationsSummary(id);
            setSituationsSummary(response.data);
        } catch (error) {
            console.error("Error loading situations summary:", error);
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
    
    const handleCreateSituation = async () => {
        const currentProgress = situationsSummary?.current_progress_percentage || 0;
        
        if (situationData.situation_type === 'global') {
            if (situationData.global_percentage <= currentProgress) {
                toast.error(`Le % doit être supérieur au cumul actuel (${currentProgress}%)`);
                return;
            }
            if (situationData.global_percentage > 100) {
                toast.error("Le pourcentage ne peut pas dépasser 100%");
                return;
            }
        }
        
        setCreatingSituation(true);
        try {
            const payload = {
                quote_id: id,
                situation_type: situationData.situation_type,
                notes: situationData.notes,
                chantier_ref: situationData.chantier_ref || `Chantier ${quote?.quote_number}`
            };
            
            if (situationData.situation_type === 'global') {
                payload.global_percentage = parseFloat(situationData.global_percentage);
            } else {
                payload.line_items = situationData.line_items.map(item => ({
                    description: item.description,
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    vat_rate: item.vat_rate,
                    progress_percent: item.progress_percent
                }));
            }
            
            const response = await createSituation(id, payload);
            toast.success(`Situation n°${response.data.situation_number} créée`);
            setShowSituationModal(false);
            setSituationData({ 
                situation_type: "global", 
                global_percentage: 30, 
                line_items: [],
                notes: "",
                chantier_ref: ""
            });
            loadSituationsSummary();
            navigate(`/factures/${response.data.id}`);
        } catch (error) {
            const message = error.response?.data?.detail || "Erreur lors de la création de la situation";
            toast.error(message);
        } finally {
            setCreatingSituation(false);
        }
    };
    
    const handleCreateSituationFinalInvoice = async () => {
        setCreatingSituationFinal(true);
        try {
            const response = await createSituationFinalInvoice(id);
            toast.success("Décompte final créé avec succès");
            navigate(`/factures/${response.data.id}`);
        } catch (error) {
            const message = error.response?.data?.detail || "Erreur lors de la création du décompte final";
            toast.error(message);
        } finally {
            setCreatingSituationFinal(false);
        }
    };
    
    const updateLineItemProgress = (index, newValue) => {
        const newLineItems = [...situationData.line_items];
        newLineItems[index] = { ...newLineItems[index], progress_percent: newValue };
        setSituationData(prev => ({ ...prev, line_items: newLineItems }));
    };
    
    const openSituationModal = () => {
        // Initialize with a sensible default percentage (current + 10 or next 5% increment)
        const currentPct = situationsSummary?.current_progress_percentage || 0;
        const defaultPct = Math.min(100, Math.ceil((currentPct + 10) / 5) * 5);
        
        setSituationData({ 
            situation_type: "global", 
            global_percentage: defaultPct, 
            line_items: [],
            notes: "",
            chantier_ref: ""
        });
        setShowSituationModal(true);
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
                    {(quote.status === "accepte" || quote.status === "envoye") && (
                        <Button 
                            className="bg-purple-600 hover:bg-purple-700"
                            onClick={() => setShowAcompteModal(true)}
                            data-testid="create-acompte-btn"
                        >
                            <CreditCard className="w-4 h-4 mr-2" />
                            Acompte
                        </Button>
                    )}
                    {(quote.status === "accepte" || quote.status === "envoye") && (
                        <Button 
                            className="bg-emerald-600 hover:bg-emerald-700"
                            onClick={openSituationModal}
                            data-testid="create-situation-btn"
                        >
                            <HardHat className="w-4 h-4 mr-2" />
                            Situation
                        </Button>
                    )}
                    {quote.status !== "brouillon" && financialSummary && (
                        <Button 
                            variant={showFinancialSummary ? "default" : "outline"}
                            className={showFinancialSummary ? "bg-slate-800 hover:bg-slate-700" : ""}
                            onClick={() => setShowFinancialSummary(!showFinancialSummary)}
                            data-testid="toggle-financial-summary-btn"
                        >
                            <BarChart3 className="w-4 h-4 mr-2" />
                            {showFinancialSummary ? "Masquer récapitulatif" : "Récapitulatif financier"}
                        </Button>
                    )}
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
                                {quote.total_vat > 0 && <TableHead className="text-white font-semibold text-right">TVA</TableHead>}
                                <TableHead className="text-white font-semibold text-right">Total HT</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {quote.items.map((item, index) => (
                                <TableRow key={index} className="table-row-hover">
                                    <TableCell className="font-medium">{item.description}</TableCell>
                                    <TableCell className="text-right">{item.quantity}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                                    {quote.total_vat > 0 && <TableCell className="text-right">{item.vat_rate}%</TableCell>}
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
                        {quote.total_vat > 0 ? (
                            <>
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
                            </>
                        ) : (
                            <>
                                <div className="flex gap-8 text-xl font-bold">
                                    <span className="text-slate-900">Total:</span>
                                    <span className="text-orange-600 w-28 text-right">{formatCurrency(quote.total_ht)}</span>
                                </div>
                                <p className="text-xs text-slate-500 italic">TVA non applicable, art. 293B du CGI</p>
                            </>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Acomptes Section */}
            {acomptesSummary && acomptesSummary.acomptes_count > 0 && (
                <Card className="border-purple-200 bg-purple-50/30">
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                            <PiggyBank className="w-5 h-5 text-purple-600" />
                            Acomptes ({acomptesSummary.acomptes_count})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Progress bar */}
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Progression des paiements</span>
                                <span className="font-medium">{acomptesSummary.percentage_invoiced}% facturé</span>
                            </div>
                            <Progress value={acomptesSummary.percentage_invoiced} className="h-3" />
                        </div>

                        {/* Acomptes list */}
                        <div className="space-y-2">
                            {acomptesSummary.acomptes.map((acompte) => (
                                <div key={acompte.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                            acompte.payment_status === 'paye' ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'
                                        }`}>
                                            {acompte.acompte_number}
                                        </div>
                                        <div>
                                            <p className="font-medium text-slate-900">{acompte.invoice_number}</p>
                                            <p className="text-sm text-slate-500">
                                                {acompte.acompte_type === 'percentage' ? `${acompte.acompte_value}%` : `${acompte.acompte_value}€`}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold text-slate-900">{formatCurrency(acompte.total_ttc)}</p>
                                        <span className={`text-xs px-2 py-1 rounded ${
                                            acompte.payment_status === 'paye' 
                                                ? 'bg-green-100 text-green-700' 
                                                : 'bg-amber-100 text-amber-700'
                                        }`}>
                                            {acompte.payment_status === 'paye' ? 'Payé' : 'En attente'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Summary */}
                        <div className="border-t pt-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Total des acomptes:</span>
                                <span className="font-medium">{formatCurrency(acomptesSummary.total_acomptes_ttc)}</span>
                            </div>
                            <div className="flex justify-between text-lg font-bold">
                                <span className="text-slate-900">Solde restant:</span>
                                <span className="text-purple-600">{formatCurrency(acomptesSummary.remaining_ttc)}</span>
                            </div>
                        </div>

                        {/* Action buttons */}
                        {quote.status === "accepte" && acomptesSummary.remaining_ttc > 0 && (
                            <div className="flex gap-2 pt-2">
                                <Button 
                                    variant="outline"
                                    onClick={() => setShowAcompteModal(true)}
                                    className="border-purple-300 text-purple-700 hover:bg-purple-100"
                                >
                                    <CreditCard className="w-4 h-4 mr-2" />
                                    Nouvel acompte
                                </Button>
                                <Button 
                                    className="bg-green-600 hover:bg-green-700"
                                    onClick={handleCreateFinalInvoice}
                                    disabled={creatingFinal}
                                >
                                    <FileText className="w-4 h-4 mr-2" />
                                    Créer facture de solde
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Situations Section */}
            {situationsSummary && situationsSummary.situations_count > 0 && (
                <Card className="border-emerald-200 bg-emerald-50/30">
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                            <HardHat className="w-5 h-5 text-emerald-600" />
                            Situations de travaux ({situationsSummary.situations_count})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Progress bar */}
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-600">Avancement du chantier</span>
                                <span className="font-medium">{situationsSummary.current_progress_percentage}% réalisé</span>
                            </div>
                            <Progress value={situationsSummary.current_progress_percentage} className="h-3 bg-emerald-100">
                                <div 
                                    className="h-full bg-emerald-500 transition-all" 
                                    style={{ width: `${situationsSummary.current_progress_percentage}%` }}
                                />
                            </Progress>
                        </div>

                        {/* Situations list */}
                        <div className="space-y-2">
                            {situationsSummary.situations.map((situation) => (
                                <Link key={situation.id} to={`/factures/${situation.id}`} className="block">
                                    <div className="flex items-center justify-between p-3 bg-white rounded-lg border hover:border-emerald-300 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                                situation.payment_status === 'paye' ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'
                                            }`}>
                                                {situation.situation_number}
                                            </div>
                                            <div>
                                                <p className="font-medium text-slate-900">{situation.invoice_number}</p>
                                                <p className="text-sm text-slate-500 flex items-center gap-1">
                                                    <TrendingUp className="w-3 h-3" />
                                                    Cumul: {situation.cumulative_percentage}%
                                                    <span className="text-xs text-slate-400">
                                                        ({situation.situation_type === 'global' ? 'global' : 'par ligne'})
                                                    </span>
                                                </p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold text-slate-900">{formatCurrency(situation.total_ttc)}</p>
                                            <span className={`text-xs px-2 py-1 rounded ${
                                                situation.payment_status === 'paye' 
                                                    ? 'bg-green-100 text-green-700' 
                                                    : 'bg-amber-100 text-amber-700'
                                            }`}>
                                                {situation.payment_status === 'paye' ? 'Payé' : 'En attente'}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>

                        {/* Summary */}
                        <div className="border-t pt-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Total facturé:</span>
                                <span className="font-medium">{formatCurrency(situationsSummary.total_situations_ttc)}</span>
                            </div>
                            <div className="flex justify-between text-lg font-bold">
                                <span className="text-slate-900">Reste à facturer:</span>
                                <span className="text-emerald-600">{formatCurrency(situationsSummary.remaining_ttc)}</span>
                            </div>
                        </div>

                        {/* Action buttons */}
                        {quote.status === "accepte" && situationsSummary.remaining_ttc > 0 && (
                            <div className="flex gap-2 pt-2">
                                <Button 
                                    variant="outline"
                                    onClick={openSituationModal}
                                    className="border-emerald-300 text-emerald-700 hover:bg-emerald-100"
                                >
                                    <TrendingUp className="w-4 h-4 mr-2" />
                                    Nouvelle situation
                                </Button>
                                {situationsSummary.current_progress_percentage >= 100 && (
                                    <Button 
                                        className="bg-green-600 hover:bg-green-700"
                                        onClick={handleCreateSituationFinalInvoice}
                                        disabled={creatingSituationFinal}
                                    >
                                        <FileText className="w-4 h-4 mr-2" />
                                        Décompte final
                                    </Button>
                                )}
                            </div>
                        )}
                        
                        {/* Final invoice button when 100% reached */}
                        {quote.status === "accepte" && situationsSummary.current_progress_percentage >= 100 && (
                            <div className="bg-emerald-100 border border-emerald-300 rounded-lg p-3">
                                <p className="text-sm text-emerald-800 mb-2">
                                    <strong>Chantier terminé !</strong> Vous pouvez créer le décompte final.
                                </p>
                                <Button 
                                    className="bg-emerald-600 hover:bg-emerald-700 w-full"
                                    onClick={handleCreateSituationFinalInvoice}
                                    disabled={creatingSituationFinal}
                                >
                                    {creatingSituationFinal ? (
                                        <span className="flex items-center gap-2">
                                            <span className="spinner w-4 h-4"></span>
                                            Création...
                                        </span>
                                    ) : (
                                        <>
                                            <ClipboardList className="w-4 h-4 mr-2" />
                                            Créer le décompte final
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

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

            {/* Acompte Modal */}
            <Dialog open={showAcompteModal} onOpenChange={setShowAcompteModal}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <CreditCard className="w-5 h-5 text-purple-600" />
                            Créer un acompte
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <div className="bg-purple-50 rounded-lg p-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Total du devis:</span>
                                <span className="font-bold">{formatCurrency(quote?.total_ttc || 0)}</span>
                            </div>
                            {acomptesSummary && acomptesSummary.acomptes_count > 0 && (
                                <>
                                    <div className="flex justify-between text-sm">
                                        <span>Déjà facturé:</span>
                                        <span className="font-medium text-purple-600">-{formatCurrency(acomptesSummary.total_acomptes_ttc)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm font-bold border-t pt-2">
                                        <span>Restant:</span>
                                        <span>{formatCurrency(acomptesSummary.remaining_ttc)}</span>
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="space-y-3">
                            <Label>Type d'acompte</Label>
                            <RadioGroup 
                                value={acompteData.acompte_type} 
                                onValueChange={(v) => setAcompteData(prev => ({ ...prev, acompte_type: v }))}
                                className="flex gap-4"
                            >
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="percentage" id="percentage" />
                                    <Label htmlFor="percentage" className="flex items-center gap-1 cursor-pointer">
                                        <Percent className="w-4 h-4" />
                                        Pourcentage
                                    </Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="amount" id="amount" />
                                    <Label htmlFor="amount" className="flex items-center gap-1 cursor-pointer">
                                        <Euro className="w-4 h-4" />
                                        Montant fixe
                                    </Label>
                                </div>
                            </RadioGroup>
                        </div>

                        <div className="space-y-2">
                            <Label>
                                {acompteData.acompte_type === 'percentage' ? 'Pourcentage (%)' : 'Montant (€ TTC)'}
                            </Label>
                            <div className="flex items-center gap-2">
                                <Input
                                    type="number"
                                    min="0"
                                    max={acompteData.acompte_type === 'percentage' ? 100 : (acomptesSummary?.remaining_ttc || quote?.total_ttc)}
                                    step={acompteData.acompte_type === 'percentage' ? 5 : 100}
                                    value={acompteData.value}
                                    onChange={(e) => setAcompteData(prev => ({ ...prev, value: parseFloat(e.target.value) || 0 }))}
                                    className="flex-1"
                                    data-testid="acompte-value-input"
                                />
                                <span className="text-lg font-medium w-8">
                                    {acompteData.acompte_type === 'percentage' ? '%' : '€'}
                                </span>
                            </div>
                            {/* Preview */}
                            <p className="text-sm text-slate-500">
                                = {formatCurrency(
                                    acompteData.acompte_type === 'percentage'
                                        ? ((quote?.total_ttc || 0) * (acompteData.value / 100))
                                        : acompteData.value
                                )} TTC
                            </p>
                        </div>

                        {/* Quick buttons */}
                        {acompteData.acompte_type === 'percentage' && (
                            <div className="flex gap-2 flex-wrap">
                                {[30, 40, 50].map(pct => (
                                    <Button
                                        key={pct}
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setAcompteData(prev => ({ ...prev, value: pct }))}
                                        className={acompteData.value === pct ? 'border-purple-500 bg-purple-50' : ''}
                                    >
                                        {pct}%
                                    </Button>
                                ))}
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label>Notes (optionnel)</Label>
                            <Textarea
                                placeholder="Notes pour la facture d'acompte..."
                                value={acompteData.notes}
                                onChange={(e) => setAcompteData(prev => ({ ...prev, notes: e.target.value }))}
                                rows={2}
                            />
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setShowAcompteModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleCreateAcompte}
                            disabled={creatingAcompte || acompteData.value <= 0}
                            className="bg-purple-600 hover:bg-purple-700"
                            data-testid="confirm-create-acompte-btn"
                        >
                            {creatingAcompte ? (
                                <>
                                    <span className="spinner w-4 h-4 mr-2"></span>
                                    Création...
                                </>
                            ) : (
                                <>
                                    <Receipt className="w-4 h-4 mr-2" />
                                    Créer la facture d'acompte
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Situation Modal */}
            <Dialog open={showSituationModal} onOpenChange={setShowSituationModal}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <HardHat className="w-5 h-5 text-emerald-600" />
                            Créer une situation de travaux
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        {/* Summary */}
                        <div className="bg-emerald-50 rounded-lg p-4 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Total du devis:</span>
                                <span className="font-bold">{formatCurrency(quote?.total_ttc || 0)}</span>
                            </div>
                            {situationsSummary && situationsSummary.situations_count > 0 && (
                                <>
                                    <div className="flex justify-between text-sm">
                                        <span>Avancement actuel:</span>
                                        <span className="font-medium text-emerald-600">{situationsSummary.current_progress_percentage}%</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span>Déjà facturé:</span>
                                        <span className="font-medium">-{formatCurrency(situationsSummary.total_situations_ttc)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm font-bold border-t pt-2">
                                        <span>Restant:</span>
                                        <span>{formatCurrency(situationsSummary.remaining_ttc)}</span>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Type selection */}
                        <div className="space-y-3">
                            <Label>Type de situation</Label>
                            <Tabs 
                                value={situationData.situation_type} 
                                onValueChange={(v) => {
                                    setSituationData(prev => ({ ...prev, situation_type: v }));
                                    if (v === 'per_line') {
                                        initializeLineItems();
                                    }
                                }}
                            >
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="global" className="flex items-center gap-2">
                                        <Percent className="w-4 h-4" />
                                        % Global
                                    </TabsTrigger>
                                    <TabsTrigger value="per_line" className="flex items-center gap-2">
                                        <ClipboardList className="w-4 h-4" />
                                        Par ligne
                                    </TabsTrigger>
                                </TabsList>

                                <TabsContent value="global" className="mt-4 space-y-4">
                                    <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600">
                                        <strong>Mode global :</strong> Appliquer un pourcentage d'avancement identique sur l'ensemble du devis.
                                    </div>
                                    
                                    <div className="space-y-3">
                                        <Label>Avancement cumulé (%)</Label>
                                        <div className="flex items-center gap-4">
                                            <Slider
                                                value={[situationData.global_percentage]}
                                                onValueChange={(v) => setSituationData(prev => ({ ...prev, global_percentage: v[0] }))}
                                                min={situationsSummary?.current_progress_percentage || 0}
                                                max={100}
                                                step={5}
                                                className="flex-1"
                                            />
                                            <div className="flex items-center gap-2 w-24">
                                                <Input
                                                    type="number"
                                                    min={situationsSummary?.current_progress_percentage || 0}
                                                    max={100}
                                                    value={situationData.global_percentage}
                                                    onChange={(e) => setSituationData(prev => ({ ...prev, global_percentage: parseFloat(e.target.value) || 0 }))}
                                                    className="text-center"
                                                    data-testid="situation-global-percentage"
                                                />
                                                <span className="font-medium">%</span>
                                            </div>
                                        </div>
                                        
                                        {/* Quick buttons */}
                                        <div className="flex gap-2 flex-wrap">
                                            {[25, 50, 75, 100].filter(p => p > (situationsSummary?.current_progress_percentage || 0)).map(pct => (
                                                <Button
                                                    key={pct}
                                                    type="button"
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => setSituationData(prev => ({ ...prev, global_percentage: pct }))}
                                                    className={situationData.global_percentage === pct ? 'border-emerald-500 bg-emerald-50' : ''}
                                                >
                                                    {pct}%
                                                </Button>
                                            ))}
                                        </div>
                                        
                                        {/* Preview */}
                                        <div className="bg-white border rounded-lg p-3 space-y-1">
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-500">Cette situation:</span>
                                                <span className="font-medium">
                                                    {(situationData.global_percentage - (situationsSummary?.current_progress_percentage || 0)).toFixed(1)}% 
                                                    ({formatCurrency(
                                                        ((quote?.total_ttc || 0) * ((situationData.global_percentage - (situationsSummary?.current_progress_percentage || 0)) / 100))
                                                    )} TTC)
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-500">Après cette situation:</span>
                                                <span className="font-bold text-emerald-600">{situationData.global_percentage}% d'avancement</span>
                                            </div>
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="per_line" className="mt-4 space-y-4">
                                    <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600">
                                        <strong>Mode par ligne :</strong> Définir l'avancement pour chaque poste du devis individuellement.
                                    </div>
                                    
                                    <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                                        {situationData.line_items.map((item, index) => {
                                            const prevPct = situationsSummary?.line_progress?.[index]?.cumulative_percent || 0;
                                            return (
                                                <div key={index} className="bg-white border rounded-lg p-3 space-y-2">
                                                    <div className="flex justify-between items-start">
                                                        <p className="font-medium text-sm text-slate-900 flex-1 pr-2">{item.description}</p>
                                                        <span className="text-xs text-slate-500 whitespace-nowrap">
                                                            {formatCurrency(item.quantity * item.unit_price)} HT
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <Slider
                                                            value={[item.progress_percent]}
                                                            onValueChange={(v) => updateLineItemProgress(index, v[0])}
                                                            min={prevPct}
                                                            max={100}
                                                            step={5}
                                                            className="flex-1"
                                                        />
                                                        <div className="flex items-center gap-1 w-20">
                                                            <Input
                                                                type="number"
                                                                min={prevPct}
                                                                max={100}
                                                                value={item.progress_percent}
                                                                onChange={(e) => updateLineItemProgress(index, parseFloat(e.target.value) || prevPct)}
                                                                className="text-center text-sm h-8"
                                                            />
                                                            <span className="text-sm">%</span>
                                                        </div>
                                                    </div>
                                                    {prevPct > 0 && (
                                                        <p className="text-xs text-slate-400">Cumul précédent: {prevPct}%</p>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </div>

                        {/* Site reference */}
                        <div className="space-y-2">
                            <Label>Référence chantier (optionnel)</Label>
                            <Input
                                placeholder={`Chantier ${quote?.quote_number || ''}`}
                                value={situationData.chantier_ref}
                                onChange={(e) => setSituationData(prev => ({ ...prev, chantier_ref: e.target.value }))}
                            />
                        </div>

                        {/* Notes */}
                        <div className="space-y-2">
                            <Label>Notes (optionnel)</Label>
                            <Textarea
                                placeholder="Notes pour la situation de travaux..."
                                value={situationData.notes}
                                onChange={(e) => setSituationData(prev => ({ ...prev, notes: e.target.value }))}
                                rows={2}
                            />
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button variant="outline" onClick={() => setShowSituationModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleCreateSituation}
                            disabled={creatingSituation}
                            className="bg-emerald-600 hover:bg-emerald-700"
                            data-testid="confirm-create-situation-btn"
                        >
                            {creatingSituation ? (
                                <>
                                    <span className="spinner w-4 h-4 mr-2"></span>
                                    Création...
                                </>
                            ) : (
                                <>
                                    <HardHat className="w-4 h-4 mr-2" />
                                    Créer la situation
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
