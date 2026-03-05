import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, Calculator, FileText, MapPin, Hammer, Euro, Clock, TrendingUp, Upload, FileUp, Download, ExternalLink, Image, PenTool } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

const AIAssistantPage = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('generate');
    const fileInputRef = useRef(null);
    const imageInputRef = useRef(null);
    
    // Generate Quote State
    const [quoteForm, setQuoteForm] = useState({
        project_type: '',
        surface: '',
        location: '',
        materials_quality: 'standard',
        description: ''
    });
    const [generatedQuote, setGeneratedQuote] = useState(null);
    
    // Estimate State
    const [estimateForm, setEstimateForm] = useState({
        project_type: '',
        surface: '',
        location: '',
        complexity: 'standard'
    });
    const [estimation, setEstimation] = useState(null);
    
    // Analyze State
    const [analyzeForm, setAnalyzeForm] = useState({ description: '' });
    const [analysis, setAnalysis] = useState(null);
    
    // PDF Analysis State
    const [pdfAnalysis, setPdfAnalysis] = useState(null);
    const [pdfLoading, setPdfLoading] = useState(false);
    
    // Image Analysis State
    const [imageAnalysis, setImageAnalysis] = useState(null);
    const [imageLoading, setImageLoading] = useState(false);

    const projectTypes = [
        { value: 'renovation_salle_de_bain', label: 'Rénovation salle de bain' },
        { value: 'renovation_cuisine', label: 'Rénovation cuisine' },
        { value: 'renovation_appartement', label: 'Rénovation appartement' },
        { value: 'peinture_interieure', label: 'Peinture intérieure' },
        { value: 'renovation_electrique', label: 'Rénovation électrique' },
    ];

    const locations = [
        { value: 'paris', label: 'Paris (+35%)' },
        { value: 'ile_de_france', label: 'Île-de-France (+25%)' },
        { value: 'lyon', label: 'Lyon (+15%)' },
        { value: 'marseille', label: 'Marseille (+10%)' },
        { value: 'bordeaux', label: 'Bordeaux (+10%)' },
        { value: 'nice', label: 'Nice (+20%)' },
        { value: 'default', label: 'Autre ville (prix standard)' },
        { value: 'rural', label: 'Zone rurale (-10%)' },
    ];

    const handleGenerateQuote = async (e) => {
        e.preventDefault();
        if (!quoteForm.project_type || !quoteForm.surface) {
            toast.error('Veuillez remplir le type de projet et la surface');
            return;
        }
        
        setLoading(true);
        try {
            const response = await api.post('/ai/generate-quote', {
                ...quoteForm,
                surface: parseFloat(quoteForm.surface)
            });
            setGeneratedQuote(response.data);
            toast.success('Devis généré avec succès !');
        } catch (error) {
            toast.error('Erreur lors de la génération du devis');
        } finally {
            setLoading(false);
        }
    };

    const handleExportQuote = async () => {
        if (!generatedQuote) return;
        
        setLoading(true);
        try {
            const response = await api.post('/ai/export-to-quote', generatedQuote);
            toast.success(response.data.message);
            navigate(`/devis/${response.data.quote_id}`);
        } catch (error) {
            toast.error('Erreur lors de l\'export du devis');
        } finally {
            setLoading(false);
        }
    };

    const handleEstimateProject = async (e) => {
        e.preventDefault();
        if (!estimateForm.project_type || !estimateForm.surface) {
            toast.error('Veuillez remplir le type de projet et la surface');
            return;
        }
        
        setLoading(true);
        try {
            const response = await api.post('/ai/estimate-project', {
                ...estimateForm,
                surface: parseFloat(estimateForm.surface)
            });
            setEstimation(response.data);
            toast.success('Estimation générée !');
        } catch (error) {
            toast.error('Erreur lors de l\'estimation');
        } finally {
            setLoading(false);
        }
    };

    const handleAnalyzeDescription = async (e) => {
        e.preventDefault();
        if (!analyzeForm.description || analyzeForm.description.length < 10) {
            toast.error('Veuillez entrer une description plus détaillée');
            return;
        }
        
        setLoading(true);
        try {
            const response = await api.post('/ai/analyze-description', analyzeForm);
            setAnalysis(response.data);
            toast.success('Analyse terminée !');
        } catch (error) {
            toast.error('Erreur lors de l\'analyse');
        } finally {
            setLoading(false);
        }
    };

    const handlePdfUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        
        if (file.type !== 'application/pdf') {
            toast.error('Veuillez sélectionner un fichier PDF');
            return;
        }
        
        setPdfLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await api.post('/ai/analyze-plan-pdf', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setPdfAnalysis(response.data);
            toast.success('Plan PDF analysé !');
        } catch (error) {
            toast.error('Erreur lors de l\'analyse du PDF');
        } finally {
            setPdfLoading(false);
        }
    };

    const handleImageUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        
        if (!file.type.startsWith('image/')) {
            toast.error('Veuillez sélectionner une image');
            return;
        }
        
        setImageLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await api.post('/ai/analyze-site-photo', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setImageAnalysis(response.data);
            toast.success('Photo analysée !');
        } catch (error) {
            toast.error('Erreur lors de l\'analyse de l\'image');
        } finally {
            setImageLoading(false);
        }
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(price);
    };

    return (
        <div className="container mx-auto py-6 px-4 max-w-6xl" data-testid="ai-assistant-page">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Sparkles className="h-8 w-8 text-blue-500" />
                    Assistant IA Devis
                </h1>
                <p className="text-gray-600 mt-2">
                    Générez des devis professionnels automatiquement grâce à notre intelligence artificielle
                </p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="generate" className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <span className="hidden sm:inline">Générer</span>
                    </TabsTrigger>
                    <TabsTrigger value="estimate" className="flex items-center gap-2">
                        <Calculator className="h-4 w-4" />
                        <span className="hidden sm:inline">Estimer</span>
                    </TabsTrigger>
                    <TabsTrigger value="analyze" className="flex items-center gap-2">
                        <Hammer className="h-4 w-4" />
                        <span className="hidden sm:inline">Analyser</span>
                    </TabsTrigger>
                    <TabsTrigger value="pdf" className="flex items-center gap-2">
                        <FileUp className="h-4 w-4" />
                        <span className="hidden sm:inline">Plan PDF</span>
                    </TabsTrigger>
                    <TabsTrigger value="photo" className="flex items-center gap-2">
                        <Image className="h-4 w-4" />
                        <span className="hidden sm:inline">Photo</span>
                    </TabsTrigger>
                </TabsList>

                {/* Generate Quote Tab */}
                <TabsContent value="generate">
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Paramètres du projet</CardTitle>
                                <CardDescription>
                                    Décrivez votre projet pour générer un devis détaillé
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleGenerateQuote} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Type de projet *</Label>
                                        <Select 
                                            value={quoteForm.project_type}
                                            onValueChange={(value) => setQuoteForm(prev => ({...prev, project_type: value}))}
                                        >
                                            <SelectTrigger data-testid="project-type-select">
                                                <SelectValue placeholder="Sélectionner un type" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {projectTypes.map(type => (
                                                    <SelectItem key={type.value} value={type.value}>
                                                        {type.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Surface (m²) *</Label>
                                        <Input
                                            type="number"
                                            placeholder="Ex: 25"
                                            value={quoteForm.surface}
                                            onChange={(e) => setQuoteForm(prev => ({...prev, surface: e.target.value}))}
                                            data-testid="surface-input"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Localisation</Label>
                                        <Select 
                                            value={quoteForm.location}
                                            onValueChange={(value) => setQuoteForm(prev => ({...prev, location: value}))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Sélectionner une région" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {locations.map(loc => (
                                                    <SelectItem key={loc.value} value={loc.value}>
                                                        {loc.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Qualité des matériaux</Label>
                                        <Select 
                                            value={quoteForm.materials_quality}
                                            onValueChange={(value) => setQuoteForm(prev => ({...prev, materials_quality: value}))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="economique">Économique (-20%)</SelectItem>
                                                <SelectItem value="standard">Standard</SelectItem>
                                                <SelectItem value="premium">Premium (+30%)</SelectItem>
                                                <SelectItem value="luxe">Luxe (+60%)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Button 
                                        type="submit" 
                                        className="w-full"
                                        disabled={loading}
                                        data-testid="generate-quote-btn"
                                    >
                                        {loading ? (
                                            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Génération...</>
                                        ) : (
                                            <><Sparkles className="mr-2 h-4 w-4" /> Générer le devis</>
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {generatedQuote && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center justify-between">
                                        Devis généré
                                        <Badge variant="secondary">
                                            <MapPin className="h-3 w-3 mr-1" />
                                            x{generatedQuote.regional_multiplier}
                                        </Badge>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        <div className="border rounded-lg overflow-hidden">
                                            <table className="w-full text-sm">
                                                <thead className="bg-gray-50">
                                                    <tr>
                                                        <th className="px-3 py-2 text-left">Description</th>
                                                        <th className="px-3 py-2 text-right">Qté</th>
                                                        <th className="px-3 py-2 text-right">P.U.</th>
                                                        <th className="px-3 py-2 text-right">Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {generatedQuote.items.map((item, idx) => (
                                                        <tr key={idx} className="border-t">
                                                            <td className="px-3 py-2">{item.description}</td>
                                                            <td className="px-3 py-2 text-right">{item.quantity} {item.unit}</td>
                                                            <td className="px-3 py-2 text-right">{formatPrice(item.unit_price)}</td>
                                                            <td className="px-3 py-2 text-right font-medium">{formatPrice(item.total_ht)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>

                                        <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                                            <div className="flex justify-between">
                                                <span>Total HT</span>
                                                <span className="font-medium">{formatPrice(generatedQuote.total_ht)}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>TVA (10%)</span>
                                                <span>{formatPrice(generatedQuote.total_vat)}</span>
                                            </div>
                                            <div className="flex justify-between text-lg font-bold border-t pt-2">
                                                <span>Total TTC</span>
                                                <span className="text-blue-600">{formatPrice(generatedQuote.total_ttc)}</span>
                                            </div>
                                        </div>

                                        <Button 
                                            onClick={handleExportQuote} 
                                            className="w-full"
                                            disabled={loading}
                                            data-testid="export-quote-btn"
                                        >
                                            {loading ? (
                                                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Export...</>
                                            ) : (
                                                <><Download className="mr-2 h-4 w-4" /> Créer le devis dans le système</>
                                            )}
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                {/* Estimate Tab */}
                <TabsContent value="estimate">
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Estimation de budget</CardTitle>
                                <CardDescription>
                                    Obtenez une estimation rapide du coût de votre projet
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleEstimateProject} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Type de projet *</Label>
                                        <Select 
                                            value={estimateForm.project_type}
                                            onValueChange={(value) => setEstimateForm(prev => ({...prev, project_type: value}))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Sélectionner un type" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {projectTypes.map(type => (
                                                    <SelectItem key={type.value} value={type.value}>
                                                        {type.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Surface (m²) *</Label>
                                        <Input
                                            type="number"
                                            placeholder="Ex: 65"
                                            value={estimateForm.surface}
                                            onChange={(e) => setEstimateForm(prev => ({...prev, surface: e.target.value}))}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Localisation</Label>
                                        <Select 
                                            value={estimateForm.location}
                                            onValueChange={(value) => setEstimateForm(prev => ({...prev, location: value}))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue placeholder="Sélectionner une région" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {locations.map(loc => (
                                                    <SelectItem key={loc.value} value={loc.value}>
                                                        {loc.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Complexité</Label>
                                        <Select 
                                            value={estimateForm.complexity}
                                            onValueChange={(value) => setEstimateForm(prev => ({...prev, complexity: value}))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="simple">Simple (-20%)</SelectItem>
                                                <SelectItem value="standard">Standard</SelectItem>
                                                <SelectItem value="complexe">Complexe (+30%)</SelectItem>
                                                <SelectItem value="tres_complexe">Très complexe (+60%)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Button type="submit" className="w-full" disabled={loading}>
                                        {loading ? (
                                            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Calcul...</>
                                        ) : (
                                            <><Calculator className="mr-2 h-4 w-4" /> Estimer le budget</>
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {estimation && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Estimation du projet</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-orange-50 rounded-lg p-4 text-center">
                                            <Euro className="h-6 w-6 mx-auto text-orange-500 mb-2" />
                                            <div className="text-2xl font-bold text-orange-600">
                                                {formatPrice(estimation.labor_cost)}
                                            </div>
                                            <div className="text-sm text-gray-600">Main d'œuvre</div>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-4 text-center">
                                            <Hammer className="h-6 w-6 mx-auto text-green-500 mb-2" />
                                            <div className="text-2xl font-bold text-green-600">
                                                {formatPrice(estimation.materials_cost)}
                                            </div>
                                            <div className="text-sm text-gray-600">Matériaux</div>
                                        </div>
                                    </div>

                                    <div className="bg-blue-50 rounded-lg p-4 text-center">
                                        <TrendingUp className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                                        <div className="text-3xl font-bold text-blue-600">
                                            {formatPrice(estimation.total_ttc)}
                                        </div>
                                        <div className="text-sm text-gray-600">Total TTC estimé</div>
                                        <div className="text-xs text-gray-500 mt-1">
                                            Fourchette: {formatPrice(estimation.price_range.min)} - {formatPrice(estimation.price_range.max)}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-center gap-2 text-gray-600">
                                        <Clock className="h-4 w-4" />
                                        <span>Durée estimée: <strong>{estimation.estimated_duration_days} jours</strong></span>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                {/* Analyze Tab */}
                <TabsContent value="analyze">
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Analyse de chantier</CardTitle>
                                <CardDescription>
                                    Décrivez votre chantier et l'IA détectera les travaux nécessaires
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleAnalyzeDescription} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Description du chantier *</Label>
                                        <Textarea
                                            placeholder="Ex: Je veux refaire ma salle de bain avec une douche italienne, du carrelage mural et de la peinture. Il faut aussi changer les prises électriques..."
                                            value={analyzeForm.description}
                                            onChange={(e) => setAnalyzeForm({ description: e.target.value })}
                                            rows={6}
                                            data-testid="description-textarea"
                                        />
                                    </div>

                                    <Button type="submit" className="w-full" disabled={loading}>
                                        {loading ? (
                                            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyse...</>
                                        ) : (
                                            <><Sparkles className="mr-2 h-4 w-4" /> Analyser</>
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {analysis && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Résultat de l'analyse</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <h4 className="font-medium mb-2">Types de travaux détectés</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {analysis.detected_work_types.map((type, idx) => (
                                                <Badge key={idx} variant="secondary" className="capitalize">
                                                    {type.replace('_', ' ')}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="font-medium mb-2">Prestations suggérées</h4>
                                        <div className="space-y-2 max-h-80 overflow-y-auto">
                                            {analysis.suggestions.map((suggestion, idx) => (
                                                <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                                    <div>
                                                        <div className="font-medium text-sm">{suggestion.description}</div>
                                                        <div className="text-xs text-gray-500">{suggestion.category}</div>
                                                    </div>
                                                    <Badge variant="outline">
                                                        {suggestion.base_price}€/{suggestion.unit}
                                                    </Badge>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                {/* PDF Analysis Tab */}
                <TabsContent value="pdf">
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <FileUp className="h-5 w-5" />
                                    Analyse de plan PDF
                                </CardTitle>
                                <CardDescription>
                                    Uploadez un plan de construction pour une analyse automatique des pièces et surfaces
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <input
                                    type="file"
                                    accept="application/pdf"
                                    ref={fileInputRef}
                                    onChange={handlePdfUpload}
                                    className="hidden"
                                />
                                
                                <div 
                                    className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-gray-50 transition-colors"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    {pdfLoading ? (
                                        <div className="flex flex-col items-center">
                                            <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
                                            <p className="text-gray-600">Analyse en cours...</p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center">
                                            <Upload className="h-12 w-12 text-gray-400 mb-4" />
                                            <p className="text-gray-600 font-medium">Cliquez pour uploader un plan PDF</p>
                                            <p className="text-sm text-gray-400 mt-2">Maximum 20 MB</p>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {pdfAnalysis && pdfAnalysis.success && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Résultat de l'analyse PDF</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-center">
                                        <div className="bg-blue-50 rounded-lg p-3">
                                            <div className="text-2xl font-bold text-blue-600">{pdfAnalysis.pages}</div>
                                            <div className="text-sm text-gray-600">Pages</div>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-3">
                                            <div className="text-2xl font-bold text-green-600">{pdfAnalysis.total_surface_estimated || 0}m²</div>
                                            <div className="text-sm text-gray-600">Surface estimée</div>
                                        </div>
                                    </div>

                                    {pdfAnalysis.rooms_detected?.length > 0 && (
                                        <div>
                                            <h4 className="font-medium mb-2">Pièces détectées</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {pdfAnalysis.rooms_detected.map((room, idx) => (
                                                    <Badge key={idx} variant="secondary">
                                                        {room.name} {room.surface ? `(${room.surface}m²)` : ''}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {pdfAnalysis.suggested_works?.length > 0 && (
                                        <div>
                                            <h4 className="font-medium mb-2">Travaux suggérés</h4>
                                            <div className="space-y-2 max-h-60 overflow-y-auto">
                                                {pdfAnalysis.suggested_works.map((work, idx) => (
                                                    <div key={idx} className="p-2 bg-gray-50 rounded text-sm">
                                                        <div className="font-medium">{work.description}</div>
                                                        <div className="text-xs text-gray-500">{work.room} - {work.price_range}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>

                {/* Photo Analysis Tab */}
                <TabsContent value="photo">
                    <div className="grid md:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Image className="h-5 w-5" />
                                    Analyse photo de chantier
                                </CardTitle>
                                <CardDescription>
                                    Uploadez une photo de votre chantier pour une analyse visuelle
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <input
                                    type="file"
                                    accept="image/*"
                                    ref={imageInputRef}
                                    onChange={handleImageUpload}
                                    className="hidden"
                                />
                                
                                <div 
                                    className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-gray-50 transition-colors"
                                    onClick={() => imageInputRef.current?.click()}
                                >
                                    {imageLoading ? (
                                        <div className="flex flex-col items-center">
                                            <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
                                            <p className="text-gray-600">Analyse en cours...</p>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center">
                                            <Upload className="h-12 w-12 text-gray-400 mb-4" />
                                            <p className="text-gray-600 font-medium">Cliquez pour uploader une photo</p>
                                            <p className="text-sm text-gray-400 mt-2">JPG, PNG - Maximum 10 MB</p>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {imageAnalysis && imageAnalysis.success && (
                            <Card>
                                <CardHeader>
                                    <CardTitle>Résultat de l'analyse photo</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-center">
                                        <div className="bg-blue-50 rounded-lg p-3">
                                            <div className="text-lg font-bold text-blue-600">{imageAnalysis.dimensions?.width}x{imageAnalysis.dimensions?.height}</div>
                                            <div className="text-sm text-gray-600">Dimensions</div>
                                        </div>
                                        <div className="bg-green-50 rounded-lg p-3">
                                            <div className="text-lg font-bold text-green-600">{imageAnalysis.format}</div>
                                            <div className="text-sm text-gray-600">Format</div>
                                        </div>
                                    </div>

                                    <div className="bg-yellow-50 rounded-lg p-4">
                                        <h4 className="font-medium mb-2">Suggestions</h4>
                                        <ul className="text-sm text-gray-600 space-y-1">
                                            {imageAnalysis.suggestions?.map((suggestion, idx) => (
                                                <li key={idx}>• {suggestion}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default AIAssistantPage;
