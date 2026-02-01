import { useState, useEffect, useRef } from "react";
import { getSettings, updateSettings, uploadLogo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Building2, Save, Upload, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPage() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploadingLogo, setUploadingLogo] = useState(false);
    const fileInputRef = useRef(null);
    
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

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const response = await getSettings();
            if (response.data) {
                setFormData({
                    company_name: response.data.company_name || "",
                    address: response.data.address || "",
                    phone: response.data.phone || "",
                    email: response.data.email || "",
                    siret: response.data.siret || "",
                    vat_number: response.data.vat_number || "",
                    default_vat_rates: response.data.default_vat_rates?.length > 0 
                        ? response.data.default_vat_rates 
                        : [20.0, 10.0, 5.5, 2.1],
                    logo_base64: response.data.logo_base64 || null
                });
            }
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

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-6" data-testid="settings-page">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                    Paramètres
                </h1>
                <p className="text-slate-500 mt-1">Configurez les informations de votre entreprise</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Logo */}
                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed']">Logo de l'entreprise</CardTitle>
                        <CardDescription>
                            Ce logo apparaîtra sur vos devis et factures PDF
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-6">
                            <div className="w-32 h-32 bg-slate-100 rounded-lg flex items-center justify-center overflow-hidden border-2 border-dashed border-slate-300">
                                {formData.logo_base64 ? (
                                    <img 
                                        src={formData.logo_base64} 
                                        alt="Logo" 
                                        className="w-full h-full object-contain"
                                    />
                                ) : (
                                    <Building2 className="w-12 h-12 text-slate-400" />
                                )}
                            </div>
                            <div className="space-y-3">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleLogoUpload}
                                    className="hidden"
                                />
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={uploadingLogo}
                                    data-testid="upload-logo-btn"
                                >
                                    {uploadingLogo ? (
                                        <span className="flex items-center gap-2">
                                            <span className="spinner w-4 h-4"></span>
                                            Téléchargement...
                                        </span>
                                    ) : (
                                        <>
                                            <Upload className="w-4 h-4 mr-2" />
                                            {formData.logo_base64 ? "Changer le logo" : "Télécharger un logo"}
                                        </>
                                    )}
                                </Button>
                                {formData.logo_base64 && (
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        onClick={handleRemoveLogo}
                                        data-testid="remove-logo-btn"
                                    >
                                        <Trash2 className="w-4 h-4 mr-2" />
                                        Supprimer
                                    </Button>
                                )}
                                <p className="text-xs text-slate-500">
                                    PNG, JPG ou GIF. Max 5MB.
                                </p>
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
                            <Input
                                id="company_name"
                                placeholder="Votre Entreprise BTP"
                                value={formData.company_name}
                                onChange={handleChange("company_name")}
                                data-testid="company-name-input"
                            />
                        </div>
                        
                        <div className="space-y-2">
                            <Label htmlFor="address">Adresse</Label>
                            <Input
                                id="address"
                                placeholder="123 Rue du Bâtiment, 75001 Paris"
                                value={formData.address}
                                onChange={handleChange("address")}
                                data-testid="address-input"
                            />
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="phone">Téléphone</Label>
                                <Input
                                    id="phone"
                                    placeholder="01 23 45 67 89"
                                    value={formData.phone}
                                    onChange={handleChange("phone")}
                                    data-testid="phone-input"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="contact@entreprise.fr"
                                    value={formData.email}
                                    onChange={handleChange("email")}
                                    data-testid="email-input"
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Legal Info */}
                <Card>
                    <CardHeader>
                        <CardTitle className="font-['Barlow_Condensed']">Informations légales</CardTitle>
                        <CardDescription>
                            Ces informations sont obligatoires sur vos factures
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="siret">Numéro SIRET</Label>
                                <Input
                                    id="siret"
                                    placeholder="123 456 789 00012"
                                    value={formData.siret}
                                    onChange={handleChange("siret")}
                                    className="font-mono"
                                    data-testid="siret-input"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="vat_number">Numéro de TVA</Label>
                                <Input
                                    id="vat_number"
                                    placeholder="FR12 345678901"
                                    value={formData.vat_number}
                                    onChange={handleChange("vat_number")}
                                    className="font-mono"
                                    data-testid="vat-number-input"
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* VAT Rates */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="font-['Barlow_Condensed']">Taux de TVA par défaut</CardTitle>
                            <CardDescription>
                                Définissez les taux de TVA disponibles dans vos devis et factures
                            </CardDescription>
                        </div>
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addVatRate}
                            data-testid="add-vat-rate-btn"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            Ajouter
                        </Button>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {formData.default_vat_rates.map((rate, index) => (
                                <div key={index} className="flex items-center gap-3">
                                    <Input
                                        type="number"
                                        min="0"
                                        max="100"
                                        step="0.1"
                                        value={rate}
                                        onChange={(e) => updateVatRate(index, e.target.value)}
                                        className="w-32"
                                        data-testid={`vat-rate-${index}`}
                                    />
                                    <span className="text-slate-500">%</span>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeVatRate(index)}
                                        disabled={formData.default_vat_rates.length === 1}
                                        className="hover:bg-red-50 hover:text-red-600"
                                        data-testid={`remove-vat-rate-${index}`}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Save Button */}
                <div className="flex justify-end">
                    <Button 
                        type="submit"
                        className="bg-orange-600 hover:bg-orange-700"
                        disabled={saving}
                        data-testid="save-settings-btn"
                    >
                        {saving ? (
                            <span className="flex items-center gap-2">
                                <span className="spinner w-4 h-4"></span>
                                Enregistrement...
                            </span>
                        ) : (
                            <>
                                <Save className="w-4 h-4 mr-2" />
                                Enregistrer les paramètres
                            </>
                        )}
                    </Button>
                </div>
            </form>
        </div>
    );
}
