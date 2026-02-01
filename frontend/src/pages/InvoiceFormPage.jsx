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

const paymentMethods = [
    { value: "virement", label: "Virement bancaire" },
    { value: "cheque", label: "Chèque" },
    { value: "especes", label: "Espèces" }
];

export default function InvoiceFormPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [clients, setClients] = useState([]);
    const [vatRates, setVatRates] = useState([20.0, 10.0, 5.5, 2.1]);
    const [formData, setFormData] = useState({
        client_id: "",
        payment_method: "virement",
        notes: "",
        items: [{ description: "", quantity: 1, unit_price: 0, vat_rate: 20.0 }]
    });

    useEffect(() => {
        Promise.all([getClients(), getSettings()]).then(([c, s]) => {
            setClients(c.data);
            if (s.data.default_vat_rates?.length) setVatRates(s.data.default_vat_rates);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.client_id) return toast.error("Sélectionnez un client");
        const validItems = formData.items.filter(i => i.description.trim());
        if (!validItems.length) return toast.error("Ajoutez une ligne");
        setSaving(true);
        createInvoice({ ...formData, items: validItems })
            .then(() => { toast.success("Créée"); navigate("/factures"); })
            .catch(() => toast.error("Erreur"))
            .finally(() => setSaving(false));
    };

    const addItem = () => setFormData(p => ({ ...p, items: [...p.items, { description: "", quantity: 1, unit_price: 0, vat_rate: vatRates[0] }] }));
    const removeItem = (i) => formData.items.length > 1 && setFormData(p => ({ ...p, items: p.items.filter((_, idx) => idx !== i) }));
    const updateItem = (i, f, v) => setFormData(p => ({ ...p, items: p.items.map((it, idx) => idx === i ? { ...it, [f]: v } : it) }));

    const totals = formData.items.reduce((acc, it) => {
        const ht = (parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0);
        const vat = ht * ((parseFloat(it.vat_rate) || 0) / 100);
        return { ht: acc.ht + ht, vat: acc.vat + vat };
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
                            <Select value={formData.client_id} onValueChange={v => setFormData(p => ({ ...p, client_id: v }))}>
                                <SelectTrigger data-testid="client-select"><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                                <SelectContent>{clients.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>Mode de paiement</Label>
                            <Select value={formData.payment_method} onValueChange={v => setFormData(p => ({ ...p, payment_method: v }))}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>{paymentMethods.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row justify-between">
                        <CardTitle>Lignes</CardTitle>
                        <Button type="button" variant="outline" size="sm" onClick={addItem} data-testid="add-item-btn">
                            <Plus className="w-4 h-4 mr-2" />Ajouter
                        </Button>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {formData.items.map((it, i) => (
                            <div key={i} className="grid grid-cols-12 gap-2 p-3 bg-slate-50 rounded" data-testid={`item-row-${i}`}>
                                <Input className="col-span-4" placeholder="Description" value={it.description} onChange={e => updateItem(i, "description", e.target.value)} />
                                <Input className="col-span-2" type="number" value={it.quantity} onChange={e => updateItem(i, "quantity", parseFloat(e.target.value) || 0)} />
                                <Input className="col-span-2" type="number" value={it.unit_price} onChange={e => updateItem(i, "unit_price", parseFloat(e.target.value) || 0)} />
                                <Select value={String(it.vat_rate)} onValueChange={v => updateItem(i, "vat_rate", parseFloat(v))}>
                                    <SelectTrigger className="col-span-2"><SelectValue /></SelectTrigger>
                                    <SelectContent>{vatRates.map(r => <SelectItem key={r} value={String(r)}>{r}%</SelectItem>)}</SelectContent>
                                </Select>
                                <Button type="button" variant="ghost" size="icon" onClick={() => removeItem(i)} className="col-span-1"><Trash2 className="w-4 h-4" /></Button>
                                <span className="col-span-1 text-right">{((parseFloat(it.quantity) || 0) * (parseFloat(it.unit_price) || 0)).toFixed(2)}€</span>
                            </div>
                        ))}
                        <div className="text-right pt-4 border-t space-y-1">
                            <p>HT: {totals.ht.toFixed(2)} €</p>
                            <p>TVA: {totals.vat.toFixed(2)} €</p>
                            <p className="text-xl font-bold text-orange-600">TTC: {(totals.ht + totals.vat).toFixed(2)} €</p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader><CardTitle>Notes</CardTitle></CardHeader>
                    <CardContent>
                        <Textarea value={formData.notes} onChange={e => setFormData(p => ({ ...p, notes: e.target.value }))} rows={3} />
                    </CardContent>
                </Card>

                <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => navigate("/factures")}>Annuler</Button>
                    <Button type="submit" className="bg-orange-600" disabled={saving} data-testid="submit-btn">
                        <Save className="w-4 h-4 mr-2" />{saving ? "..." : "Créer"}
                    </Button>
                </div>
            </form>
        </div>
    );
}
