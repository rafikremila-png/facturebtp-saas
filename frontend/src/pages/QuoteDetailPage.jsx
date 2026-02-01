import { useState, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { getQuote, updateQuote, convertQuoteToInvoice, downloadQuotePdf } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { ArrowLeft, Download, Pencil, FileCheck, Calendar, User, Euro } from "lucide-react";
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

    useEffect(() => {
        loadQuote();
    }, [id]);

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

    const handleDownloadPdf = async () => {
        try {
            await downloadQuotePdf(quote.id, quote.quote_number);
            toast.success("PDF téléchargé");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du PDF");
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
        </div>
    );
}
