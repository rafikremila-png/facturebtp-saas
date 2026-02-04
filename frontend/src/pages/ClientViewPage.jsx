import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getPublicQuote, getPublicInvoice, downloadPublicQuotePdf, downloadPublicInvoicePdf } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Download, Building2, Calendar, Euro, CheckCircle, Clock, XCircle, AlertCircle } from "lucide-react";

export default function ClientViewPage() {
    const { type, token } = useParams();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [document, setDocument] = useState(null);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        loadDocument();
    }, [type, token]);

    const loadDocument = async () => {
        try {
            setLoading(true);
            setError(null);
            
            let response;
            if (type === "devis") {
                response = await getPublicQuote(token);
            } else if (type === "facture") {
                response = await getPublicInvoice(token);
            } else {
                throw new Error("Type de document invalide");
            }
            
            setDocument(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || "Document non trouvé ou lien expiré");
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadPdf = async () => {
        setDownloading(true);
        try {
            if (type === "devis") {
                await downloadPublicQuotePdf(token);
            } else {
                await downloadPublicInvoicePdf(token);
            }
        } catch (err) {
            setError("Erreur lors du téléchargement");
        } finally {
            setDownloading(false);
        }
    };

    const getStatusBadge = () => {
        if (!document) return null;
        
        if (type === "devis") {
            const statusConfig = {
                brouillon: { color: "bg-slate-500", icon: FileText },
                envoye: { color: "bg-blue-500", icon: Clock },
                accepte: { color: "bg-green-500", icon: CheckCircle },
                refuse: { color: "bg-red-500", icon: XCircle },
                facture: { color: "bg-purple-500", icon: CheckCircle }
            };
            const config = statusConfig[document.status] || statusConfig.brouillon;
            const Icon = config.icon;
            return (
                <Badge className={`${config.color} text-white px-3 py-1 text-sm`}>
                    <Icon className="w-4 h-4 mr-1" />
                    {document.status_label}
                </Badge>
            );
        } else {
            const statusConfig = {
                impaye: { color: "bg-amber-500", icon: AlertCircle },
                partiel: { color: "bg-blue-500", icon: Clock },
                paye: { color: "bg-green-500", icon: CheckCircle }
            };
            const config = statusConfig[document.payment_status] || statusConfig.impaye;
            const Icon = config.icon;
            return (
                <Badge className={`${config.color} text-white px-3 py-1 text-sm`}>
                    <Icon className="w-4 h-4 mr-1" />
                    {document.payment_status_label}
                </Badge>
            );
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="spinner mx-auto mb-4"></div>
                    <p className="text-slate-500">Chargement du document...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
                <Card className="max-w-md w-full">
                    <CardContent className="pt-6 text-center">
                        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <XCircle className="w-8 h-8 text-red-600" />
                        </div>
                        <h2 className="text-xl font-semibold text-slate-900 mb-2">Document non disponible</h2>
                        <p className="text-slate-500">{error}</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 py-8 px-4">
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="flex items-center justify-center gap-2 mb-2">
                        <Building2 className="w-6 h-6 text-orange-600" />
                        <h1 className="text-2xl font-bold text-slate-900">
                            {document.company?.name || "BTP Facture"}
                        </h1>
                    </div>
                    {document.company?.address && (
                        <p className="text-slate-500 text-sm">{document.company.address}</p>
                    )}
                </div>

                {/* Document Info */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-4">
                        <div>
                            <CardTitle className="text-2xl font-bold text-slate-900 flex items-center gap-3">
                                <FileText className="w-6 h-6 text-orange-600" />
                                {type === "devis" ? "Devis" : "Facture"} N° {document.document_number}
                            </CardTitle>
                            <p className="text-slate-500 mt-1">
                                Pour : <span className="font-medium text-slate-700">{document.client_name}</span>
                            </p>
                        </div>
                        {getStatusBadge()}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex flex-wrap gap-6 text-sm">
                            <div className="flex items-center gap-2">
                                <Calendar className="w-4 h-4 text-slate-400" />
                                <span className="text-slate-500">Date d'émission :</span>
                                <span className="font-medium">{new Date(document.issue_date).toLocaleDateString('fr-FR')}</span>
                            </div>
                            {type === "devis" && document.validity_date && (
                                <div className="flex items-center gap-2">
                                    <Clock className="w-4 h-4 text-slate-400" />
                                    <span className="text-slate-500">Valide jusqu'au :</span>
                                    <span className="font-medium">{new Date(document.validity_date).toLocaleDateString('fr-FR')}</span>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Items Table */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Détail des prestations</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b bg-slate-50">
                                        <th className="text-left py-3 px-4 font-semibold">Description</th>
                                        <th className="text-right py-3 px-4 font-semibold">Qté</th>
                                        <th className="text-right py-3 px-4 font-semibold">Prix unit. HT</th>
                                        <th className="text-right py-3 px-4 font-semibold">TVA</th>
                                        <th className="text-right py-3 px-4 font-semibold">Total HT</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {document.items?.map((item, index) => (
                                        <tr key={index} className="border-b">
                                            <td className="py-3 px-4">{item.description}</td>
                                            <td className="py-3 px-4 text-right">{item.quantity}</td>
                                            <td className="py-3 px-4 text-right">{item.unit_price?.toFixed(2)} €</td>
                                            <td className="py-3 px-4 text-right">{item.vat_rate}%</td>
                                            <td className="py-3 px-4 text-right font-medium">
                                                {(item.quantity * item.unit_price).toFixed(2)} €
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Totals */}
                        <div className="mt-6 border-t pt-4 space-y-2">
                            <div className="flex justify-end gap-8 text-sm">
                                <span className="text-slate-500">Total HT :</span>
                                <span className="font-medium w-28 text-right">{document.total_ht?.toFixed(2)} €</span>
                            </div>
                            <div className="flex justify-end gap-8 text-sm">
                                <span className="text-slate-500">Total TVA :</span>
                                <span className="font-medium w-28 text-right">{document.total_vat?.toFixed(2)} €</span>
                            </div>
                            <div className="flex justify-end gap-8 text-lg font-bold border-t pt-2 mt-2">
                                <span>Total TTC :</span>
                                <span className="text-orange-600 w-28 text-right">{document.total_ttc?.toFixed(2)} €</span>
                            </div>
                            {type === "facture" && document.paid_amount > 0 && (
                                <>
                                    <div className="flex justify-end gap-8 text-sm text-green-600">
                                        <span>Montant payé :</span>
                                        <span className="font-medium w-28 text-right">-{document.paid_amount?.toFixed(2)} €</span>
                                    </div>
                                    <div className="flex justify-end gap-8 text-lg font-bold text-amber-600">
                                        <span>Reste à payer :</span>
                                        <span className="w-28 text-right">{(document.total_ttc - document.paid_amount).toFixed(2)} €</span>
                                    </div>
                                </>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Notes */}
                {document.notes && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Notes</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-slate-600 whitespace-pre-wrap">{document.notes}</p>
                        </CardContent>
                    </Card>
                )}

                {/* Download Button */}
                <div className="flex justify-center pt-4">
                    <Button 
                        onClick={handleDownloadPdf} 
                        className="bg-orange-600 hover:bg-orange-700 px-8 py-6 text-lg"
                        disabled={downloading}
                    >
                        {downloading ? (
                            <>
                                <span className="spinner w-5 h-5 mr-2"></span>
                                Téléchargement...
                            </>
                        ) : (
                            <>
                                <Download className="w-5 h-5 mr-2" />
                                Télécharger le PDF
                            </>
                        )}
                    </Button>
                </div>

                {/* Legal Footer */}
                <div className="text-center text-xs text-slate-400 pt-8 border-t">
                    {document.company?.siret && <p>SIRET : {document.company.siret}</p>}
                    {document.company?.vat_number && <p>N° TVA : {document.company.vat_number}</p>}
                    {document.company?.phone && <p>Tél : {document.company.phone}</p>}
                    {document.company?.email && <p>Email : {document.company.email}</p>}
                </div>
            </div>
        </div>
    );
}
