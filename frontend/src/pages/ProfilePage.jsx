import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { User, Mail, Phone, Building, MapPin, Calendar, Clock, Shield, Save, CheckCircle } from "lucide-react";
import { toast } from "sonner";

const ROLE_LABELS = {
    super_admin: { label: "Super Admin", color: "bg-purple-100 text-purple-800" },
    admin: { label: "Administrateur", color: "bg-blue-100 text-blue-800" },
    user: { label: "Utilisateur", color: "bg-slate-100 text-slate-800" }
};

export default function ProfilePage() {
    const { user: authUser } = useAuth();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        phone: "",
        company_name: "",
        address: ""
    });

    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            const response = await api.get("/auth/profile");
            setProfile(response.data);
            setFormData({
                name: response.data.name || "",
                phone: response.data.phone || "",
                company_name: response.data.company_name || "",
                address: response.data.address || ""
            });
        } catch (error) {
            toast.error("Erreur lors du chargement du profil");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        
        try {
            const response = await api.put("/auth/profile", formData);
            setProfile(response.data);
            toast.success("Profil mis à jour avec succès");
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la mise à jour");
        } finally {
            setSaving(false);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "Jamais";
        return new Date(dateStr).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    const roleInfo = ROLE_LABELS[profile?.role] || ROLE_LABELS.user;

    return (
        <div className="space-y-6 max-w-3xl" data-testid="profile-page">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
                    <User className="w-8 h-8 text-orange-600" />
                    Mon profil
                </h1>
                <p className="text-slate-500 mt-1">Gérez vos informations personnelles</p>
            </div>

            {/* Profile Overview Card */}
            <Card>
                <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center">
                                <span className="text-2xl font-bold text-orange-600">
                                    {profile?.name?.charAt(0)?.toUpperCase() || "U"}
                                </span>
                            </div>
                            <div>
                                <CardTitle className="font-['Barlow_Condensed'] text-xl">{profile?.name}</CardTitle>
                                <p className="text-slate-500">{profile?.email}</p>
                                <div className="flex items-center gap-2 mt-2">
                                    <Badge className={roleInfo.color}>{roleInfo.label}</Badge>
                                    {profile?.email_verified && (
                                        <Badge className="bg-green-100 text-green-800">
                                            <CheckCircle className="w-3 h-3 mr-1" />
                                            Email vérifié
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex items-center gap-2 text-slate-500">
                            <Calendar className="w-4 h-4" />
                            <span>Inscrit le {formatDate(profile?.created_at)}</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500">
                            <Clock className="w-4 h-4" />
                            <span>Dernière connexion: {formatDate(profile?.last_login)}</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Edit Profile Form */}
            <Card>
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed']">Modifier mes informations</CardTitle>
                    <CardDescription>Mettez à jour vos coordonnées et informations professionnelles</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Nom complet</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="pl-10"
                                        data-testid="profile-name"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="phone">Téléphone</Label>
                                <div className="relative">
                                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                    <Input
                                        id="phone"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        className="pl-10"
                                        data-testid="profile-phone"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="company_name">Nom de l'entreprise</Label>
                            <div className="relative">
                                <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    id="company_name"
                                    value={formData.company_name}
                                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                                    className="pl-10"
                                    data-testid="profile-company"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="address">Adresse</Label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    id="address"
                                    value={formData.address}
                                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                    className="pl-10"
                                    data-testid="profile-address"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Email</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    value={profile?.email}
                                    disabled
                                    className="pl-10 bg-slate-50"
                                />
                            </div>
                            <p className="text-xs text-slate-500">L'email ne peut pas être modifié</p>
                        </div>

                        <div className="flex justify-end pt-4">
                            <Button
                                type="submit"
                                disabled={saving}
                                className="bg-orange-600 hover:bg-orange-700"
                                data-testid="save-profile-btn"
                            >
                                {saving ? (
                                    <>
                                        <span className="spinner w-4 h-4 mr-2"></span>
                                        Enregistrement...
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4 mr-2" />
                                        Enregistrer les modifications
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
