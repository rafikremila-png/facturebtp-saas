import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getClients, createInvoice, getSettings, getPredefinedCategories } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Save, Plus, Trash2, Package } from "lucide-react";
import { toast } from "sonner";

function InvoiceFormPage() {
    var navigate = useNavigate();
    var [loading, setLoading] = useState(true);
    var [saving, setSaving] = useState(false);
    var [clients, setClients] = useState([]);
    var [vatRates, setVatRates] = useState([20, 10, 5.5, 2.1]);
    var [categories, setCategories] = useState([]);
    var [selectedCategory, setSelectedCategory] = useState("");
    var [selectedItem, setSelectedItem] = useState("");
    var [clientId, setClientId] = useState("");
    var [paymentMethod, setPaymentMethod] = useState("virement");
    var [notes, setNotes] = useState("");
    var [items, setItems] = useState([{ description: "", quantity: 1, unit_price: 0, vat_rate: 20, unit: "" }]);

    useEffect(function() {
        Promise.all([getClients(), getSettings(), getPredefinedCategories()]).then(function(results) {
            setClients(results[0].data);
            if (results[1].data.default_vat_rates) setVatRates(results[1].data.default_vat_rates);
            setCategories(results[2].data);
            setLoading(false);
        }).catch(function() { setLoading(false); });
    }, []);

    function handleSubmit(e) {
        e.preventDefault();
        if (!clientId) { toast.error("Sélectionnez un client"); return; }
        var validItems = items.filter(function(i) { return i.description.trim(); });
        if (!validItems.length) { toast.error("Ajoutez une ligne"); return; }
        setSaving(true);
        var payload = {
            client_id: clientId,
            payment_method: paymentMethod,
            notes: notes,
            items: validItems.map(function(item) {
                return {
                    description: item.unit ? item.description + " (" + item.unit + ")" : item.description,
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    vat_rate: item.vat_rate
                };
            })
        };
        createInvoice(payload)
            .then(function() { toast.success("Créée"); navigate("/factures"); })
            .catch(function() { toast.error("Erreur"); })
            .finally(function() { setSaving(false); });
    }

    function addItem() { setItems([...items, { description: "", quantity: 1, unit_price: 0, vat_rate: vatRates[0], unit: "" }]); }
    
    function addPredefinedItem() {
        if (!selectedCategory || !selectedItem) { toast.error("Sélectionnez une catégorie et un article"); return; }
        var category = categories.find(function(c) { return c.name === selectedCategory; });
        if (!category) return;
        var item = category.items.find(function(i) { return i.id === selectedItem; });
        if (!item) return;
        setItems([...items, { description: item.description, quantity: 1, unit_price: item.default_price, vat_rate: item.default_vat_rate, unit: item.unit }]);
        setSelectedItem("");
        toast.success("Article ajouté");
    }
    
    function removeItem(i) { if (items.length > 1) setItems(items.filter(function(_, idx) { return idx !== i; })); }
    function updateItem(i, f, v) { var n = [...items]; n[i] = { ...n[i], [f]: v }; setItems(n); }

    var totals = items.reduce(function(a, it) {
        var ht = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0);
        return { ht: a.ht + ht, vat: a.vat + ht * (parseFloat(it.vat_rate) || 0) / 100 };
    }, { ht: 0, vat: 0 });

    var selectedCategoryItems = [];
    var cat = categories.find(function(c) { return c.name === selectedCategory; });
    if (cat) selectedCategoryItems = cat.items;

    if (loading) return <div className="flex justify-center py-20"><div className="spinner"></div></div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-form-page">
            <Button variant="ghost" onClick={function() { navigate("/factures"); }} data-testid="back-btn"><ArrowLeft className="w-4 h-4 mr-2" />Retour</Button>
            <form onSubmit={handleSubmit} className="space-y-6">
                <Card>
                    <CardHeader><CardTitle>Nouvelle facture</CardTitle></CardHeader>
                    <CardContent className="grid grid-cols-2 gap-4">
                        <div><Label>Client *</Label>
                            <Select value={clientId} onValueChange={setClientId}><SelectTrigger data-testid="client-select"><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                                <SelectContent>{clients.map(function(c) { return <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>; })}</SelectContent></Select></div>
                        <div><Label>Mode de paiement</Label>
                            <Select value={paymentMethod} onValueChange={setPaymentMethod}><SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent><SelectItem value="virement">Virement</SelectItem><SelectItem value="cheque">Chèque</SelectItem><SelectItem value="especes">Espèces</SelectItem></SelectContent></Select></div>
                    </CardContent>
                </Card>

                <Card className="border-orange-200 bg-orange-50/50">
                    <CardHeader className="pb-3"><CardTitle className="text-lg flex items-center gap-2"><Package className="w-5 h-5 text-orange-600" />Ajouter un article prédéfini</CardTitle></CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div><Label className="text-xs">Catégorie</Label>
                                <Select value={selectedCategory} onValueChange={function(v) { setSelectedCategory(v); setSelectedItem(""); }}>
                                    <SelectTrigger><SelectValue placeholder={!selectedCategory ? "Choisir" : undefined} /></SelectTrigger>
                                    <SelectContent>{categories.map(function(c) { return <SelectItem key={c.name} value={c.name}>{c.name}</SelectItem>; })}</SelectContent></Select></div>
                            <div><Label className="text-xs">Article</Label>
                                <Select value={selectedItem} onValueChange={setSelectedItem} disabled={!selectedCategory}>
                                    <SelectTrigger><SelectValue placeholder={!selectedItem ? "Choisir" : undefined} /></SelectTrigger>
                                    <SelectContent>{selectedCategoryItems.map(function(it) { return <SelectItem key={it.id} value={it.id}>{it.description} ({it.default_price}€/{it.unit})</SelectItem>; })}</SelectContent></Select></div>
                            <div className="flex items-end"><Button type="button" onClick={addPredefinedItem} className="bg-orange-600 w-full" disabled={!selectedCategory || !selectedItem}><Plus className="w-4 h-4 mr-2" />Ajouter</Button></div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row justify-between"><CardTitle>Lignes</CardTitle><Button type="button" variant="outline" size="sm" onClick={addItem} data-testid="add-item-btn"><Plus className="w-4 h-4 mr-2" />Ligne manuelle</Button></CardHeader>
                    <CardContent className="space-y-3">
                        {items.map(function(it, i) { return (
                            <div key={i} className="grid grid-cols-12 gap-2 p-3 bg-slate-50 rounded" data-testid={"item-row-" + i}>
                                <Input className="col-span-4" placeholder="Description" value={it.description} onChange={function(e) { updateItem(i, "description", e.target.value); }} />
                                <Input className="col-span-1" placeholder="Unité" value={it.unit || ""} onChange={function(e) { updateItem(i, "unit", e.target.value); }} />
                                <Input className="col-span-2" type="number" value={it.quantity} onChange={function(e) { updateItem(i, "quantity", parseFloat(e.target.value) || 0); }} />
                                <Input className="col-span-2" type="number" value={it.unit_price} onChange={function(e) { updateItem(i, "unit_price", parseFloat(e.target.value) || 0); }} />
                                <Select value={String(it.vat_rate)} onValueChange={function(v) { updateItem(i, "vat_rate", parseFloat(v)); }}><SelectTrigger className="col-span-1"><SelectValue /></SelectTrigger>
                                    <SelectContent>{vatRates.map(function(r) { return <SelectItem key={r} value={String(r)}>{r}%</SelectItem>; })}</SelectContent></Select>
                                <Button type="button" variant="ghost" size="icon" onClick={function() { removeItem(i); }} className="col-span-1"><Trash2 className="w-4 h-4" /></Button>
                                <span className="col-span-1 text-right">{((parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0)).toFixed(2)}€</span>
                            </div>
                        ); })}
                        <div className="text-right pt-4 border-t"><p>HT: {totals.ht.toFixed(2)} €</p><p>TVA: {totals.vat.toFixed(2)} €</p><p className="text-xl font-bold text-orange-600">TTC: {(totals.ht + totals.vat).toFixed(2)} €</p></div>
                    </CardContent>
                </Card>
                <Card><CardHeader><CardTitle>Notes</CardTitle></CardHeader><CardContent><Textarea value={notes} onChange={function(e) { setNotes(e.target.value); }} rows={3} /></CardContent></Card>
                <div className="flex gap-3"><Button type="button" variant="outline" onClick={function() { navigate("/factures"); }}>Annuler</Button><Button type="submit" className="bg-orange-600" disabled={saving} data-testid="submit-btn"><Save className="w-4 h-4 mr-2" />{saving ? "..." : "Créer"}</Button></div>
            </form>
        </div>
    );
}

export default InvoiceFormPage;
