import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getQuote, getClients, createQuote, updateQuote, getSettings, getPredefinedCategories, getKits, createKit } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ArrowLeft, Save, Plus, Trash2, Package, Layers, BookmarkPlus } from "lucide-react";
import { toast } from "sonner";

export default function QuoteFormPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const isEdit = !!id;
    
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [clients, setClients] = useState([]);
    const [vatRates, setVatRates] = useState([20.0, 10.0, 5.5, 2.1]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState("");
    const [selectedItem, setSelectedItem] = useState("");
    const [kits, setKits] = useState([]);
    const [showKitModal, setShowKitModal] = useState(false);
    const [showSaveKitModal, setShowSaveKitModal] = useState(false);
    const [newKitName, setNewKitName] = useState("");
    const [newKitDescription, setNewKitDescription] = useState("");
    
    const [formData, setFormData] = useState({
        client_id: "",
        validity_days: 30,
        notes: "",
        items: [{ description: "", quantity: 1, unit_price: 0, vat_rate: 20.0, unit: "" }]
    });

    useEffect(() => {
        loadData();
    }, [id]);

    const loadData = async () => {
        try {
            const [clientsRes, settingsRes, categoriesRes, kitsRes] = await Promise.all([
                getClients(),
                getSettings(),
                getPredefinedCategories(),
                getKits()
            ]);
            setClients(clientsRes.data);
            setCategories(categoriesRes.data);
            setKits(kitsRes.data);
            
            if (settingsRes.data.default_vat_rates?.length > 0) {
                setVatRates(settingsRes.data.default_vat_rates);
            }

            if (isEdit) {
                const quoteRes = await getQuote(id);
                setFormData({
                    client_id: quoteRes.data.client_id,
                    validity_days: 30,
                    notes: quoteRes.data.notes || "",
                    items: quoteRes.data.items.length > 0 
                        ? quoteRes.data.items.map(item => ({ ...item, unit: item.unit || "" }))
                        : [{ description: "", quantity: 1, unit_price: 0, vat_rate: 20.0, unit: "" }]
                });
            }
        } catch (error) {
            toast.error("Erreur lors du chargement des données");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.client_id) {
            toast.error("Veuillez sélectionner un client");
            return;
        }
        
        const validItems = formData.items.filter(item => item.description.trim());
        if (validItems.length === 0) {
            toast.error("Ajoutez au moins une ligne au devis");
            return;
        }

        setSaving(true);
        try {
            const payload = {
                ...formData,
                items: validItems.map(item => ({
                    description: item.unit ? `${item.description} (${item.unit})` : item.description,
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    vat_rate: item.vat_rate
                }))
            };
            
            if (isEdit) {
                await updateQuote(id, payload);
                toast.success("Devis mis à jour avec succès");
            } else {
                await createQuote(payload);
                toast.success("Devis créé avec succès");
            }
            navigate("/devis");
        } catch (error) {
            toast.error("Erreur lors de l'enregistrement du devis");
        } finally {
            setSaving(false);
        }
    };

    const addItem = () => {
        setFormData(prev => ({
            ...prev,
            items: [...prev.items, { description: "", quantity: 1, unit_price: 0, vat_rate: vatRates[0] || 20.0, unit: "" }]
        }));
    };

    const addPredefinedItem = () => {
        if (!selectedCategory || !selectedItem) {
            toast.error("Sélectionnez une catégorie et un article");
            return;
        }
        
        const category = categories.find(c => c.name === selectedCategory);
        if (!category) return;
        
        const item = category.items.find(i => i.id === selectedItem);
        if (!item) return;
        
        setFormData(prev => ({
            ...prev,
            items: [...prev.items, {
                description: item.description,
                quantity: 1,
                unit_price: item.default_price,
                vat_rate: item.default_vat_rate,
                unit: item.unit
            }]
        }));
        
        setSelectedItem("");
        toast.success("Article ajouté");
    };

    const addKit = (kit) => {
        const newItems = kit.items.map(item => ({
            description: item.description,
            quantity: item.quantity,
            unit_price: item.unit_price,
            vat_rate: item.vat_rate,
            unit: item.unit || ""
        }));
        
        setFormData(prev => ({
            ...prev,
            items: [...prev.items.filter(item => item.description.trim()), ...newItems]
        }));
        
        setShowKitModal(false);
        toast.success(`Kit "${kit.name}" ajouté avec ${kit.items.length} lignes`);
    };

    const saveAsKit = async () => {
        if (!newKitName.trim()) {
            toast.error("Veuillez saisir un nom pour le kit");
            return;
        }
        
        const validItems = formData.items.filter(item => item.description.trim());
        if (validItems.length === 0) {
            toast.error("Le devis doit contenir au moins une ligne");
            return;
        }
        
        try {
            await createKit({
                name: newKitName,
                description: newKitDescription,
                items: validItems.map(item => ({
                    description: item.description,
                    unit: item.unit || "unité",
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    vat_rate: item.vat_rate
                }))
            });
            
            // Refresh kits list
            const kitsRes = await getKits();
            setKits(kitsRes.data);
            
            setShowSaveKitModal(false);
            setNewKitName("");
            setNewKitDescription("");
            toast.success("Kit sauvegardé avec succès");
        } catch (error) {
            toast.error("Erreur lors de la sauvegarde du kit");
        }
    };

    const removeItem = (index) => {
        if (formData.items.length === 1) return;
        setFormData(prev => ({
            ...prev,
            items: prev.items.filter((_, i) => i !== index)
        }));
    };

    const updateItem = (index, field, value) => {
        setFormData(prev => ({
            ...prev,
            items: prev.items.map((item, i) => 
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    const calculateTotals = () => {
        let totalHT = 0;
        let totalVAT = 0;
        
        formData.items.forEach(item => {
            const lineHT = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
            const lineVAT = lineHT * ((parseFloat(item.vat_rate) || 0) / 100);
            totalHT += lineHT;
            totalVAT += lineVAT;
        });
        
        return {
            totalHT: totalHT.toFixed(2),
            totalVAT: totalVAT.toFixed(2),
            totalTTC: (totalHT + totalVAT).toFixed(2)
        };
    };

    const totals = calculateTotals();
    const selectedCategoryItems = categories.find(c => c.name === selectedCategory)?.items || [];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="quote-form-page">
            <div className="flex items-center gap-4">
                <Button variant="ghost" onClick={() => navigate("/devis")} data-testid="back-btn">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Retour
                </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed'] text-2xl">
                            {isEdit ? "Modifier le devis" : "Nouveau devis"}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Client *</Label>
                                <Select 
                                    value={formData.client_id} 
                                    onValueChange={(v) => setFormData(prev => ({ ...prev, client_id: v }))}
                                >
                                    <SelectTrigger data-testid="client-select">
                                        <SelectValue placeholder="Sélectionner un client" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {clients.map(client => (
                                            <SelectItem key={client.id} value={client.id}>
                                                {client.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                {clients.length === 0 && (
                                    <p className="text-sm text-amber-600">
                                        Aucun client. <a href="/clients/new" className="underline">Créer un client</a>
                                    </p>
                                )}
                            </div>
                            <div className="space-y-2">
                                <Label>Validité (jours)</Label>
                                <Input
                                    type="number"
                                    min="1"
                                    value={formData.validity_days}
                                    onChange={(e) => setFormData(prev => ({ ...prev, validity_days: parseInt(e.target.value) || 30 }))}
                                    data-testid="validity-input"
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Predefined Items Selector */}
                <Card className="border-orange-200 bg-orange-50/50">
                    <CardHeader className="pb-3">
                        <CardTitle className="font-['Barlow_Condensed'] text-lg flex items-center gap-2">
                            <Package className="w-5 h-5 text-orange-600" />
                            Ajouter un article prédéfini
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="space-y-1">
                                <Label className="text-xs">Catégorie</Label>
                                <Select value={selectedCategory} onValueChange={(v) => { setSelectedCategory(v); setSelectedItem(""); }}>
                                    <SelectTrigger data-testid="category-select">
                                        <SelectValue placeholder="Choisir une catégorie" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {categories.map(cat => (
                                            <SelectItem key={cat.name} value={cat.name}>{cat.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-1">
                                <Label className="text-xs">Article</Label>
                                <Select value={selectedItem} onValueChange={setSelectedItem} disabled={!selectedCategory}>
                                    <SelectTrigger data-testid="predefined-item-select">
                                        <SelectValue placeholder="Choisir un article" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {selectedCategoryItems.map(item => (
                                            <SelectItem key={item.id} value={item.id}>
                                                {item.description} ({item.default_price}€/{item.unit})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="flex items-end">
                                <Button 
                                    type="button" 
                                    onClick={addPredefinedItem}
                                    className="bg-orange-600 hover:bg-orange-700 w-full"
                                    disabled={!selectedCategory || !selectedItem}
                                    data-testid="add-predefined-btn"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Ajouter
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Line Items */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="font-['Barlow_Condensed']">Lignes du devis</CardTitle>
                        <Button type="button" variant="outline" size="sm" onClick={addItem} data-testid="add-item-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Ligne manuelle
                        </Button>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {formData.items.map((item, index) => (
                            <div key={index} className="grid grid-cols-12 gap-2 items-end p-4 bg-slate-50 rounded-lg" data-testid={`item-row-${index}`}>
                                <div className="col-span-12 md:col-span-4 space-y-1">
                                    <Label className="text-xs">Description</Label>
                                    <Input
                                        placeholder="Description du service..."
                                        value={item.description}
                                        onChange={(e) => updateItem(index, "description", e.target.value)}
                                        data-testid={`item-description-${index}`}
                                    />
                                </div>
                                <div className="col-span-3 md:col-span-1 space-y-1">
                                    <Label className="text-xs">Unité</Label>
                                    <Input
                                        placeholder="m², h..."
                                        value={item.unit || ""}
                                        onChange={(e) => updateItem(index, "unit", e.target.value)}
                                        className="text-center"
                                    />
                                </div>
                                <div className="col-span-3 md:col-span-2 space-y-1">
                                    <Label className="text-xs">Quantité</Label>
                                    <Input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={item.quantity}
                                        onChange={(e) => updateItem(index, "quantity", parseFloat(e.target.value) || 0)}
                                        data-testid={`item-quantity-${index}`}
                                    />
                                </div>
                                <div className="col-span-3 md:col-span-2 space-y-1">
                                    <Label className="text-xs">Prix unit. HT</Label>
                                    <Input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={item.unit_price}
                                        onChange={(e) => updateItem(index, "unit_price", parseFloat(e.target.value) || 0)}
                                        data-testid={`item-price-${index}`}
                                    />
                                </div>
                                <div className="col-span-2 md:col-span-1 space-y-1">
                                    <Label className="text-xs">TVA</Label>
                                    <Select value={String(item.vat_rate)} onValueChange={(v) => updateItem(index, "vat_rate", parseFloat(v))}>
                                        <SelectTrigger data-testid={`item-vat-${index}`}>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {vatRates.map(rate => (
                                                <SelectItem key={rate} value={String(rate)}>{rate}%</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="col-span-1 space-y-1">
                                    <Label className="text-xs opacity-0">X</Label>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeItem(index)}
                                        disabled={formData.items.length === 1}
                                        className="hover:bg-red-50 hover:text-red-600"
                                        data-testid={`remove-item-${index}`}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                                <div className="col-span-12 md:col-span-1 text-right">
                                    <p className="text-sm font-medium text-slate-700">
                                        {((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)).toFixed(2)} €
                                    </p>
                                </div>
                            </div>
                        ))}

                        <div className="border-t pt-4 mt-4 space-y-2">
                            <div className="flex justify-end gap-8 text-sm">
                                <span className="text-slate-500">Total HT:</span>
                                <span className="font-medium w-24 text-right">{totals.totalHT} €</span>
                            </div>
                            <div className="flex justify-end gap-8 text-sm">
                                <span className="text-slate-500">Total TVA:</span>
                                <span className="font-medium w-24 text-right">{totals.totalVAT} €</span>
                            </div>
                            <div className="flex justify-end gap-8 text-lg font-bold">
                                <span className="text-slate-900">Total TTC:</span>
                                <span className="text-orange-600 w-24 text-right">{totals.totalTTC} €</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed']">Notes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Textarea
                            placeholder="Notes ou conditions particulières..."
                            value={formData.notes}
                            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                            rows={3}
                            data-testid="notes-input"
                        />
                    </CardContent>
                </Card>

                <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => navigate("/devis")}>
                        Annuler
                    </Button>
                    <Button type="submit" className="bg-orange-600 hover:bg-orange-700" disabled={saving} data-testid="submit-btn">
                        {saving ? (
                            <span className="flex items-center gap-2">
                                <span className="spinner w-4 h-4"></span>
                                Enregistrement...
                            </span>
                        ) : (
                            <>
                                <Save className="w-4 h-4 mr-2" />
                                {isEdit ? "Mettre à jour" : "Créer le devis"}
                            </>
                        )}
                    </Button>
                </div>
            </form>
        </div>
    );
}
