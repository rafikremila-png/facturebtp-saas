import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getClient, createClient, updateClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Save, User, Mail, Phone, MapPin } from "lucide-react";
import { toast } from "sonner";

export default function ClientFormPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const isEdit = !!id;
    
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        email: "",
        phone: "",
        address: ""
    });

    useEffect(() => {
        if (isEdit) {
            loadClient();
        }
    }, [id]);

    const loadClient = async () => {
        setLoading(true);
        try {
            const response = await getClient(id);
            setFormData({
                name: response.data.name || "",
                email: response.data.email || "",
                phone: response.data.phone || "",
                address: response.data.address || ""
            });
        } catch (error) {
            toast.error("Erreur lors du chargement du client");
            navigate("/clients");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.name.trim()) {
            toast.error("Le nom est obligatoire");
            return;
        }

        setSaving(true);
        try {
            if (isEdit) {
                await updateClient(id, formData);
                toast.success("Client mis à jour avec succès");
            } else {
                await createClient(formData);
                toast.success("Client créé avec succès");
            }
            navigate("/clients");
        } catch (error) {
            toast.error("Erreur lors de l'enregistrement du client");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (field) => (e) => {
        setFormData(prev => ({ ...prev, [field]: e.target.value }));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6" data-testid="client-form-page">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button 
                    variant="ghost" 
                    onClick={() => navigate("/clients")}
                    data-testid="back-btn"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Retour
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed'] text-2xl">
                        {isEdit ? "Modifier le client" : "Nouveau client"}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <Label htmlFor="name">Nom *</Label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    id="name"
                                    placeholder="Nom de l'entreprise ou du particulier"
                                    value={formData.name}
                                    onChange={handleChange("name")}
                                    className="pl-10"
                                    required
                                    data-testid="name-input"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="client@exemple.fr"
                                    value={formData.email}
                                    onChange={handleChange("email")}
                                    className="pl-10"
                                    data-testid="email-input"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="phone">Téléphone</Label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    id="phone"
                                    type="tel"
                                    placeholder="01 23 45 67 89"
                                    value={formData.phone}
                                    onChange={handleChange("phone")}
                                    className="pl-10"
                                    data-testid="phone-input"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="address">Adresse</Label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                                <Input
                                    id="address"
                                    placeholder="123 Rue Exemple, 75001 Paris"
                                    value={formData.address}
                                    onChange={handleChange("address")}
                                    className="pl-10"
                                    data-testid="address-input"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 pt-4">
                            <Button 
                                type="button" 
                                variant="outline"
                                onClick={() => navigate("/clients")}
                            >
                                Annuler
                            </Button>
                            <Button 
                                type="submit"
                                className="bg-orange-600 hover:bg-orange-700"
                                disabled={saving}
                                data-testid="submit-btn"
                            >
                                {saving ? (
                                    <span className="flex items-center gap-2">
                                        <span className="spinner w-4 h-4"></span>
                                        Enregistrement...
                                    </span>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4 mr-2" />
                                        {isEdit ? "Mettre à jour" : "Créer le client"}
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
