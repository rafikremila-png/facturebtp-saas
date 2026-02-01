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

export default function InvoiceFormPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [clients, setClients] = useState([]);
    const [vatRates, setVatRates] = useState([20, 10, 5.5, 2.1]);
    const [clientId, setClientId] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("virement");
    const [notes, setNotes] = useState("");
    const [items, setItems] = useState([
        { description: "", quantity: 1, unit_price: 0, vat_rate: 20 }
    ]);

    useEffect(() => {
        const load = async () => {
            try {
                const [c, s] = await Promise.all([getClients(), getSettings()]);
                setClients(c.data);
                if (s.data.default_vat_rates && s.data.default_vat_rates.length > 0) {
                    setVatRates(s.data.default_vat_rates);
                }
            } catch (e) {
                console.error(e);
            }
            setLoading(false);
        };
        load();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!clientId) {
            toast.error("Sélectionnez un client");
            return;
        }
        const validItems = items.filter(i => i.description.trim() !== "");
        if (validItems.length === 0) {
            toast.error("Ajoutez au moins une ligne");
            return;
        }
        setSaving(true);
        try {
            await createInvoice({
                client_id: clientId,
                payment_method: paymentMethod,
                notes: notes,
                items: validItems
            });
            toast.success("Facture créée");
            navigate("/factures");
        } catch (err) {
            toast.error("Erreur lors de la création");
        }
        setSaving(false);
    };

    const addItem = () => {
        setItems([...items, { description: "", quantity: 1, unit_price: 0, vat_rate: vatRates[0] }]);
    };

    const removeItem = (index) => {
        if (items.length > 1) {
            setItems(items.filter((_, i) => i !== index));
        }
    };

    const updateItem = (index, field, value) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const calculateTotals = () => {
        let ht = 0;
        let vat = 0;
        items.forEach(item => {
            const lineHT = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
            const lineVAT = lineHT * ((parseFloat(item.vat_rate) || 0) / 100);
            ht += lineHT;
            vat += lineVAT;
        });
        return { ht, vat, ttc: ht + vat };
    };

    const totals = calculateTotals();

    if (loading) {
        return (
            <div className="flex justify-center py-20">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6" data-testid="invoice-form-page">
            <Button variant="ghost" onClick={() => navigate("/factures")} data-testid="back-btn">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Retour
            </Button>

            <form onSubmit={handleSubmit} className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed'] text-2xl">
                            Nouvelle facture
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Client *</Label>
                            <Select value={clientId} onValueChange={setClientId}>
                                <SelectTrigger data-testid="client-select">
                                    <SelectValue placeholder="Sélectionner un client" />
                                </SelectTrigger>
                                <SelectContent>
                                    {clients.map(c => (
                                        <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Mode de paiement</Label>
                            <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="virement">Virement bancaire</SelectItem>
                                    <SelectItem value="cheque">Chèque</SelectItem>
                                    <SelectItem value="especes">Espèces</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="font-['Barlow_Condensed']">Lignes de la facture</CardTitle>
                        <Button type="button" variant="outline" size="sm" onClick={addItem} data-testid="add-item-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Ajouter
                        </Button>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {items.map((item, index) => (
                            <div key={index} className="grid grid-cols-12 gap-2 items-end p-3 bg-slate-50 rounded-lg" data-testid={`item-row-${index}`}>
                                <div className="col-span-12 md:col-span-4">
                                    <Label className="text-xs">Description</Label>
                                    <Input
                                        placeholder="Description"
                                        value={item.description}
                                        onChange={(e) => updateItem(index, "description", e.target.value)}
                                    />
                                </div>
                                <div className="col-span-4 md:col-span-2">
                                    <Label className="text-xs">Quantité</Label>
                                    <Input
                                        type="number"
                                        value={item.quantity}
                                        onChange={(e) => updateItem(index, "quantity", parseFloat(e.target.value) || 0)}
                                    />
                                </div>
                                <div className="col-span-4 md:col-span-2">
                                    <Label className="text-xs">Prix HT</Label>
                                    <Input
                                        type="number"
                                        value={item.unit_price}
                                        onChange={(e) => updateItem(index, "unit_price", parseFloat(e.target.value) || 0)}
                                    />
                                </div>
                                <div className="col-span-3 md:col-span-2">
                                    <Label className="text-xs">TVA</Label>
                                    <Select value={String(item.vat_rate)} onValueChange={(v) => updateItem(index, "vat_rate", parseFloat(v))}>
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {vatRates.map(r => (
                                                <SelectItem key={r} value={String(r)}>{r}%</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="col-span-1">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeItem(index)}
                                        disabled={items.length === 1}
                                        className="hover:bg-red-50 hover:text-red-600"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                                <div className="col-span-12 md:col-span-1 text-right font-medium">
                                    {((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)).toFixed(2)} €
                                </div>
                            </div>
                        ))}

                        <div className="border-t pt-4 space-y-2 text-right">
                            <p className="text-sm">Total HT: <span className="font-medium">{totals.ht.toFixed(2)} €</span></p>
                            <p className="text-sm">Total TVA: <span className="font-medium">{totals.vat.toFixed(2)} €</span></p>
                            <p className="text-lg font-bold">Total TTC: <span className="text-orange-600">{totals.ttc.toFixed(2)} €</span></p>
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
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            rows={3}
                        />
                    </CardContent>
                </Card>

                <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => navigate("/factures")}>
                        Annuler
                    </Button>
                    <Button type="submit" className="bg-orange-600 hover:bg-orange-700" disabled={saving} data-testid="submit-btn">
                        <Save className="w-4 h-4 mr-2" />
                        {saving ? "Création..." : "Créer la facture"}
                    </Button>
                </div>
            </form>
        </div>
    );
}
