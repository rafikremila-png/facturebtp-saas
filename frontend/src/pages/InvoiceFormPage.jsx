import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getClients, createInvoice, getSettings } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Save, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import UpgradeModal from "@/components/UpgradeModal";
import ServiceItemSelector from "@/components/ServiceItemSelector";

function InvoiceFormPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [clients, setClients] = useState([]);
    const [vatRates, setVatRates] = useState([20, 10, 5.5, 2.1]);
    const [clientId, setClientId] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("virement");
    const [notes, setNotes] = useState("");
    const [items, setItems] = useState([{ description: "", quantity: 1, unit_price: 0, vat_rate: 20, unit: "" }]);
    
    // Upgrade modal state
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);
    const [upgradeModalConfig, setUpgradeModalConfig] = useState({
        title: "Mise à niveau requise",
        message: "",
        type: "limit"
    });

    useEffect(() => {
        Promise.all([getClients(), getSettings()]).then((results) => {
            setClients(results[0].data);
            if (results[1].data.default_vat_rates) {
                setVatRates(results[1].data.default_vat_rates);
            }
            setLoading(false);
        }).catch(() => { setLoading(false); });
    }, []);

    function handleSubmit(e) {
        e.preventDefault();
        if (!clientId) { toast.error("Sélectionnez un client"); return; }
        const validItems = items.filter((i) => i.description.trim());
        if (!validItems.length) { toast.error("Ajoutez au moins une ligne"); return; }
        setSaving(true);
        const payload = {
            client_id: clientId,
            payment_method: paymentMethod,
            notes: notes,
            items: validItems.map((item) => ({
                description: item.unit ? `${item.description} (${item.unit})` : item.description,
                quantity: item.quantity,
                unit_price: item.unit_price,
                vat_rate: item.vat_rate
            }))
        };
        createInvoice(payload)
            .then(() => { toast.success("Facture créée"); navigate("/factures"); })
            .catch((error) => { 
                if (error.response && error.response.status === 403) {
                    const errorMessage = error.response.data?.detail || "Limite atteinte";
                    const isExpired = errorMessage.toLowerCase().includes("expir");
                    setUpgradeModalConfig({
                        title: isExpired ? "Période d'essai expirée" : "Limite atteinte",
                        message: errorMessage,
                        type: isExpired ? "expired" : "limit"
                    });
                    setShowUpgradeModal(true);
                } else {
                    toast.error("Erreur lors de la création de la facture"); 
                }
            })
            .finally(() => { setSaving(false); });
    }

    function addItem() { 
        setItems([...items, { description: "", quantity: 1, unit_price: 0, vat_rate: vatRates[0], unit: "" }]); 
    }
    
    function handleAddPredefinedItem(item) {
        setItems([...items, item]);
    }
    
    function handleAddMultipleItems(newItems) {
        setItems([...items, ...newItems]);
    }
    
    function removeItem(i) { 
        if (items.length > 1) setItems(items.filter((_, idx) => idx !== i)); 
    }
    
    function updateItem(i, field, value) { 
        const newItems = [...items]; 
        newItems[i] = { ...newItems[i], [field]: value }; 
        setItems(newItems); 
    }

    const totals = items.reduce((acc, it) => {
        const ht = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0);
        return { ht: acc.ht + ht, vat: acc.vat + ht * (parseFloat(it.vat_rate) || 0) / 100 };
    }, { ht: 0, vat: 0 });

    if (loading) return <div className="flex justify-center py-20"><div className="spinner"></div></div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-form-page">
            <Button variant="ghost" onClick={() => navigate("/factures")} data-testid="back-btn">
                <ArrowLeft className="w-4 h-4 mr-2" />Retour
            </Button>
            
            <form onSubmit={handleSubmit} className="space-y-6">
                <Card>
                    <CardHeader><CardTitle>Nouvelle facture</CardTitle></CardHeader>
                    <CardContent className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>Client *</Label>
                            <Select value={clientId} onValueChange={setClientId}>
                                <SelectTrigger data-testid="client-select">
                                    <SelectValue placeholder="Sélectionner" />
                                </SelectTrigger>
                                <SelectContent>
                                    {clients.map((c) => (
                                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>Mode de paiement</Label>
                            <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="virement">Virement</SelectItem>
                                    <SelectItem value="cheque">Chèque</SelectItem>
                                    <SelectItem value="especes">Espèces</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Simplified Service Item Selector */}
                <ServiceItemSelector 
                    onAddItem={handleAddPredefinedItem}
                    onAddMultipleItems={handleAddMultipleItems}
                />

                <Card>
                    <CardHeader className="flex flex-row justify-between items-center">
                        <CardTitle>Lignes de la facture</CardTitle>
                        <Button type="button" variant="outline" size="sm" onClick={addItem} data-testid="add-item-btn">
                            <Plus className="w-4 h-4 mr-2" />Ligne manuelle
                        </Button>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {items.map((it, i) => (
                            <div key={i} className="grid grid-cols-12 gap-2 p-3 bg-slate-50 rounded" data-testid={`item-row-${i}`}>
                                <Input 
                                    className="col-span-4" 
                                    placeholder="Description" 
                                    value={it.description} 
                                    onChange={(e) => updateItem(i, "description", e.target.value)} 
                                />
                                <Input 
                                    className="col-span-1" 
                                    placeholder="Unité" 
                                    value={it.unit || ""} 
                                    onChange={(e) => updateItem(i, "unit", e.target.value)} 
                                />
                                <Input 
                                    className="col-span-2" 
                                    type="number" 
                                    value={it.quantity} 
                                    onChange={(e) => updateItem(i, "quantity", parseFloat(e.target.value) || 0)} 
                                />
                                <Input 
                                    className="col-span-2" 
                                    type="number" 
                                    value={it.unit_price} 
                                    onChange={(e) => updateItem(i, "unit_price", parseFloat(e.target.value) || 0)} 
                                />
                                <Select 
                                    value={String(it.vat_rate)} 
                                    onValueChange={(v) => updateItem(i, "vat_rate", parseFloat(v))}
                                >
                                    <SelectTrigger className="col-span-1"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {vatRates.map((r) => (
                                            <SelectItem key={r} value={String(r)}>{r}%</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Button 
                                    type="button" 
                                    variant="ghost" 
                                    size="icon" 
                                    onClick={() => removeItem(i)} 
                                    className="col-span-1"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                                <span className="col-span-1 text-right text-sm pt-2">
                                    {((parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0)).toFixed(2)}€
                                </span>
                            </div>
                        ))}
                        <div className="text-right pt-4 border-t">
                            <p>HT: {totals.ht.toFixed(2)} €</p>
                            <p>TVA: {totals.vat.toFixed(2)} €</p>
                            <p className="text-xl font-bold text-orange-600">TTC: {(totals.ht + totals.vat).toFixed(2)} €</p>
                        </div>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardHeader><CardTitle>Notes</CardTitle></CardHeader>
                    <CardContent>
                        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
                    </CardContent>
                </Card>
                
                <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => navigate("/factures")}>
                        Annuler
                    </Button>
                    <Button type="submit" className="bg-orange-600 hover:bg-orange-700" disabled={saving} data-testid="submit-btn">
                        <Save className="w-4 h-4 mr-2" />{saving ? "Création..." : "Créer la facture"}
                    </Button>
                </div>
            </form>
            
            {/* Upgrade Modal */}
            <UpgradeModal 
                open={showUpgradeModal} 
                onOpenChange={setShowUpgradeModal}
                title={upgradeModalConfig.title}
                message={upgradeModalConfig.message}
                type={upgradeModalConfig.type}
            />
        </div>
    );
}

export default InvoiceFormPage;
