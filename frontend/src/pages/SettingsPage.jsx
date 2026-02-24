import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { getSettings, updateSettings, uploadLogo, getPredefinedCategories, createPredefinedItem, updatePredefinedItem, deletePredefinedItem, resetPredefinedItems, getKits, createKit, updateKit, deleteKit, resetKits } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Building2, Save, Upload, Plus, Trash2, Package, RefreshCw, Pencil, Layers, ChevronDown, ChevronUp, CreditCard, FileText, AlertTriangle, Globe, ExternalLink, Palette, Check } from "lucide-react";
import { toast } from "sonner";
import WebsiteRequestDialog from "@/components/WebsiteRequestDialog";

const UNIT_OPTIONS = ["unité", "m²", "ml", "m³", "heure", "jour", "forfait", "kg", "litre"];

const DEFAULT_CATEGORIES = [
    "Menuiserie",
    "Plomberie", 
    "Électricité",
    "Peinture",
    "Maçonnerie",
    "Carrelage",
    "Plâtrerie / Isolation",
    "Rénovation générale"
];

export default function SettingsPage() {
    const { isAdmin } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploadingLogo, setUploadingLogo] = useState(false);
    const [showWebsiteDialog, setShowWebsiteDialog] = useState(false);
    const fileInputRef = useRef(null);
    
    // Company settings
    const [formData, setFormData] = useState({
        company_name: "",
        address: "",
        phone: "",
        email: "",
        siret: "",
        vat_number: "",
        default_vat_rates: [20.0, 10.0, 5.5, 2.1],
        logo_base64: null,
        // New French legal fields
        rcs_rm: "",
        code_ape: "",
        capital_social: "",
        iban: "",
        bic: "",
        is_auto_entrepreneur: false,
        auto_entrepreneur_mention: "TVA non applicable, art. 293B du CGI",
        default_payment_delay_days: 30,
        late_payment_rate: 3.0,
        // Retenue de garantie settings
        default_retenue_garantie_enabled: false,
        default_retenue_garantie_rate: 5.0,
        default_retenue_garantie_duration_months: 12,
        // Website
        website: "",
        // Document appearance
        document_theme_color: "blue"
    });

    // Theme color options
    const THEME_COLOR_OPTIONS = [
        { value: "blue", label: "Bleu", color: "#2563EB", preview: "bg-blue-600" },
        { value: "light_blue", label: "Bleu clair", color: "#0EA5E9", preview: "bg-sky-500" },
        { value: "green", label: "Vert", color: "#16A34A", preview: "bg-green-600" },
        { value: "orange", label: "Orange", color: "#EA580C", preview: "bg-orange-600" },
        { value: "burgundy", label: "Bordeaux", color: "#9F1239", preview: "bg-rose-800" },
        { value: "dark_grey", label: "Gris foncé", color: "#475569", preview: "bg-slate-600" }
    ];

    // Predefined items
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState("");
    const [editingItem, setEditingItem] = useState(null);
    const [showDeleteDialog, setShowDeleteDialog] = useState(null);
    const [showResetDialog, setShowResetDialog] = useState(false);
    
    // New item form
    const [newItem, setNewItem] = useState({
        category: "",
        description: "",
        unit: "unité",
        default_price: 0,
        default_vat_rate: 20
    });

    // Kits state
    const [kits, setKits] = useState([]);
    const [editingKit, setEditingKit] = useState(null);
    const [showDeleteKitDialog, setShowDeleteKitDialog] = useState(null);
    const [showResetKitsDialog, setShowResetKitsDialog] = useState(false);
    const [expandedKit, setExpandedKit] = useState(null);
    const [showNewKitModal, setShowNewKitModal] = useState(false);
    const [newKit, setNewKit] = useState({
        name: "",
        description: "",
        items: [{ description: "", unit: "unité", quantity: 1, unit_price: 0, vat_rate: 20 }]
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [settingsRes, categoriesRes, kitsRes] = await Promise.all([
                getSettings(),
                getPredefinedCategories(),
                getKits()
            ]);
            
            if (settingsRes.data) {
                setFormData({
                    company_name: settingsRes.data.company_name || "",
                    address: settingsRes.data.address || "",
                    phone: settingsRes.data.phone || "",
                    email: settingsRes.data.email || "",
                    siret: settingsRes.data.siret || "",
                    vat_number: settingsRes.data.vat_number || "",
                    default_vat_rates: settingsRes.data.default_vat_rates?.length > 0 
                        ? settingsRes.data.default_vat_rates 
                        : [20.0, 10.0, 5.5, 2.1],
                    logo_base64: settingsRes.data.logo_base64 || null,
                    // New French legal fields
                    rcs_rm: settingsRes.data.rcs_rm || "",
                    code_ape: settingsRes.data.code_ape || "",
                    capital_social: settingsRes.data.capital_social || "",
                    iban: settingsRes.data.iban || "",
                    bic: settingsRes.data.bic || "",
                    is_auto_entrepreneur: settingsRes.data.is_auto_entrepreneur || false,
                    auto_entrepreneur_mention: settingsRes.data.auto_entrepreneur_mention || "TVA non applicable, art. 293B du CGI",
                    default_payment_delay_days: settingsRes.data.default_payment_delay_days || 30,
                    late_payment_rate: settingsRes.data.late_payment_rate || 3.0,
                    // Retenue de garantie settings
                    default_retenue_garantie_enabled: settingsRes.data.default_retenue_garantie_enabled || false,
                    default_retenue_garantie_rate: settingsRes.data.default_retenue_garantie_rate || 5.0,
                    default_retenue_garantie_duration_months: settingsRes.data.default_retenue_garantie_duration_months || 12
                });
            }
            
            setCategories(categoriesRes.data);
            if (categoriesRes.data.length > 0) {
                setSelectedCategory(categoriesRes.data[0].name);
            }
            
            setKits(kitsRes.data);
        } catch (error) {
            toast.error("Erreur lors du chargement des paramètres");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await updateSettings(formData);
            toast.success("Paramètres enregistrés avec succès");
        } catch (error) {
            toast.error("Erreur lors de l'enregistrement des paramètres");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (field) => (e) => {
        setFormData(prev => ({ ...prev, [field]: e.target.value }));
    };

    const handleLogoUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            toast.error("Veuillez sélectionner une image");
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            toast.error("L'image ne doit pas dépasser 5MB");
            return;
        }

        setUploadingLogo(true);
        try {
            const response = await uploadLogo(file);
            setFormData(prev => ({ ...prev, logo_base64: response.data.logo }));
            toast.success("Logo téléchargé avec succès");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du logo");
        } finally {
            setUploadingLogo(false);
        }
    };

    const handleRemoveLogo = () => {
        setFormData(prev => ({ ...prev, logo_base64: null }));
    };

    const addVatRate = () => {
        setFormData(prev => ({
            ...prev,
            default_vat_rates: [...prev.default_vat_rates, 0]
        }));
    };

    const removeVatRate = (index) => {
        if (formData.default_vat_rates.length === 1) return;
        setFormData(prev => ({
            ...prev,
            default_vat_rates: prev.default_vat_rates.filter((_, i) => i !== index)
        }));
    };

    const updateVatRate = (index, value) => {
        setFormData(prev => ({
            ...prev,
            default_vat_rates: prev.default_vat_rates.map((rate, i) => 
                i === index ? parseFloat(value) || 0 : rate
            )
        }));
    };

    // Predefined items handlers
    const handleCreateItem = async () => {
        if (!newItem.category || !newItem.description) {
            toast.error("Catégorie et description requises");
            return;
        }
        try {
            await createPredefinedItem(newItem);
            toast.success("Article créé");
            setNewItem({ category: "", description: "", unit: "unité", default_price: 0, default_vat_rate: 20 });
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la création");
        }
    };

    const handleUpdateItem = async () => {
        if (!editingItem) return;
        try {
            await updatePredefinedItem(editingItem.id, editingItem);
            toast.success("Article mis à jour");
            setEditingItem(null);
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la mise à jour");
        }
    };

    const handleDeleteItem = async () => {
        if (!showDeleteDialog) return;
        try {
            await deletePredefinedItem(showDeleteDialog);
            toast.success("Article supprimé");
            setShowDeleteDialog(null);
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la suppression");
        }
    };

    const handleResetItems = async () => {
        try {
            await resetPredefinedItems();
            toast.success("Articles réinitialisés");
            setShowResetDialog(false);
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la réinitialisation");
        }
    };

    // Kits handlers
    const handleCreateKit = async () => {
        if (!newKit.name.trim()) {
            toast.error("Le nom du kit est requis");
            return;
        }
        const validItems = newKit.items.filter(i => i.description.trim());
        if (validItems.length === 0) {
            toast.error("Ajoutez au moins une ligne au kit");
            return;
        }
        try {
            await createKit({ ...newKit, items: validItems });
            toast.success("Kit créé avec succès");
            setShowNewKitModal(false);
            setNewKit({ name: "", description: "", items: [{ description: "", unit: "unité", quantity: 1, unit_price: 0, vat_rate: 20 }] });
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la création du kit");
        }
    };

    const handleDeleteKit = async () => {
        if (!showDeleteKitDialog) return;
        try {
            await deleteKit(showDeleteKitDialog);
            toast.success("Kit supprimé");
            setShowDeleteKitDialog(null);
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la suppression");
        }
    };

    const handleResetKits = async () => {
        try {
            await resetKits();
            toast.success("Kits réinitialisés");
            setShowResetKitsDialog(false);
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la réinitialisation");
        }
    };

    const addKitItem = () => {
        setNewKit(prev => ({
            ...prev,
            items: [...prev.items, { description: "", unit: "unité", quantity: 1, unit_price: 0, vat_rate: 20 }]
        }));
    };

    const removeKitItem = (index) => {
        if (newKit.items.length === 1) return;
        setNewKit(prev => ({
            ...prev,
            items: prev.items.filter((_, i) => i !== index)
        }));
    };

    const updateKitItem = (index, field, value) => {
        setNewKit(prev => ({
            ...prev,
            items: prev.items.map((item, i) => i === index ? { ...item, [field]: value } : item)
        }));
    };

    const calculateKitTotal = (items) => {
        return items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0).toFixed(2);
    };

    const currentCategoryItems = categories.find(c => c.name === selectedCategory)?.items || [];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="settings-page">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                    Paramètres
                </h1>
                <p className="text-slate-500 mt-1">Configurez votre entreprise et vos articles prédéfinis</p>
            </div>

            <Tabs defaultValue="company" className="space-y-6">
                <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="company" className="flex items-center gap-2">
                        <Building2 className="w-4 h-4" />
                        Entreprise
                    </TabsTrigger>
                    <TabsTrigger value="items" className="flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        Articles
                    </TabsTrigger>
                    <TabsTrigger value="kits" className="flex items-center gap-2">
                        <Layers className="w-4 h-4" />
                        Kits
                    </TabsTrigger>
                </TabsList>

                {/* Company Settings Tab */}
                <TabsContent value="company">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Logo */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed']">Logo de l'entreprise</CardTitle>
                                <CardDescription>Ce logo apparaîtra sur vos devis et factures PDF</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center gap-6">
                                    <div className="w-32 h-32 bg-slate-100 rounded-lg flex items-center justify-center overflow-hidden border-2 border-dashed border-slate-300">
                                        {formData.logo_base64 ? (
                                            <img src={formData.logo_base64} alt="Logo" className="w-full h-full object-contain" />
                                        ) : (
                                            <Building2 className="w-12 h-12 text-slate-400" />
                                        )}
                                    </div>
                                    <div className="space-y-3">
                                        <input ref={fileInputRef} type="file" accept="image/*" onChange={handleLogoUpload} className="hidden" />
                                        <Button type="button" variant="outline" onClick={() => fileInputRef.current?.click()} disabled={uploadingLogo} data-testid="upload-logo-btn">
                                            {uploadingLogo ? "Téléchargement..." : <><Upload className="w-4 h-4 mr-2" />{formData.logo_base64 ? "Changer" : "Télécharger"}</>}
                                        </Button>
                                        {formData.logo_base64 && (
                                            <Button type="button" variant="ghost" className="text-red-600" onClick={handleRemoveLogo}>
                                                <Trash2 className="w-4 h-4 mr-2" />Supprimer
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Company Info */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed']">Informations de l'entreprise</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="company_name">Nom de l'entreprise</Label>
                                    <Input id="company_name" placeholder="Votre Entreprise BTP" value={formData.company_name} onChange={handleChange("company_name")} data-testid="company-name-input" />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="address">Adresse</Label>
                                    <Input id="address" placeholder="123 Rue du Bâtiment, 75001 Paris" value={formData.address} onChange={handleChange("address")} data-testid="address-input" />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="phone">Téléphone</Label>
                                        <Input id="phone" placeholder="01 23 45 67 89" value={formData.phone} onChange={handleChange("phone")} data-testid="phone-input" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Email</Label>
                                        <Input id="email" type="email" placeholder="contact@entreprise.fr" value={formData.email} onChange={handleChange("email")} data-testid="email-input" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Legal Info */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed']">Informations légales</CardTitle>
                                <CardDescription>Ces informations sont obligatoires sur vos factures</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="siret">Numéro SIRET</Label>
                                        <Input id="siret" placeholder="123 456 789 00012" value={formData.siret} onChange={handleChange("siret")} className="font-mono" data-testid="siret-input" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="vat_number">Numéro de TVA intracommunautaire</Label>
                                        <Input id="vat_number" placeholder="FR12 345678901" value={formData.vat_number} onChange={handleChange("vat_number")} className="font-mono" data-testid="vat-number-input" disabled={formData.is_auto_entrepreneur} />
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="rcs_rm">RCS ou RM</Label>
                                        <Input id="rcs_rm" placeholder="RCS Paris B 123456789" value={formData.rcs_rm} onChange={handleChange("rcs_rm")} data-testid="rcs-input" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="code_ape">Code APE/NAF</Label>
                                        <Input id="code_ape" placeholder="4332A" value={formData.code_ape} onChange={handleChange("code_ape")} className="font-mono" data-testid="code-ape-input" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="capital_social">Capital social</Label>
                                        <Input id="capital_social" placeholder="10 000 €" value={formData.capital_social} onChange={handleChange("capital_social")} data-testid="capital-input" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Auto-entrepreneur Mode */}
                        <Card className={formData.is_auto_entrepreneur ? "border-amber-300 bg-amber-50/50" : ""}>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                            <FileText className="w-5 h-5" />
                                            Mode Auto-entrepreneur
                                        </CardTitle>
                                        <CardDescription>Activez si vous êtes auto-entrepreneur (TVA non applicable)</CardDescription>
                                    </div>
                                    <Switch 
                                        checked={formData.is_auto_entrepreneur} 
                                        onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_auto_entrepreneur: checked }))}
                                        data-testid="auto-entrepreneur-toggle"
                                    />
                                </div>
                            </CardHeader>
                            {formData.is_auto_entrepreneur && (
                                <CardContent>
                                    <div className="bg-amber-100 border border-amber-300 rounded-lg p-4">
                                        <div className="flex items-start gap-3">
                                            <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                                            <div>
                                                <p className="font-medium text-amber-800">TVA non applicable</p>
                                                <p className="text-sm text-amber-700 mt-1">La mention suivante sera ajoutée automatiquement sur tous vos documents :</p>
                                                <p className="text-sm font-mono bg-white px-2 py-1 rounded mt-2 text-amber-900">
                                                    {formData.auto_entrepreneur_mention}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            )}
                        </Card>

                        {/* Bank Details */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                    <CreditCard className="w-5 h-5" />
                                    Coordonnées bancaires
                                </CardTitle>
                                <CardDescription>Affichées sur vos factures pour le règlement par virement</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="iban">IBAN</Label>
                                        <Input id="iban" placeholder="FR76 1234 5678 9012 3456 7890 123" value={formData.iban} onChange={handleChange("iban")} className="font-mono" data-testid="iban-input" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="bic">BIC / SWIFT</Label>
                                        <Input id="bic" placeholder="BNPAFRPP" value={formData.bic} onChange={handleChange("bic")} className="font-mono" data-testid="bic-input" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Website */}
                        <Card className={!formData.website ? "border-orange-200 bg-orange-50/30" : ""}>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                    <Globe className="w-5 h-5" />
                                    Site web
                                </CardTitle>
                                <CardDescription>Votre présence en ligne</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="website">URL du site web</Label>
                                    <div className="flex gap-2">
                                        <Input 
                                            id="website" 
                                            type="url" 
                                            placeholder="https://votre-entreprise.fr" 
                                            value={formData.website} 
                                            onChange={handleChange("website")} 
                                            data-testid="website-input" 
                                        />
                                        {formData.website && (
                                            <Button 
                                                type="button" 
                                                variant="outline" 
                                                onClick={() => window.open(formData.website, '_blank')}
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </Button>
                                        )}
                                    </div>
                                </div>
                                
                                {!formData.website && (
                                    <div className="bg-orange-100 border border-orange-200 rounded-lg p-4">
                                        <div className="flex items-start gap-3">
                                            <Globe className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                                            <div>
                                                <p className="font-medium text-orange-900">
                                                    Votre entreprise ne possède pas encore de site web
                                                </p>
                                                <p className="text-sm text-orange-800 mt-1">
                                                    Un site web professionnel vous permet d'être visible sur internet et d'attirer de nouveaux clients.
                                                </p>
                                                <Button 
                                                    type="button"
                                                    onClick={() => setShowWebsiteDialog(true)}
                                                    className="mt-3 bg-orange-600 hover:bg-orange-700"
                                                    data-testid="request-website-btn"
                                                >
                                                    <Globe className="w-4 h-4 mr-2" />
                                                    Demander une création de site
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Document Appearance */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                    <Palette className="w-5 h-5" />
                                    Apparence des documents
                                </CardTitle>
                                <CardDescription>Personnalisez la couleur de vos devis et factures</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-3">
                                    <Label>Couleur principale</Label>
                                    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                                        {THEME_COLOR_OPTIONS.map((option) => (
                                            <button
                                                key={option.value}
                                                type="button"
                                                onClick={() => setFormData(prev => ({ ...prev, document_theme_color: option.value }))}
                                                className={`relative p-3 rounded-lg border-2 transition-all ${
                                                    formData.document_theme_color === option.value
                                                        ? 'border-slate-900 ring-2 ring-slate-900/20'
                                                        : 'border-slate-200 hover:border-slate-300'
                                                }`}
                                                data-testid={`theme-color-${option.value}`}
                                            >
                                                <div 
                                                    className={`w-full h-8 rounded-md ${option.preview}`}
                                                    style={{ backgroundColor: option.color }}
                                                />
                                                <p className="text-xs text-center mt-2 font-medium text-slate-700">
                                                    {option.label}
                                                </p>
                                                {formData.document_theme_color === option.value && (
                                                    <div className="absolute top-1 right-1 w-5 h-5 bg-slate-900 rounded-full flex items-center justify-center">
                                                        <Check className="w-3 h-3 text-white" />
                                                    </div>
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                
                                {/* Preview */}
                                <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                                    <p className="text-sm font-medium text-slate-500 mb-3">Aperçu</p>
                                    <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
                                        <div 
                                            className="h-3"
                                            style={{ backgroundColor: THEME_COLOR_OPTIONS.find(o => o.value === formData.document_theme_color)?.color || '#2563EB' }}
                                        />
                                        <div className="p-4 space-y-3">
                                            <div className="flex justify-between items-center">
                                                <div>
                                                    <p className="font-bold text-sm">{formData.company_name || "Votre Entreprise"}</p>
                                                    <p className="text-xs text-slate-500">DEVIS N° 2026-0001</p>
                                                </div>
                                                <div 
                                                    className="px-3 py-1 rounded text-white text-xs font-medium"
                                                    style={{ backgroundColor: THEME_COLOR_OPTIONS.find(o => o.value === formData.document_theme_color)?.color || '#2563EB' }}
                                                >
                                                    En attente
                                                </div>
                                            </div>
                                            <div className="border-t pt-2">
                                                <div 
                                                    className="text-xs px-2 py-1 rounded text-white font-medium inline-block"
                                                    style={{ backgroundColor: THEME_COLOR_OPTIONS.find(o => o.value === formData.document_theme_color)?.color || '#2563EB' }}
                                                >
                                                    Description | Qté | Prix
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Payment Settings */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="font-['Barlow_Condensed']">Conditions de paiement</CardTitle>
                                <CardDescription>Paramètres par défaut pour vos factures</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="payment_delay">Délai de paiement par défaut</Label>
                                        <div className="flex items-center gap-2">
                                            <Input 
                                                id="payment_delay" 
                                                type="number" 
                                                min="0" 
                                                max="90" 
                                                value={formData.default_payment_delay_days} 
                                                onChange={(e) => setFormData(prev => ({ ...prev, default_payment_delay_days: parseInt(e.target.value) || 30 }))}
                                                className="w-24"
                                                data-testid="payment-delay-input"
                                            />
                                            <span className="text-slate-500">jours</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600">
                                    <p><strong>Mentions légales automatiques sur les factures :</strong></p>
                                    <ul className="list-disc list-inside mt-1 text-xs">
                                        <li>Pénalités de retard au taux légal (3x le taux d'intérêt légal)</li>
                                        <li>Indemnité forfaitaire de recouvrement de 40 €</li>
                                    </ul>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Retenue de Garantie Settings */}
                        <Card className={formData.default_retenue_garantie_enabled ? "border-amber-300 bg-amber-50/50" : ""}>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                            <AlertTriangle className="w-5 h-5 text-amber-600" />
                                            Retenue de garantie (BTP)
                                        </CardTitle>
                                        <CardDescription>Paramètres par défaut pour la retenue de garantie</CardDescription>
                                    </div>
                                    <Switch 
                                        checked={formData.default_retenue_garantie_enabled} 
                                        onCheckedChange={(checked) => setFormData(prev => ({ ...prev, default_retenue_garantie_enabled: checked }))}
                                        data-testid="retenue-garantie-toggle"
                                    />
                                </div>
                            </CardHeader>
                            {formData.default_retenue_garantie_enabled && (
                                <CardContent className="space-y-4">
                                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                                        <div className="flex items-start gap-2">
                                            <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                                            <div className="text-sm text-amber-800">
                                                <p className="font-medium">Loi n°75-1334 du 31 décembre 1975</p>
                                                <p className="mt-1">La retenue de garantie ne peut excéder 5% du montant TTC des travaux. Elle peut être remplacée par une caution bancaire à la demande du prestataire.</p>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="retenue_rate">Taux de retenue par défaut</Label>
                                            <div className="flex items-center gap-2">
                                                <Input 
                                                    id="retenue_rate" 
                                                    type="number" 
                                                    min="0.5" 
                                                    max="5" 
                                                    step="0.5"
                                                    value={formData.default_retenue_garantie_rate} 
                                                    onChange={(e) => setFormData(prev => ({ 
                                                        ...prev, 
                                                        default_retenue_garantie_rate: Math.min(5, parseFloat(e.target.value) || 5)
                                                    }))}
                                                    className="w-24"
                                                    data-testid="retenue-rate-input"
                                                />
                                                <span className="text-slate-500">% (max 5%)</span>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="retenue_duration">Durée de garantie par défaut</Label>
                                            <Select
                                                value={String(formData.default_retenue_garantie_duration_months)}
                                                onValueChange={(v) => setFormData(prev => ({ ...prev, default_retenue_garantie_duration_months: parseInt(v) }))}
                                            >
                                                <SelectTrigger className="w-48" data-testid="retenue-duration-select">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="6">6 mois</SelectItem>
                                                    <SelectItem value="12">12 mois (1 an)</SelectItem>
                                                    <SelectItem value="24">24 mois (2 ans)</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                    
                                    <div className="bg-white border rounded-lg p-3 text-sm text-slate-600">
                                        <p><strong>Mention légale sur les factures :</strong></p>
                                        <p className="mt-1 italic text-xs">
                                            "Une retenue de garantie de X% est appliquée conformément à la loi n°75-1334 du 31 décembre 1975. Cette retenue sera libérée [date], sauf réserves non levées."
                                        </p>
                                    </div>
                                </CardContent>
                            )}
                        </Card>

                        {/* VAT Rates */}
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <div>
                                    <CardTitle className="font-['Barlow_Condensed']">Taux de TVA par défaut</CardTitle>
                                    <CardDescription>Définissez les taux de TVA disponibles</CardDescription>
                                </div>
                                <Button type="button" variant="outline" size="sm" onClick={addVatRate}>
                                    <Plus className="w-4 h-4 mr-2" />Ajouter
                                </Button>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {formData.default_vat_rates.map((rate, index) => (
                                        <div key={index} className="flex items-center gap-3">
                                            <Input type="number" min="0" max="100" step="0.1" value={rate} onChange={(e) => updateVatRate(index, e.target.value)} className="w-32" />
                                            <span className="text-slate-500">%</span>
                                            <Button type="button" variant="ghost" size="icon" onClick={() => removeVatRate(index)} disabled={formData.default_vat_rates.length === 1} className="hover:bg-red-50 hover:text-red-600">
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        <div className="flex justify-end">
                            <Button type="submit" className="bg-orange-600 hover:bg-orange-700" disabled={saving} data-testid="save-settings-btn">
                                <Save className="w-4 h-4 mr-2" />{saving ? "Enregistrement..." : "Enregistrer"}
                            </Button>
                        </div>
                    </form>
                </TabsContent>

                {/* Predefined Items Tab */}
                <TabsContent value="items" className="space-y-6">
                    {/* Add New Item */}
                    <Card className="border-orange-200 bg-orange-50/50">
                        <CardHeader>
                            <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                <Plus className="w-5 h-5 text-orange-600" />
                                Ajouter un article
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
                                <div className="md:col-span-2">
                                    <Label className="text-xs">Catégorie</Label>
                                    <Select value={newItem.category} onValueChange={(v) => setNewItem(p => ({ ...p, category: v }))}>
                                        <SelectTrigger><SelectValue placeholder="Choisir" /></SelectTrigger>
                                        <SelectContent>
                                            {DEFAULT_CATEGORIES.map(cat => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="md:col-span-2">
                                    <Label className="text-xs">Description</Label>
                                    <Input placeholder="Description de l'article" value={newItem.description} onChange={(e) => setNewItem(p => ({ ...p, description: e.target.value }))} />
                                </div>
                                <div>
                                    <Label className="text-xs">Unité</Label>
                                    <Select value={newItem.unit} onValueChange={(v) => setNewItem(p => ({ ...p, unit: v }))}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            {UNIT_OPTIONS.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div>
                                    <Label className="text-xs">Prix défaut (€)</Label>
                                    <Input type="number" min="0" step="0.01" value={newItem.default_price} onChange={(e) => setNewItem(p => ({ ...p, default_price: parseFloat(e.target.value) || 0 }))} />
                                </div>
                            </div>
                            <div className="mt-4 flex justify-end">
                                <Button onClick={handleCreateItem} className="bg-orange-600 hover:bg-orange-700" data-testid="create-item-btn">
                                    <Plus className="w-4 h-4 mr-2" />Créer l'article
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Category Tabs */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle className="font-['Barlow_Condensed']">Articles par catégorie</CardTitle>
                            <Button variant="outline" size="sm" onClick={() => setShowResetDialog(true)} className="text-amber-600 border-amber-300 hover:bg-amber-50">
                                <RefreshCw className="w-4 h-4 mr-2" />Réinitialiser
                            </Button>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-wrap gap-2 mb-4">
                                {categories.map(cat => (
                                    <Button
                                        key={cat.name}
                                        variant={selectedCategory === cat.name ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setSelectedCategory(cat.name)}
                                        className={selectedCategory === cat.name ? "bg-orange-600 hover:bg-orange-700" : ""}
                                    >
                                        {cat.name} ({cat.items.length})
                                    </Button>
                                ))}
                            </div>

                            <div className="space-y-2 max-h-96 overflow-y-auto">
                                {currentCategoryItems.length === 0 ? (
                                    <p className="text-center text-slate-500 py-8">Aucun article dans cette catégorie</p>
                                ) : (
                                    currentCategoryItems.map(item => (
                                        <div key={item.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                            {editingItem?.id === item.id ? (
                                                <>
                                                    <Input className="flex-1" value={editingItem.description} onChange={(e) => setEditingItem(p => ({ ...p, description: e.target.value }))} />
                                                    <Select value={editingItem.unit} onValueChange={(v) => setEditingItem(p => ({ ...p, unit: v }))}>
                                                        <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                                                        <SelectContent>{UNIT_OPTIONS.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}</SelectContent>
                                                    </Select>
                                                    <Input type="number" className="w-24" value={editingItem.default_price} onChange={(e) => setEditingItem(p => ({ ...p, default_price: parseFloat(e.target.value) || 0 }))} />
                                                    <Button size="sm" onClick={handleUpdateItem} className="bg-green-600 hover:bg-green-700">OK</Button>
                                                    <Button size="sm" variant="ghost" onClick={() => setEditingItem(null)}>Annuler</Button>
                                                </>
                                            ) : (
                                                <>
                                                    <span className="flex-1 font-medium">{item.description}</span>
                                                    <span className="text-slate-500 w-16 text-center">{item.unit}</span>
                                                    <span className="font-medium w-20 text-right">{item.default_price.toFixed(2)} €</span>
                                                    <Button variant="ghost" size="icon" onClick={() => setEditingItem(item)} className="hover:bg-blue-50 hover:text-blue-600">
                                                        <Pencil className="w-4 h-4" />
                                                    </Button>
                                                    <Button variant="ghost" size="icon" onClick={() => setShowDeleteDialog(item.id)} className="hover:bg-red-50 hover:text-red-600">
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Kits Tab */}
                <TabsContent value="kits" className="space-y-6">
                    {/* Create Kit Button */}
                    <Card className="border-blue-200 bg-blue-50/50">
                        <CardHeader>
                            <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                <Plus className="w-5 h-5 text-blue-600" />
                                Créer un kit de rénovation
                            </CardTitle>
                            <CardDescription>
                                Les kits permettent d'ajouter plusieurs lignes à un devis en un seul clic
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button onClick={() => setShowNewKitModal(true)} className="bg-blue-600 hover:bg-blue-700" data-testid="create-kit-btn">
                                <Plus className="w-4 h-4 mr-2" />Nouveau kit
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Kits List */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle className="font-['Barlow_Condensed']">Kits disponibles ({kits.length})</CardTitle>
                            <Button variant="outline" size="sm" onClick={() => setShowResetKitsDialog(true)} className="text-amber-600 border-amber-300 hover:bg-amber-50">
                                <RefreshCw className="w-4 h-4 mr-2" />Réinitialiser
                            </Button>
                        </CardHeader>
                        <CardContent>
                            {kits.length === 0 ? (
                                <p className="text-center text-slate-500 py-8">Aucun kit disponible</p>
                            ) : (
                                <div className="space-y-3">
                                    {kits.map(kit => (
                                        <div key={kit.id} className="border rounded-lg overflow-hidden">
                                            <div 
                                                className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50"
                                                onClick={() => setExpandedKit(expandedKit === kit.id ? null : kit.id)}
                                            >
                                                <div className="flex items-center gap-3">
                                                    {expandedKit === kit.id ? (
                                                        <ChevronUp className="w-4 h-4 text-slate-400" />
                                                    ) : (
                                                        <ChevronDown className="w-4 h-4 text-slate-400" />
                                                    )}
                                                    <div>
                                                        <h3 className="font-semibold">{kit.name}</h3>
                                                        <p className="text-sm text-slate-500">
                                                            {kit.items.length} lignes • {kit.is_default ? "Kit par défaut" : "Kit personnalisé"}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="font-medium text-orange-600">{calculateKitTotal(kit.items)} € HT</span>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon" 
                                                        onClick={(e) => { e.stopPropagation(); setShowDeleteKitDialog(kit.id); }}
                                                        className="hover:bg-red-50 hover:text-red-600"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                            {expandedKit === kit.id && (
                                                <div className="border-t bg-slate-50 p-4">
                                                    {kit.description && (
                                                        <p className="text-sm text-slate-600 mb-3">{kit.description}</p>
                                                    )}
                                                    <div className="space-y-2">
                                                        {kit.items.map((item, idx) => (
                                                            <div key={idx} className="flex items-center gap-3 text-sm bg-white p-2 rounded">
                                                                <span className="flex-1">{item.description}</span>
                                                                <span className="text-slate-500 w-16">{item.quantity} {item.unit}</span>
                                                                <span className="font-medium w-20 text-right">{item.unit_price.toFixed(2)} €</span>
                                                                <span className="text-slate-400 w-16 text-right">{(item.quantity * item.unit_price).toFixed(2)} €</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!showDeleteDialog} onOpenChange={() => setShowDeleteDialog(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Supprimer l'article ?</AlertDialogTitle>
                        <AlertDialogDescription>Cette action est irréversible.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDeleteItem} className="bg-red-600 hover:bg-red-700">Supprimer</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Reset Confirmation Dialog */}
            <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Réinitialiser les articles ?</AlertDialogTitle>
                        <AlertDialogDescription>Tous vos articles personnalisés seront remplacés par les articles par défaut BTP.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={handleResetItems} className="bg-amber-600 hover:bg-amber-700">Réinitialiser</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Delete Kit Dialog */}
            <AlertDialog open={!!showDeleteKitDialog} onOpenChange={() => setShowDeleteKitDialog(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Supprimer ce kit ?</AlertDialogTitle>
                        <AlertDialogDescription>Cette action est irréversible.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDeleteKit} className="bg-red-600 hover:bg-red-700">Supprimer</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Reset Kits Dialog */}
            <AlertDialog open={showResetKitsDialog} onOpenChange={setShowResetKitsDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Réinitialiser les kits ?</AlertDialogTitle>
                        <AlertDialogDescription>Tous vos kits personnalisés seront supprimés et remplacés par les kits par défaut.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={handleResetKits} className="bg-amber-600 hover:bg-amber-700">Réinitialiser</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* New Kit Modal */}
            <Dialog open={showNewKitModal} onOpenChange={setShowNewKitModal}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <Layers className="w-5 h-5 text-blue-600" />
                            Créer un nouveau kit
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 mt-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Nom du kit *</Label>
                                <Input
                                    placeholder="Ex: Rénovation salle de bain"
                                    value={newKit.name}
                                    onChange={(e) => setNewKit(prev => ({ ...prev, name: e.target.value }))}
                                    data-testid="new-kit-name"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Description</Label>
                                <Input
                                    placeholder="Description du kit..."
                                    value={newKit.description}
                                    onChange={(e) => setNewKit(prev => ({ ...prev, description: e.target.value }))}
                                />
                            </div>
                        </div>

                        <div className="border-t pt-4">
                            <div className="flex items-center justify-between mb-3">
                                <Label className="text-base font-semibold">Lignes du kit</Label>
                                <Button type="button" variant="outline" size="sm" onClick={addKitItem}>
                                    <Plus className="w-4 h-4 mr-2" />Ajouter ligne
                                </Button>
                            </div>
                            <div className="space-y-3">
                                {newKit.items.map((item, index) => (
                                    <div key={index} className="grid grid-cols-12 gap-2 items-end p-3 bg-slate-50 rounded-lg">
                                        <div className="col-span-12 md:col-span-4">
                                            <Label className="text-xs">Description</Label>
                                            <Input
                                                placeholder="Description"
                                                value={item.description}
                                                onChange={(e) => updateKitItem(index, "description", e.target.value)}
                                            />
                                        </div>
                                        <div className="col-span-4 md:col-span-2">
                                            <Label className="text-xs">Unité</Label>
                                            <Select value={item.unit} onValueChange={(v) => updateKitItem(index, "unit", v)}>
                                                <SelectTrigger><SelectValue /></SelectTrigger>
                                                <SelectContent>
                                                    {UNIT_OPTIONS.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="col-span-3 md:col-span-2">
                                            <Label className="text-xs">Quantité</Label>
                                            <Input
                                                type="number"
                                                min="0"
                                                step="0.1"
                                                value={item.quantity}
                                                onChange={(e) => updateKitItem(index, "quantity", parseFloat(e.target.value) || 0)}
                                            />
                                        </div>
                                        <div className="col-span-3 md:col-span-2">
                                            <Label className="text-xs">Prix €</Label>
                                            <Input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                value={item.unit_price}
                                                onChange={(e) => updateKitItem(index, "unit_price", parseFloat(e.target.value) || 0)}
                                            />
                                        </div>
                                        <div className="col-span-2 md:col-span-2 flex items-end gap-2">
                                            <span className="text-sm font-medium flex-1 text-right">
                                                {(item.quantity * item.unit_price).toFixed(2)} €
                                            </span>
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => removeKitItem(index)}
                                                disabled={newKit.items.length === 1}
                                                className="hover:bg-red-50 hover:text-red-600"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-4 text-right">
                                <span className="text-lg font-bold">Total: {calculateKitTotal(newKit.items)} € HT</span>
                            </div>
                        </div>
                    </div>
                    <DialogFooter className="mt-4">
                        <Button type="button" variant="outline" onClick={() => setShowNewKitModal(false)}>
                            Annuler
                        </Button>
                        <Button type="button" onClick={handleCreateKit} className="bg-blue-600 hover:bg-blue-700" data-testid="confirm-create-kit">
                            <Plus className="w-4 h-4 mr-2" />Créer le kit
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Website Request Dialog */}
            <WebsiteRequestDialog 
                open={showWebsiteDialog} 
                onOpenChange={setShowWebsiteDialog} 
            />
        </div>
    );
}
