import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  FileText,
  Receipt,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Loader2,
  Euro,
  Calendar,
  Download,
  PenTool,
  Building2,
  User,
  Mail,
  Trash2,
  RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status configurations
const QUOTE_STATUS_CONFIG = {
  draft: { label: 'Brouillon', color: 'bg-slate-100 text-slate-800', icon: Clock },
  sent: { label: 'Envoyé', color: 'bg-blue-100 text-blue-800', icon: FileText },
  signed: { label: 'Signé', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  accepted: { label: 'Accepté', color: 'bg-green-500 text-white', icon: CheckCircle },
  rejected: { label: 'Refusé', color: 'bg-red-100 text-red-800', icon: XCircle },
  expired: { label: 'Expiré', color: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
};

const INVOICE_STATUS_CONFIG = {
  draft: { label: 'Brouillon', color: 'bg-slate-100 text-slate-800' },
  sent: { label: 'Envoyée', color: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Payée', color: 'bg-green-500 text-white' },
  partial: { label: 'Partielle', color: 'bg-yellow-100 text-yellow-800' },
  overdue: { label: 'En retard', color: 'bg-red-500 text-white' },
  cancelled: { label: 'Annulée', color: 'bg-slate-500 text-white' },
};

export default function ClientPortalPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [portalData, setPortalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Signature modal state
  const [showSignModal, setShowSignModal] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [signing, setSigning] = useState(false);
  const [signatureForm, setSignatureForm] = useState({
    signer_name: '',
    signer_email: '',
    signer_title: ''
  });
  
  // Signature canvas
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);

  useEffect(() => {
    if (token) {
      loadPortalData();
    }
  }, [token]);

  const loadPortalData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_URL}/api/portal/${token}`);
      setPortalData(response.data);
      
      // Pre-fill signer info if available
      if (response.data.client) {
        setSignatureForm(prev => ({
          ...prev,
          signer_name: response.data.client.name || '',
          signer_email: response.data.client.email || ''
        }));
      }
    } catch (err) {
      console.error('Error loading portal:', err);
      if (err.response?.status === 404) {
        setError('Lien invalide ou expiré. Veuillez demander un nouveau lien à votre prestataire.');
      } else {
        setError('Erreur lors du chargement du portail');
      }
    } finally {
      setLoading(false);
    }
  };

  // Canvas drawing functions
  const initCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    setHasSignature(false);
  };

  const startDrawing = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasSignature(true);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearSignature = () => {
    initCanvas();
  };

  const getSignatureData = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    return canvas.toDataURL('image/png');
  };

  const openSignModal = (quote) => {
    setSelectedQuote(quote);
    setShowSignModal(true);
    setTimeout(initCanvas, 100);
  };

  const handleSign = async () => {
    if (!selectedQuote) return;
    
    if (!signatureForm.signer_name.trim()) {
      toast.error('Veuillez entrer votre nom');
      return;
    }
    
    if (!signatureForm.signer_email.trim()) {
      toast.error('Veuillez entrer votre email');
      return;
    }
    
    if (!hasSignature) {
      toast.error('Veuillez dessiner votre signature');
      return;
    }
    
    setSigning(true);
    try {
      const signatureData = getSignatureData();
      
      await axios.post(`${API_URL}/api/portal/${token}/quotes/${selectedQuote.id}/sign`, {
        signer_name: signatureForm.signer_name,
        signer_email: signatureForm.signer_email,
        signer_title: signatureForm.signer_title || null,
        signature_data: signatureData
      });
      
      toast.success('Devis signé avec succès !');
      setShowSignModal(false);
      loadPortalData();
    } catch (err) {
      console.error('Error signing quote:', err);
      toast.error(err.response?.data?.detail || 'Erreur lors de la signature');
    } finally {
      setSigning(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-orange-600 mx-auto" />
          <p className="mt-4 text-slate-600">Chargement du portail client...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="w-16 h-16 text-orange-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-900 mb-2">Accès impossible</h2>
            <p className="text-slate-500 mb-4">{error}</p>
            <Button variant="outline" onClick={() => window.location.reload()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Réessayer
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!portalData) return null;

  const { client, quotes, invoices, pending_signatures, unpaid_invoices } = portalData;

  return (
    <div className="min-h-screen bg-slate-50" data-testid="client-portal-page">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 bg-orange-500 rounded-lg flex items-center justify-center">
              <Building2 className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-['Barlow_Condensed']">Portail Client</h1>
              <p className="text-slate-300">{client.company_name || client.name}</p>
            </div>
          </div>
          
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-sm text-slate-300">Devis en attente</p>
              <p className="text-2xl font-bold">{pending_signatures.length}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-sm text-slate-300">Factures à payer</p>
              <p className="text-2xl font-bold">{unpaid_invoices.length}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-sm text-slate-300">Total devis</p>
              <p className="text-2xl font-bold">{quotes.length}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-sm text-slate-300">Total factures</p>
              <p className="text-2xl font-bold">{invoices.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Pending Signatures Alert */}
        {pending_signatures.length > 0 && (
          <Card className="mb-6 border-orange-200 bg-orange-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <PenTool className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-orange-900">
                    {pending_signatures.length} devis à signer
                  </h3>
                  <p className="text-sm text-orange-700 mt-1">
                    Signez vos devis électroniquement pour confirmer votre accord.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs defaultValue="quotes" className="space-y-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="quotes" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Devis ({quotes.length})
            </TabsTrigger>
            <TabsTrigger value="invoices" className="flex items-center gap-2">
              <Receipt className="w-4 h-4" />
              Factures ({invoices.length})
            </TabsTrigger>
          </TabsList>

          {/* Quotes Tab */}
          <TabsContent value="quotes" className="space-y-4">
            {quotes.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">Aucun devis</p>
                </CardContent>
              </Card>
            ) : (
              quotes.map((quote) => {
                const statusInfo = QUOTE_STATUS_CONFIG[quote.status] || QUOTE_STATUS_CONFIG.draft;
                const canSign = ['draft', 'sent'].includes(quote.status);
                
                return (
                  <Card key={quote.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <h3 className="font-semibold text-lg text-slate-900">
                              {quote.quote_number}
                            </h3>
                            <Badge className={statusInfo.color}>
                              {statusInfo.label}
                            </Badge>
                            {quote.is_signed && (
                              <Badge className="bg-green-500 text-white">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Signé
                              </Badge>
                            )}
                          </div>
                          
                          {quote.title && (
                            <p className="text-slate-600 mb-2">{quote.title}</p>
                          )}
                          
                          <div className="flex items-center gap-4 text-sm text-slate-500 flex-wrap">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(quote.quote_date)}
                            </span>
                            {quote.validity_date && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                Valide jusqu'au {formatDate(quote.validity_date)}
                              </span>
                            )}
                          </div>
                          
                          {quote.signature && (
                            <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                              <p className="text-sm text-green-800">
                                <CheckCircle className="w-4 h-4 inline mr-1" />
                                Signé par <strong>{quote.signature.signer_name}</strong> le {formatDate(quote.signature.signed_at)}
                              </p>
                            </div>
                          )}
                        </div>
                        
                        <div className="text-right">
                          <p className="text-2xl font-bold text-orange-600">
                            {formatCurrency(quote.total_ttc)}
                          </p>
                          <p className="text-sm text-slate-500">TTC</p>
                          
                          <div className="flex gap-2 mt-4">
                            {canSign && !quote.is_signed && (
                              <Button 
                                onClick={() => openSignModal(quote)}
                                className="bg-orange-600 hover:bg-orange-700"
                                data-testid={`sign-quote-${quote.id}`}
                              >
                                <PenTool className="w-4 h-4 mr-2" />
                                Signer
                              </Button>
                            )}
                            {quote.pdf_url && (
                              <Button variant="outline" asChild>
                                <a href={quote.pdf_url} target="_blank" rel="noopener noreferrer">
                                  <Download className="w-4 h-4 mr-2" />
                                  PDF
                                </a>
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>

          {/* Invoices Tab */}
          <TabsContent value="invoices" className="space-y-4">
            {invoices.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Receipt className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">Aucune facture</p>
                </CardContent>
              </Card>
            ) : (
              invoices.map((invoice) => {
                const statusInfo = INVOICE_STATUS_CONFIG[invoice.status] || INVOICE_STATUS_CONFIG.draft;
                
                return (
                  <Card key={invoice.id} className={`hover:shadow-md transition-shadow ${invoice.is_overdue ? 'border-red-300' : ''}`}>
                    <CardContent className="pt-6">
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap mb-2">
                            <h3 className="font-semibold text-lg text-slate-900">
                              {invoice.invoice_number}
                            </h3>
                            <Badge className={statusInfo.color}>
                              {statusInfo.label}
                            </Badge>
                            {invoice.is_overdue && (
                              <Badge className="bg-red-500 text-white">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                En retard
                              </Badge>
                            )}
                          </div>
                          
                          {invoice.title && (
                            <p className="text-slate-600 mb-2">{invoice.title}</p>
                          )}
                          
                          <div className="flex items-center gap-4 text-sm text-slate-500 flex-wrap">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(invoice.invoice_date)}
                            </span>
                            {invoice.due_date && (
                              <span className={`flex items-center gap-1 ${invoice.is_overdue ? 'text-red-600 font-medium' : ''}`}>
                                <Clock className="w-3 h-3" />
                                Échéance: {formatDate(invoice.due_date)}
                              </span>
                            )}
                          </div>
                          
                          {invoice.payments?.length > 0 && (
                            <div className="mt-3 space-y-1">
                              <p className="text-sm font-medium text-slate-700">Paiements reçus:</p>
                              {invoice.payments.map((payment, idx) => (
                                <p key={idx} className="text-sm text-green-600">
                                  <CheckCircle className="w-3 h-3 inline mr-1" />
                                  {formatCurrency(payment.amount)} - {formatDate(payment.date)}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        <div className="text-right">
                          <p className="text-2xl font-bold text-orange-600">
                            {formatCurrency(invoice.total_ttc)}
                          </p>
                          <p className="text-sm text-slate-500">TTC</p>
                          
                          {invoice.amount_paid > 0 && invoice.amount_paid < invoice.total_ttc && (
                            <div className="mt-2">
                              <p className="text-sm text-green-600">
                                Payé: {formatCurrency(invoice.amount_paid)}
                              </p>
                              <p className="text-sm font-medium text-red-600">
                                Reste: {formatCurrency(invoice.total_ttc - invoice.amount_paid)}
                              </p>
                            </div>
                          )}
                          
                          {invoice.pdf_url && (
                            <Button variant="outline" className="mt-4" asChild>
                              <a href={invoice.pdf_url} target="_blank" rel="noopener noreferrer">
                                <Download className="w-4 h-4 mr-2" />
                                PDF
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Signature Modal */}
      <Dialog open={showSignModal} onOpenChange={setShowSignModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
              <PenTool className="w-5 h-5 text-orange-600" />
              Signature électronique
            </DialogTitle>
            <DialogDescription>
              {selectedQuote && (
                <>Signez le devis <strong>{selectedQuote.quote_number}</strong> - {formatCurrency(selectedQuote.total_ttc)}</>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Signer Info */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="signer_name">Nom complet *</Label>
                <Input
                  id="signer_name"
                  value={signatureForm.signer_name}
                  onChange={(e) => setSignatureForm({...signatureForm, signer_name: e.target.value})}
                  placeholder="Votre nom"
                  data-testid="signer-name"
                />
              </div>
              
              <div>
                <Label htmlFor="signer_email">Email *</Label>
                <Input
                  id="signer_email"
                  type="email"
                  value={signatureForm.signer_email}
                  onChange={(e) => setSignatureForm({...signatureForm, signer_email: e.target.value})}
                  placeholder="votre@email.fr"
                  data-testid="signer-email"
                />
              </div>
              
              <div>
                <Label htmlFor="signer_title">Fonction (optionnel)</Label>
                <Input
                  id="signer_title"
                  value={signatureForm.signer_title}
                  onChange={(e) => setSignatureForm({...signatureForm, signer_title: e.target.value})}
                  placeholder="Ex: Gérant, Directeur..."
                />
              </div>
            </div>
            
            {/* Signature Canvas */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Votre signature *</Label>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={clearSignature}
                  className="text-slate-500"
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Effacer
                </Button>
              </div>
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-1 bg-white">
                <canvas
                  ref={canvasRef}
                  width={400}
                  height={150}
                  className="w-full touch-none cursor-crosshair"
                  onMouseDown={startDrawing}
                  onMouseMove={draw}
                  onMouseUp={stopDrawing}
                  onMouseLeave={stopDrawing}
                  onTouchStart={startDrawing}
                  onTouchMove={draw}
                  onTouchEnd={stopDrawing}
                  data-testid="signature-canvas"
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Dessinez votre signature avec la souris ou le doigt
              </p>
            </div>
            
            {/* Legal Notice */}
            <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600">
              <p className="font-medium mb-1">En signant ce document, vous acceptez :</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li>Les conditions du devis ci-dessus</li>
                <li>Que cette signature électronique a la même valeur qu'une signature manuscrite</li>
                <li>Que votre adresse IP et la date seront enregistrées</li>
              </ul>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSignModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSign}
              disabled={signing || !hasSignature}
              className="bg-orange-600 hover:bg-orange-700"
              data-testid="confirm-signature-btn"
            >
              {signing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Signer le devis
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
