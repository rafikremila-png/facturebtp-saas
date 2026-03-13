import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
    Library, Plus, Search, Edit2, Trash2, Copy, Filter, 
    Package, Euro, FileText, ChevronRight, MoreVertical,
    Building2, Hammer, Wrench, Zap, Paintbrush, Layers, Settings2
} from "lucide-react";
import { toast } from "sonner";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Categories BTP avec icônes
const BTP_CATEGORIES = {
    gros_oeuvre: { label: "Gros œuvre", icon: Building2, color: "bg-slate-600" },
    second_oeuvre: { label: "Second œuvre", icon: Hammer, color: "bg-amber-600" },
    plomberie: { label: "Plomberie", icon: Wrench, color: "bg-blue-600" },
    electricite: { label: "Électricité", icon: Zap, color: "bg-yellow-600" },
    peinture: { label: "Peinture", icon: Paintbrush, color: "bg-pink-600" },
    menuiserie: { label: "Menuiserie", icon: Layers, color: "bg-orange-600" },
    carrelage: { label: "Carrelage", icon: Layers, color: "bg-cyan-600" },
    isolation: { label: "Isolation", icon: Building2, color: "bg-green-600" },
    toiture: { label: "Toiture", icon: Building2, color: "bg-red-600" },
    amenagements: { label: "Aménagements", icon: Settings2, color: "bg-purple-600" },
    autres: { label: "Autres", icon: Package, color: "bg-gray-600" }
};

// Unités disponibles
const UNITS = [
    { value: "u", label: "Unité (u)" },
    { value: "m²", label: "Mètre carré (m²)" },
    { value: "m³", label: "Mètre cube (m³)" },
    { value: "ml", label: "Mètre linéaire (ml)" },
    { value: "h", label: "Heure (h)" },
    { value: "jour", label: "Jour" },
    { value: "forfait", label: "Forfait" },
    { value: "kg", label: "Kilogramme (kg)" },
    { value: "l", label: "Litre (l)" },
    { value: "m", label: "Mètre (m)" }
];

export default function WorkLibraryPage() {
    const [items, setItems] = useState([]);
    const [categories, setCategories] = useState([]);
    const [units, setUnits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("all");
    
    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [selectedItem, setSelectedItem] = useState(null);
    
    // Form state
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        category: "autres",
        unit: "u",
        unit_price: 0,
        vat_rate: 20,
        labor_cost: null,
        material_cost: null,
        is_template: false
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [itemsRes, categoriesRes, unitsRes] = await Promise.all([
                api.get("/work-items"),
                api.get("/work-items/categories"),
                api.get("/work-items/units")
            ]);
            
            setItems(itemsRes.data);
            setCategories(categoriesRes.data.categories || []);
            setUnits(unitsRes.data || UNITS);
        } catch (error) {
            console.error("Erreur chargement:", error);
            toast.error("Erreur lors du chargement de la bibliothèque");
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!formData.name.trim()) {
            toast.error("Le nom est obligatoire");
            return;
        }
        
        try {
            await api.post("/work-items", formData);
            toast.success("Ouvrage créé avec succès");
            setShowCreateModal(false);
            resetForm();
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la création");
        }
    };

    const handleUpdate = async () => {
        if (!selectedItem || !formData.name.trim()) {
            toast.error("Le nom est obligatoire");
            return;
        }
        
        try {
            await api.put(`/work-items/${selectedItem.id}`, formData);
            toast.success("Ouvrage mis à jour avec succès");
            setShowEditModal(false);
            setSelectedItem(null);
            resetForm();
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la mise à jour");
        }
    };

    const handleDelete = async () => {
        if (!selectedItem) return;
        
        try {
            await api.delete(`/work-items/${selectedItem.id}`);
            toast.success("Ouvrage supprimé");
            setShowDeleteDialog(false);
            setSelectedItem(null);
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la suppression");
        }
    };

    const handleDuplicate = async (item) => {
        try {
            await api.post(`/work-items/${item.id}/duplicate`);
            toast.success("Ouvrage dupliqué");
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la duplication");
        }
    };

    const resetForm = () => {
        setFormData({
            name: "",
            description: "",
            category: "autres",
            unit: "u",
            unit_price: 0,
            vat_rate: 20,
            labor_cost: null,
            material_cost: null,
            is_template: false
        });
    };

    const openEditModal = (item) => {
        setSelectedItem(item);
        setFormData({
            name: item.name,
            description: item.description || "",
            category: item.category,
            unit: item.unit,
            unit_price: item.unit_price,
            vat_rate: item.vat_rate,
            labor_cost: item.labor_cost,
            material_cost: item.material_cost,
            is_template: item.is_template
        });
        setShowEditModal(true);
    };

    // Filtrer les items
    const filteredItems = items.filter(item => {
        const matchesSearch = !searchQuery || 
            item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (item.description && item.description.toLowerCase().includes(searchQuery.toLowerCase()));
        
        const matchesCategory = selectedCategory === "all" || item.category === selectedCategory;
        
        return matchesSearch && matchesCategory;
    });

    // Grouper par catégorie
    const groupedItems = filteredItems.reduce((acc, item) => {
        const cat = item.category || "autres";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(item);
        return acc;
    }, {});

    const formatPrice = (price) => {
        if (price == null || isNaN(price)) return '0,00 €';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(price);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6" data-testid="work-library-page">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
                        <Library className="w-8 h-8 text-orange-600" />
                        Bibliothèque d'ouvrages
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Gérez vos prestations et matériaux réutilisables ({items.length} ouvrages)
                    </p>
                </div>
                <Button 
                    onClick={() => setShowCreateModal(true)}
                    className="bg-orange-600 hover:bg-orange-700"
                    data-testid="create-work-item-btn"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Nouvel ouvrage
                </Button>
            </div>

            {/* Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <Input
                                placeholder="Rechercher un ouvrage..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                                data-testid="search-work-items"
                            />
                        </div>
                        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                            <SelectTrigger className="w-full md:w-48" data-testid="filter-category">
                                <Filter className="w-4 h-4 mr-2" />
                                <SelectValue placeholder="Catégorie" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Toutes les catégories</SelectItem>
                                {Object.entries(BTP_CATEGORIES).map(([key, { label }]) => (
                                    <SelectItem key={key} value={key}>{label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            {/* Items List */}
            {filteredItems.length === 0 ? (
                <Card>
                    <CardContent className="py-12">
                        <div className="text-center">
                            <Library className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-slate-900 mb-2">
                                Aucun ouvrage trouvé
                            </h3>
                            <p className="text-slate-500 mb-4">
                                {searchQuery || selectedCategory !== "all" 
                                    ? "Essayez de modifier vos filtres"
                                    : "Commencez par créer votre premier ouvrage"
                                }
                            </p>
                            {!searchQuery && selectedCategory === "all" && (
                                <Button 
                                    onClick={() => setShowCreateModal(true)}
                                    className="bg-orange-600 hover:bg-orange-700"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Créer un ouvrage
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-6">
                    {Object.entries(groupedItems).map(([categoryKey, categoryItems]) => {
                        const categoryInfo = BTP_CATEGORIES[categoryKey] || BTP_CATEGORIES.autres;
                        const CategoryIcon = categoryInfo.icon;
                        
                        return (
                            <Card key={categoryKey}>
                                <CardHeader className="pb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 ${categoryInfo.color} rounded-lg flex items-center justify-center`}>
                                            <CategoryIcon className="w-5 h-5 text-white" />
                                        </div>
                                        <div>
                                            <CardTitle className="font-['Barlow_Condensed'] text-lg">
                                                {categoryInfo.label}
                                            </CardTitle>
                                            <p className="text-sm text-slate-500">{categoryItems.length} ouvrage(s)</p>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        {categoryItems.map((item) => (
                                            <div 
                                                key={item.id}
                                                className="flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors group"
                                                data-testid={`work-item-${item.id}`}
                                            >
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="font-medium text-slate-900 truncate">
                                                            {item.name}
                                                        </h4>
                                                        {item.is_template && (
                                                            <Badge variant="secondary" className="text-xs">
                                                                Modèle
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    {item.description && (
                                                        <p className="text-sm text-slate-500 truncate mt-1">
                                                            {item.description}
                                                        </p>
                                                    )}
                                                </div>
                                                
                                                <div className="flex items-center gap-4 ml-4">
                                                    <div className="text-right">
                                                        <p className="font-semibold text-orange-600">
                                                            {formatPrice(item.unit_price)}
                                                        </p>
                                                        <p className="text-xs text-slate-500">
                                                            / {item.unit} • TVA {item.vat_rate}%
                                                        </p>
                                                    </div>
                                                    
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <Button 
                                                                variant="ghost" 
                                                                size="icon"
                                                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                                                            >
                                                                <MoreVertical className="w-4 h-4" />
                                                            </Button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuItem onClick={() => openEditModal(item)}>
                                                                <Edit2 className="w-4 h-4 mr-2" />
                                                                Modifier
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => handleDuplicate(item)}>
                                                                <Copy className="w-4 h-4 mr-2" />
                                                                Dupliquer
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem 
                                                                onClick={() => {
                                                                    setSelectedItem(item);
                                                                    setShowDeleteDialog(true);
                                                                }}
                                                                className="text-red-600"
                                                            >
                                                                <Trash2 className="w-4 h-4 mr-2" />
                                                                Supprimer
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}

            {/* Create Modal */}
            <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <Plus className="w-5 h-5 text-orange-600" />
                            Nouvel ouvrage
                        </DialogTitle>
                        <DialogDescription>
                            Créez un nouvel ouvrage réutilisable dans vos devis et factures
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Nom de l'ouvrage *</Label>
                            <Input
                                id="name"
                                placeholder="Ex: Pose de carrelage"
                                value={formData.name}
                                onChange={(e) => setFormData({...formData, name: e.target.value})}
                                data-testid="work-item-name"
                            />
                        </div>
                        
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                placeholder="Description détaillée de l'ouvrage..."
                                value={formData.description}
                                onChange={(e) => setFormData({...formData, description: e.target.value})}
                                rows={2}
                            />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="category">Catégorie</Label>
                                <Select 
                                    value={formData.category} 
                                    onValueChange={(v) => setFormData({...formData, category: v})}
                                >
                                    <SelectTrigger data-testid="work-item-category">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(BTP_CATEGORIES).map(([key, { label }]) => (
                                            <SelectItem key={key} value={key}>{label}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            
                            <div className="space-y-2">
                                <Label htmlFor="unit">Unité</Label>
                                <Select 
                                    value={formData.unit} 
                                    onValueChange={(v) => setFormData({...formData, unit: v})}
                                >
                                    <SelectTrigger data-testid="work-item-unit">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {UNITS.map((u) => (
                                            <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="unit_price">Prix unitaire HT (€)</Label>
                                <Input
                                    id="unit_price"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={formData.unit_price}
                                    onChange={(e) => setFormData({...formData, unit_price: parseFloat(e.target.value) || 0})}
                                    data-testid="work-item-price"
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label htmlFor="vat_rate">Taux TVA (%)</Label>
                                <Select 
                                    value={String(formData.vat_rate)} 
                                    onValueChange={(v) => setFormData({...formData, vat_rate: parseFloat(v)})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="20">20%</SelectItem>
                                        <SelectItem value="10">10%</SelectItem>
                                        <SelectItem value="5.5">5.5%</SelectItem>
                                        <SelectItem value="2.1">2.1%</SelectItem>
                                        <SelectItem value="0">0%</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="labor_cost">Coût main d'œuvre (€)</Label>
                                <Input
                                    id="labor_cost"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    placeholder="Optionnel"
                                    value={formData.labor_cost || ""}
                                    onChange={(e) => setFormData({...formData, labor_cost: e.target.value ? parseFloat(e.target.value) : null})}
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label htmlFor="material_cost">Coût matériaux (€)</Label>
                                <Input
                                    id="material_cost"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    placeholder="Optionnel"
                                    value={formData.material_cost || ""}
                                    onChange={(e) => setFormData({...formData, material_cost: e.target.value ? parseFloat(e.target.value) : null})}
                                />
                            </div>
                        </div>
                    </div>
                    
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleCreate}
                            className="bg-orange-600 hover:bg-orange-700"
                            data-testid="save-work-item-btn"
                        >
                            Créer l'ouvrage
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Edit Modal */}
            <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <Edit2 className="w-5 h-5 text-orange-600" />
                            Modifier l'ouvrage
                        </DialogTitle>
                    </DialogHeader>
                    
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="edit-name">Nom de l'ouvrage *</Label>
                            <Input
                                id="edit-name"
                                value={formData.name}
                                onChange={(e) => setFormData({...formData, name: e.target.value})}
                            />
                        </div>
                        
                        <div className="space-y-2">
                            <Label htmlFor="edit-description">Description</Label>
                            <Textarea
                                id="edit-description"
                                value={formData.description}
                                onChange={(e) => setFormData({...formData, description: e.target.value})}
                                rows={2}
                            />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Catégorie</Label>
                                <Select 
                                    value={formData.category} 
                                    onValueChange={(v) => setFormData({...formData, category: v})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(BTP_CATEGORIES).map(([key, { label }]) => (
                                            <SelectItem key={key} value={key}>{label}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            
                            <div className="space-y-2">
                                <Label>Unité</Label>
                                <Select 
                                    value={formData.unit} 
                                    onValueChange={(v) => setFormData({...formData, unit: v})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {UNITS.map((u) => (
                                            <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Prix unitaire HT (€)</Label>
                                <Input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={formData.unit_price}
                                    onChange={(e) => setFormData({...formData, unit_price: parseFloat(e.target.value) || 0})}
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label>Taux TVA (%)</Label>
                                <Select 
                                    value={String(formData.vat_rate)} 
                                    onValueChange={(v) => setFormData({...formData, vat_rate: parseFloat(v)})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="20">20%</SelectItem>
                                        <SelectItem value="10">10%</SelectItem>
                                        <SelectItem value="5.5">5.5%</SelectItem>
                                        <SelectItem value="2.1">2.1%</SelectItem>
                                        <SelectItem value="0">0%</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Coût main d'œuvre (€)</Label>
                                <Input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    placeholder="Optionnel"
                                    value={formData.labor_cost || ""}
                                    onChange={(e) => setFormData({...formData, labor_cost: e.target.value ? parseFloat(e.target.value) : null})}
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label>Coût matériaux (€)</Label>
                                <Input
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    placeholder="Optionnel"
                                    value={formData.material_cost || ""}
                                    onChange={(e) => setFormData({...formData, material_cost: e.target.value ? parseFloat(e.target.value) : null})}
                                />
                            </div>
                        </div>
                    </div>
                    
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEditModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleUpdate}
                            className="bg-orange-600 hover:bg-orange-700"
                        >
                            Enregistrer
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Supprimer cet ouvrage ?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Cette action est irréversible. L'ouvrage "{selectedItem?.name}" sera définitivement supprimé de votre bibliothèque.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-red-600 hover:bg-red-700"
                        >
                            Supprimer
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
