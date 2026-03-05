import { useState, useEffect } from "react";
import { useAuth, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER } from "@/context/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Users, Shield, ShieldCheck, User, UserX, UserCheck, Trash2, Crown, Eye, Key, UserCog, Mail, Phone, Building, MapPin, Calendar, Clock, CheckCircle, XCircle, ArrowLeft, Check, X, Image, Globe, CreditCard, FileText } from "lucide-react";
import { toast } from "sonner";
import OTPInput from "@/components/OTPInput";

const ROLE_LABELS = {
    [ROLE_SUPER_ADMIN]: { label: "Super Admin", color: "bg-purple-100 text-purple-800", icon: Crown },
    [ROLE_ADMIN]: { label: "Administrateur", color: "bg-blue-100 text-blue-800", icon: ShieldCheck },
    [ROLE_USER]: { label: "Utilisateur", color: "bg-slate-100 text-slate-800", icon: User }
};

export default function UsersPage() {
    const { user: currentUser, isAdmin, isSuperAdmin } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState(null);
    const [userDetail, setUserDetail] = useState(null);
    const [profileCompletion, setProfileCompletion] = useState(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    
    // OTP dialogs state
    const [otpDialog, setOtpDialog] = useState({ open: false, type: null, userId: null, userName: null });
    const [otpCode, setOtpCode] = useState("");
    const [otpLoading, setOtpLoading] = useState(false);
    const [newPassword, setNewPassword] = useState("");
    const [newRole, setNewRole] = useState("");
    
    // Simple dialogs
    const [deactivateDialogUser, setDeactivateDialogUser] = useState(null);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const response = await api.get("/users");
            setUsers(response.data);
        } catch (error) {
            if (error.response?.status === 403) {
                toast.error("Accès refusé. Droits administrateur requis.");
            } else {
                toast.error("Erreur lors du chargement des utilisateurs");
            }
        } finally {
            setLoading(false);
        }
    };

    const loadUserDetail = async (userId) => {
        setLoadingDetail(true);
        try {
            const [userRes, completionRes] = await Promise.all([
                api.get(`/users/${userId}`),
                api.get(`/users/${userId}/profile-completion`)
            ]);
            setUserDetail(userRes.data);
            setProfileCompletion(completionRes.data);
            setSelectedUser(userId);
        } catch (error) {
            toast.error("Erreur lors du chargement des détails");
        } finally {
            setLoadingDetail(false);
        }
    };

    // Request OTP for action
    const requestOTP = async (userId, userName, otpType) => {
        try {
            await api.post(`/users/${userId}/request-otp?otp_type=${otpType}`);
            toast.success("Code OTP envoyé à votre email");
            setOtpDialog({ open: true, type: otpType, userId, userName });
            setOtpCode("");
            setNewPassword("");
            setNewRole("");
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de l'envoi du code");
        }
    };

    // Perform action with OTP
    const performOTPAction = async () => {
        if (otpCode.length !== 6) {
            toast.error("Entrez le code à 6 chiffres");
            return;
        }

        setOtpLoading(true);
        try {
            const { type, userId } = otpDialog;

            if (type === "promote_admin") {
                await api.patch(`/users/${userId}/role`, { role: newRole, otp_code: otpCode });
                toast.success("Rôle modifié avec succès");
            } else if (type === "delete_user") {
                await api.delete(`/users/${userId}`, { data: { otp_code: otpCode } });
                toast.success("Utilisateur supprimé");
                setSelectedUser(null);
                setUserDetail(null);
            } else if (type === "password_reset") {
                await api.post(`/users/${userId}/reset-password`, {
                    user_id: userId,
                    new_password: newPassword,
                    otp_code: otpCode
                });
                toast.success("Mot de passe réinitialisé");
            } else if (type === "impersonation") {
                const response = await api.post("/admin/impersonate", {
                    target_user_id: userId,
                    otp_code: otpCode
                });
                localStorage.setItem("token", response.data.access_token);
                toast.success("Mode support activé");
                window.location.href = "/";
            }

            setOtpDialog({ open: false, type: null, userId: null, userName: null });
            loadUsers();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Code OTP invalide ou expiré");
        } finally {
            setOtpLoading(false);
        }
    };

    const handleToggleActive = async (userId, isActive) => {
        if (isActive) {
            setDeactivateDialogUser(users.find(u => u.id === userId));
        } else {
            try {
                await api.patch(`/users/${userId}/activate`);
                toast.success("Compte activé");
                loadUsers();
            } catch (error) {
                toast.error(error.response?.data?.detail || "Erreur");
            }
        }
    };

    const confirmDeactivate = async () => {
        if (!deactivateDialogUser) return;
        try {
            await api.patch(`/users/${deactivateDialogUser.id}/deactivate`);
            toast.success("Compte désactivé");
            setDeactivateDialogUser(null);
            loadUsers();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la désactivation");
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "Jamais";
        return new Date(dateStr).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getOTPDialogTitle = () => {
        switch (otpDialog.type) {
            case "promote_admin": return "Modifier le rôle";
            case "delete_user": return "Supprimer l'utilisateur";
            case "password_reset": return "Réinitialiser le mot de passe";
            case "impersonation": return "Mode Support";
            default: return "Vérification";
        }
    };

    if (!isAdmin()) {
        return (
            <div className="flex items-center justify-center h-64">
                <Card className="max-w-md">
                    <CardContent className="pt-6 text-center">
                        <Shield className="w-12 h-12 text-red-500 mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-slate-900 mb-2">Accès refusé</h2>
                        <p className="text-slate-500">Vous n'avez pas les droits nécessaires pour accéder à cette page.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    // User Detail View
    if (selectedUser && userDetail) {
        const roleInfo = ROLE_LABELS[userDetail.role] || ROLE_LABELS[ROLE_USER];
        const RoleIcon = roleInfo.icon;
        const isCurrentUser = userDetail.id === currentUser?.id;
        const canModify = !isCurrentUser && userDetail.role !== ROLE_SUPER_ADMIN;
        // Admin can delete users, but only super_admin can delete other admins
        const canDelete = canModify && (isSuperAdmin() || userDetail.role === ROLE_USER);

        // Helper to get completion color
        const getCompletionColor = (percentage) => {
            if (percentage >= 80) return "text-green-600";
            if (percentage >= 50) return "text-amber-600";
            return "text-red-600";
        };

        const getProgressColor = (percentage) => {
            if (percentage >= 80) return "bg-green-500";
            if (percentage >= 50) return "bg-amber-500";
            return "bg-red-500";
        };

        // Category icons
        const categoryIcons = {
            profil: User,
            entreprise: Building,
            legal: FileText,
            bancaire: CreditCard,
        };

        return (
            <div className="space-y-6" data-testid="user-detail-page">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" onClick={() => { setSelectedUser(null); setUserDetail(null); setProfileCompletion(null); }}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Retour
                    </Button>
                    <h1 className="text-2xl font-bold text-slate-900 font-['Barlow_Condensed']">
                        Fiche utilisateur
                    </h1>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Main Info Card */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <div className="flex items-center gap-4">
                                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${roleInfo.color}`}>
                                    <RoleIcon className="w-8 h-8" />
                                </div>
                                <div>
                                    <CardTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                                        {userDetail.name}
                                        {isCurrentUser && <Badge variant="outline">Vous</Badge>}
                                    </CardTitle>
                                    <Badge className={roleInfo.color}>{roleInfo.label}</Badge>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                    <Mail className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Email</p>
                                        <p className="font-medium">{userDetail.email}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                    <Phone className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Téléphone</p>
                                        <p className="font-medium">{userDetail.phone || "Non renseigné"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                    <Building className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Entreprise</p>
                                        <p className="font-medium">{userDetail.company_name || "Non renseigné"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                    <MapPin className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Adresse</p>
                                        <p className="font-medium">{userDetail.address || "Non renseigné"}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
                                <div className="flex items-center gap-3">
                                    <Calendar className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Inscrit le</p>
                                        <p className="text-sm">{formatDate(userDetail.created_at)}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <Clock className="w-5 h-5 text-slate-400" />
                                    <div>
                                        <p className="text-xs text-slate-500">Dernière connexion</p>
                                        <p className="text-sm">{formatDate(userDetail.last_login)}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4 pt-4 border-t">
                                <div className="flex items-center gap-2">
                                    {userDetail.email_verified ? (
                                        <Badge className="bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" />Email vérifié</Badge>
                                    ) : (
                                        <Badge className="bg-amber-100 text-amber-800"><XCircle className="w-3 h-3 mr-1" />Email non vérifié</Badge>
                                    )}
                                </div>
                                <div>
                                    {userDetail.is_active ? (
                                        <Badge className="bg-green-100 text-green-800">Compte actif</Badge>
                                    ) : (
                                        <Badge variant="destructive">Compte désactivé</Badge>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Actions Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="font-['Barlow_Condensed']">Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {canModify && (
                                <>
                                    {/* Change Role */}
                                    <Button
                                        variant="outline"
                                        className="w-full justify-start"
                                        onClick={() => {
                                            setNewRole(userDetail.role);
                                            requestOTP(userDetail.id, userDetail.name, "promote_admin");
                                        }}
                                        data-testid="change-role-btn"
                                    >
                                        <ShieldCheck className="w-4 h-4 mr-2" />
                                        Modifier le rôle
                                    </Button>

                                    {/* Reset Password */}
                                    <Button
                                        variant="outline"
                                        className="w-full justify-start"
                                        onClick={() => requestOTP(userDetail.id, userDetail.name, "password_reset")}
                                        data-testid="reset-password-btn"
                                    >
                                        <Key className="w-4 h-4 mr-2" />
                                        Réinitialiser le mot de passe
                                    </Button>

                                    {/* Toggle Active */}
                                    <Button
                                        variant="outline"
                                        className="w-full justify-start"
                                        onClick={() => handleToggleActive(userDetail.id, userDetail.is_active)}
                                    >
                                        {userDetail.is_active ? (
                                            <><UserX className="w-4 h-4 mr-2" />Désactiver le compte</>
                                        ) : (
                                            <><UserCheck className="w-4 h-4 mr-2" />Activer le compte</>
                                        )}
                                    </Button>

                                    {/* Impersonate (Super Admin only) */}
                                    {isSuperAdmin() && (
                                        <Button
                                            variant="outline"
                                            className="w-full justify-start text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                                            onClick={() => requestOTP(userDetail.id, userDetail.name, "impersonation")}
                                            data-testid="impersonate-btn"
                                        >
                                            <UserCog className="w-4 h-4 mr-2" />
                                            Mode Support
                                        </Button>
                                    )}

                                    {/* Delete - Admin can delete users, Super Admin can delete anyone except super_admin */}
                                    {canDelete && (
                                        <Button
                                            variant="outline"
                                            className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => requestOTP(userDetail.id, userDetail.name, "delete_user")}
                                            data-testid="delete-user-btn"
                                        >
                                            <Trash2 className="w-4 h-4 mr-2" />
                                            Supprimer l'utilisateur
                                        </Button>
                                    )}
                                </>
                            )}
                            
                            {!canModify && (
                                <p className="text-sm text-slate-500 text-center py-4">
                                    {isCurrentUser ? "Vous ne pouvez pas modifier votre propre compte ici" : "Ce compte ne peut pas être modifié"}
                                </p>
                            )}
                        </CardContent>
                    </Card>

                    {/* Profile Completion Card */}
                    {profileCompletion && (
                        <Card className="lg:col-span-3">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                                            <CheckCircle className="w-5 h-5 text-orange-600" />
                                            Progression du profil
                                        </CardTitle>
                                        <CardDescription>
                                            {profileCompletion.completed_count}/{profileCompletion.total_count} éléments complétés
                                        </CardDescription>
                                    </div>
                                    <div className={`text-3xl font-bold ${getCompletionColor(profileCompletion.completion_percentage)}`}>
                                        {profileCompletion.completion_percentage}%
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* Progress Bar */}
                                <div className="space-y-2">
                                    <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                                        <div 
                                            className={`h-full transition-all duration-500 ${getProgressColor(profileCompletion.completion_percentage)}`}
                                            style={{ width: `${profileCompletion.completion_percentage}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Categories Summary */}
                                <div className="grid md:grid-cols-4 gap-4">
                                    {Object.entries(profileCompletion.summary || {}).filter(([key]) => !key.includes('_total')).map(([category, completed]) => {
                                        const total = profileCompletion.summary[`${category}_total`] || 0;
                                        const CategoryIcon = categoryIcons[category] || User;
                                        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
                                        const categoryLabels = {
                                            profil: "Profil",
                                            entreprise: "Entreprise",
                                            legal: "Légal",
                                            bancaire: "Bancaire"
                                        };
                                        
                                        return (
                                            <div key={category} className="p-4 bg-slate-50 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <CategoryIcon className="w-4 h-4 text-slate-500" />
                                                    <span className="font-medium text-sm">{categoryLabels[category]}</span>
                                                </div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className={`text-lg font-bold ${getCompletionColor(percentage)}`}>
                                                        {completed}/{total}
                                                    </span>
                                                    <span className={`text-sm ${getCompletionColor(percentage)}`}>
                                                        {percentage}%
                                                    </span>
                                                </div>
                                                <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                                    <div 
                                                        className={`h-full ${getProgressColor(percentage)}`}
                                                        style={{ width: `${percentage}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Detailed Items */}
                                <div className="space-y-2">
                                    <p className="text-sm font-medium text-slate-700">Détail des éléments</p>
                                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2">
                                        {profileCompletion.items?.map((item) => (
                                            <div 
                                                key={item.key}
                                                className={`flex items-center gap-2 p-2 rounded-lg text-sm ${
                                                    item.completed ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                                                }`}
                                            >
                                                {item.completed ? (
                                                    <Check className="w-4 h-4 text-green-600" />
                                                ) : (
                                                    <X className="w-4 h-4 text-red-500" />
                                                )}
                                                <span>{item.label}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        );
    }

    // Users List View
    return (
        <div className="space-y-6" data-testid="users-page">
            <div>
                <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
                    <Users className="w-8 h-8 text-orange-600" />
                    Gestion des utilisateurs
                </h1>
                <p className="text-slate-500 mt-1">
                    {users.length} utilisateur{users.length > 1 ? 's' : ''} enregistré{users.length > 1 ? 's' : ''}
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="font-['Barlow_Condensed']">Liste des utilisateurs</CardTitle>
                    <CardDescription>Cliquez sur un utilisateur pour voir sa fiche détaillée</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {users.map(u => {
                            const roleInfo = ROLE_LABELS[u.role] || ROLE_LABELS[ROLE_USER];
                            const RoleIcon = roleInfo.icon;
                            const isCurrentUser = u.id === currentUser?.id;

                            return (
                                <div
                                    key={u.id}
                                    onClick={() => loadUserDetail(u.id)}
                                    className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                                        !u.is_active ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200 hover:border-orange-300'
                                    } ${isCurrentUser ? 'ring-2 ring-orange-300' : ''}`}
                                    data-testid={`user-row-${u.id}`}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${roleInfo.color}`}>
                                            <RoleIcon className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-slate-900">{u.name}</span>
                                                {isCurrentUser && (
                                                    <Badge variant="outline" className="text-xs">Vous</Badge>
                                                )}
                                                {!u.is_active && (
                                                    <Badge variant="destructive" className="text-xs">Désactivé</Badge>
                                                )}
                                                {!u.email_verified && (
                                                    <Badge className="bg-amber-100 text-amber-800 text-xs">Non vérifié</Badge>
                                                )}
                                            </div>
                                            <p className="text-sm text-slate-500">{u.email}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <Badge className={roleInfo.color}>{roleInfo.label}</Badge>
                                        <Eye className="w-4 h-4 text-slate-400" />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* Deactivate Confirmation Dialog */}
            <AlertDialog open={!!deactivateDialogUser} onOpenChange={() => setDeactivateDialogUser(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Désactiver ce compte ?</AlertDialogTitle>
                        <AlertDialogDescription>
                            L'utilisateur <strong>{deactivateDialogUser?.name}</strong> ne pourra plus se connecter.
                            Vous pourrez réactiver son compte à tout moment.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={confirmDeactivate} className="bg-amber-600 hover:bg-amber-700">
                            Désactiver
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* OTP Dialog for sensitive actions */}
            <Dialog open={otpDialog.open} onOpenChange={(open) => !open && setOtpDialog({ open: false, type: null, userId: null, userName: null })}>
                <DialogContent data-testid="otp-dialog">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed']">{getOTPDialogTitle()}</DialogTitle>
                        <DialogDescription>
                            Un code de vérification a été envoyé à votre email. 
                            {otpDialog.userName && <span> Action sur: <strong>{otpDialog.userName}</strong></span>}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Code de vérification</Label>
                            <OTPInput value={otpCode} onChange={setOtpCode} />
                        </div>

                        {otpDialog.type === "promote_admin" && (
                            <div className="space-y-2">
                                <Label>Nouveau rôle</Label>
                                <Select value={newRole} onValueChange={setNewRole}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={ROLE_USER}>Utilisateur</SelectItem>
                                        <SelectItem value={ROLE_ADMIN}>Administrateur</SelectItem>
                                        {isSuperAdmin() && (
                                            <SelectItem value={ROLE_SUPER_ADMIN}>Super Admin</SelectItem>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {otpDialog.type === "password_reset" && (
                            <div className="space-y-2">
                                <Label>Nouveau mot de passe</Label>
                                <Input
                                    type="password"
                                    placeholder="Min. 8 caractères, 1 maj, 1 min, 1 chiffre"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                />
                            </div>
                        )}

                        {otpDialog.type === "delete_user" && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                <p className="text-sm text-red-800">
                                    <strong>Attention :</strong> Cette action est irréversible. 
                                    Toutes les données de l'utilisateur seront supprimées.
                                </p>
                            </div>
                        )}

                        {otpDialog.type === "impersonation" && (
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                                <p className="text-sm text-amber-800">
                                    <strong>Mode Support :</strong> Vous allez vous connecter en tant que cet utilisateur. 
                                    Une bannière sera visible et l'action sera enregistrée.
                                </p>
                            </div>
                        )}
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setOtpDialog({ open: false, type: null, userId: null, userName: null })}>
                            Annuler
                        </Button>
                        <Button
                            onClick={performOTPAction}
                            disabled={otpLoading || otpCode.length !== 6}
                            className={otpDialog.type === "delete_user" ? "bg-red-600 hover:bg-red-700" : "bg-orange-600 hover:bg-orange-700"}
                        >
                            {otpLoading ? "Vérification..." : "Confirmer"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
