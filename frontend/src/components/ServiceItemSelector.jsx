import { useState, useEffect } from "react";
import { getCategoriesWithItemsV3, getKitsV3, getKitV3 } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Plus, Package, Layers, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

/**
 * Simplified Service Item Selector
 * Direct Category -> Article selection (no subcategories)
 * 
 * Props:
 * - onAddItem: (item) => void - Called when a single item is added
 * - onAddMultipleItems: (items) => void - Called when a kit is added
 */
export default function ServiceItemSelector({ onAddItem, onAddMultipleItems }) {
    const [categories, setCategories] = useState([]);
    const [kits, setKits] = useState([]);
    const [loading, setLoading] = useState(true);
    
    const [selectedCategory, setSelectedCategory] = useState("");
    const [selectedItem, setSelectedItem] = useState("");
    
    const [items, setItems] = useState([]);
    
    // Kit dialog
    const [showKitDialog, setShowKitDialog] = useState(false);
    const [selectedKit, setSelectedKit] = useState(null);
    const [kitDetails, setKitDetails] = useState(null);
    const [loadingKit, setLoadingKit] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [categoriesRes, kitsRes] = await Promise.all([
                getCategoriesWithItemsV3(),
                getKitsV3()
            ]);
            setCategories(categoriesRes.data || []);
            setKits(kitsRes.data || []);
        } catch (error) {
            console.error("Error loading categories:", error);
            toast.error("Erreur lors du chargement des catégories");
        } finally {
            setLoading(false);
        }
    };

    const handleCategoryChange = (categoryId) => {
        setSelectedCategory(categoryId);
        setSelectedItem("");
        
        // Find items for this category
        const category = categories.find(c => c.id === categoryId);
        setItems(category?.items || []);
    };

    const handleAddItem = () => {
        if (!selectedItem) {
            toast.error("Sélectionnez un article");
            return;
        }
        
        const item = items.find(i => i.id === selectedItem);
        if (!item) return;
        
        onAddItem({
            description: item.name,
            quantity: 1,
            unit_price: item.smart_price || item.default_price || 0,
            vat_rate: 20,
            unit: item.unit || "unité"
        });
        
        setSelectedItem("");
        toast.success("Article ajouté");
    };

    const handleSelectKit = async (kitId) => {
        setSelectedKit(kitId);
        setLoadingKit(true);
        
        try {
            const response = await getKitV3(kitId);
            setKitDetails(response.data);
        } catch (error) {
            console.error("Error loading kit:", error);
            toast.error("Erreur lors du chargement du kit");
            setKitDetails(null);
        } finally {
            setLoadingKit(false);
        }
    };

    const handleAddKit = () => {
        if (!kitDetails || !kitDetails.expanded_items) return;
        
        const itemsToAdd = kitDetails.expanded_items.map(item => ({
            description: item.name,
            quantity: item.quantity,
            unit_price: item.unit_price,
            vat_rate: 20,
            unit: item.unit || "unité"
        }));
        
        onAddMultipleItems(itemsToAdd);
        setShowKitDialog(false);
        setSelectedKit(null);
        setKitDetails(null);
        toast.success(`Kit "${kitDetails.name}" ajouté (${itemsToAdd.length} articles)`);
    };

    if (loading) {
        return (
            <Card className="border-orange-200 bg-orange-50/50">
                <CardContent className="py-8 flex justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-orange-600" />
                </CardContent>
            </Card>
        );
    }

    const selectedCategoryData = categories.find(c => c.id === selectedCategory);

    return (
        <>
            <Card className="border-orange-200 bg-orange-50/50">
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Package className="w-5 h-5 text-orange-600" />
                            Ajouter un article prédéfini
                        </CardTitle>
                        {kits.length > 0 && (
                            <Button 
                                type="button" 
                                variant="outline" 
                                size="sm"
                                onClick={() => setShowKitDialog(true)}
                                className="border-orange-300 text-orange-700 hover:bg-orange-100"
                                data-testid="add-kit-btn"
                            >
                                <Sparkles className="w-4 h-4 mr-2" />
                                Ajouter un kit
                            </Button>
                        )}
                    </div>
                    <CardDescription>
                        Sélectionnez une catégorie puis un article pour l'ajouter rapidement
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {/* Breadcrumb */}
                    {selectedCategoryData && (
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                            <Layers className="w-4 h-4" />
                            <span>{selectedCategoryData.name}</span>
                            <Badge variant="secondary" className="text-xs">
                                {items.length} articles
                            </Badge>
                        </div>
                    )}
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {/* Category Select */}
                        <div className="space-y-1">
                            <Label className="text-xs">Catégorie</Label>
                            <Select 
                                value={selectedCategory} 
                                onValueChange={handleCategoryChange}
                            >
                                <SelectTrigger data-testid="category-select">
                                    <SelectValue placeholder="Choisir une catégorie" />
                                </SelectTrigger>
                                <SelectContent>
                                    {categories.map(cat => (
                                        <SelectItem key={cat.id} value={cat.id}>
                                            {cat.name} ({cat.items?.length || 0})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        
                        {/* Item Select */}
                        <div className="space-y-1">
                            <Label className="text-xs">Article</Label>
                            <Select 
                                value={selectedItem} 
                                onValueChange={setSelectedItem}
                                disabled={!selectedCategory}
                            >
                                <SelectTrigger data-testid="item-select">
                                    <SelectValue placeholder={selectedCategory ? "Choisir un article" : "Sélectionnez d'abord une catégorie"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {items.map(item => (
                                        <SelectItem key={item.id} value={item.id}>
                                            {item.name} ({item.smart_price || item.default_price}€/{item.unit})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        
                        {/* Add Button */}
                        <div className="flex items-end">
                            <Button 
                                type="button" 
                                onClick={handleAddItem}
                                className="bg-orange-600 hover:bg-orange-700 w-full"
                                disabled={!selectedItem}
                                data-testid="add-item-btn"
                            >
                                <Plus className="w-4 h-4 mr-2" />
                                Ajouter
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Kit Selection Dialog */}
            <Dialog open={showKitDialog} onOpenChange={setShowKitDialog}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-orange-600" />
                            Ajouter un kit prédéfini
                        </DialogTitle>
                        <DialogDescription>
                            Les kits regroupent plusieurs articles fréquemment utilisés ensemble
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
                        {/* Kit List */}
                        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                            {kits.map(kit => (
                                <div
                                    key={kit.id}
                                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                                        selectedKit === kit.id 
                                            ? 'border-orange-500 bg-orange-50' 
                                            : 'border-gray-200 hover:border-orange-300 hover:bg-gray-50'
                                    }`}
                                    onClick={() => handleSelectKit(kit.id)}
                                    data-testid={`kit-${kit.id}`}
                                >
                                    <div className="font-medium text-sm">{kit.name}</div>
                                    <div className="text-xs text-gray-500 mt-1">{kit.description}</div>
                                    <Badge variant="secondary" className="mt-2 text-xs">
                                        {kit.business_type === 'general' ? 'Général' : kit.business_type}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                        
                        {/* Kit Details */}
                        <div className="border rounded-lg p-4 bg-gray-50">
                            {loadingKit ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="w-6 h-6 animate-spin text-orange-600" />
                                </div>
                            ) : kitDetails ? (
                                <div className="space-y-3">
                                    <div className="font-semibold">{kitDetails.name}</div>
                                    <div className="text-sm text-gray-600">{kitDetails.description}</div>
                                    
                                    <div className="border-t pt-3">
                                        <div className="text-xs font-medium text-gray-500 mb-2">
                                            Articles inclus ({kitDetails.expanded_items?.length || 0})
                                        </div>
                                        <div className="space-y-1 max-h-[200px] overflow-y-auto">
                                            {kitDetails.expanded_items?.map((item, idx) => (
                                                <div key={idx} className="text-xs flex justify-between">
                                                    <span>{item.quantity}x {item.name}</span>
                                                    <span className="text-gray-500">{item.total.toFixed(2)}€</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    
                                    <div className="border-t pt-3 flex justify-between font-medium">
                                        <span>Total HT</span>
                                        <span className="text-orange-600">{kitDetails.total_ht?.toFixed(2)}€</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-sm text-gray-500 text-center py-8">
                                    Sélectionnez un kit pour voir les détails
                                </div>
                            )}
                        </div>
                    </div>
                    
                    <DialogFooter>
                        <Button 
                            type="button" 
                            variant="outline" 
                            onClick={() => setShowKitDialog(false)}
                        >
                            Annuler
                        </Button>
                        <Button 
                            type="button" 
                            onClick={handleAddKit}
                            disabled={!kitDetails}
                            className="bg-orange-600 hover:bg-orange-700"
                            data-testid="confirm-add-kit-btn"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            Ajouter le kit
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
