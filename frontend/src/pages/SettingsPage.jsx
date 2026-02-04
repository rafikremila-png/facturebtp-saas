import { useState, useEffect, useRef } from "react";
import { getSettings, updateSettings, uploadLogo, getPredefinedCategories, createPredefinedItem, updatePredefinedItem, deletePredefinedItem, resetPredefinedItems, getKits, createKit, updateKit, deleteKit, resetKits } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Building2, Save, Upload, Plus, Trash2, Package, RefreshCw, Pencil, Layers, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

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
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploadingLogo, setUploadingLogo] = useState(false);
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
        logo_base64: null
    });

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
                    logo_base64: settingsRes.data.logo_base64 || null
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
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="company" className="flex items-center gap-2">
                        <Building2 className="w-4 h-4" />
                        Entreprise
                    </TabsTrigger>
                    <TabsTrigger value="items" className="flex items-center gap-2">
                        <Package className="w-4 h-4" />
                        Articles prédéfinis
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
                                        <Label htmlFor="vat_number">Numéro de TVA</Label>
                                        <Input id="vat_number" placeholder="FR12 345678901" value={formData.vat_number} onChange={handleChange("vat_number")} className="font-mono" data-testid="vat-number-input" />
                                    </div>
                                </div>
                            </CardContent>
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
        </div>
    );
}
