import { useState, useEffect } from "react";
import { useAuth, ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER } from "@/context/AuthContext";
import { getUsers, updateUserRole, activateUser, deactivateUser, deleteUser } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Users, Shield, ShieldCheck, User, UserX, UserCheck, Trash2, Crown } from "lucide-react";
import { toast } from "sonner";

const ROLE_LABELS = {
    [ROLE_SUPER_ADMIN]: { label: "Super Admin", color: "bg-purple-100 text-purple-800", icon: Crown },
    [ROLE_ADMIN]: { label: "Administrateur", color: "bg-blue-100 text-blue-800", icon: ShieldCheck },
    [ROLE_USER]: { label: "Utilisateur", color: "bg-slate-100 text-slate-800", icon: User }
};

export default function UsersPage() {
    const { user: currentUser, isAdmin, isSuperAdmin } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteDialogUser, setDeleteDialogUser] = useState(null);
    const [deactivateDialogUser, setDeactivateDialogUser] = useState(null);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = async () => {
        try {
            const response = await getUsers();
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

    const handleRoleChange = async (userId, newRole) => {
        try {
            await updateUserRole(userId, newRole);
            toast.success("Rôle modifié avec succès");
            loadUsers();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la modification du rôle");
        }
    };

    const handleToggleActive = async (userId, isActive) => {
        try {
            if (isActive) {
                setDeactivateDialogUser(users.find(u => u.id === userId));
            } else {
                await activateUser(userId);
                toast.success("Compte activé");
                loadUsers();
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur");
        }
    };

    const confirmDeactivate = async () => {
        if (!deactivateDialogUser) return;
        try {
            await deactivateUser(deactivateDialogUser.id);
            toast.success("Compte désactivé");
            setDeactivateDialogUser(null);
            loadUsers();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la désactivation");
        }
    };

    const handleDelete = async (userId) => {
        setDeleteDialogUser(users.find(u => u.id === userId));
    };

    const confirmDelete = async () => {
        if (!deleteDialogUser) return;
        try {
            await deleteUser(deleteDialogUser.id);
            toast.success("Utilisateur supprimé");
            setDeleteDialogUser(null);
            loadUsers();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la suppression");
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
                    <CardDescription>Gérez les comptes et les permissions des utilisateurs</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {users.map(u => {
                            const roleInfo = ROLE_LABELS[u.role] || ROLE_LABELS[ROLE_USER];
                            const RoleIcon = roleInfo.icon;
                            const isCurrentUser = u.id === currentUser?.id;
                            const canEditRole = isSuperAdmin() || (isAdmin() && u.role !== ROLE_SUPER_ADMIN);
                            const canToggleActive = !isCurrentUser && u.role !== ROLE_SUPER_ADMIN;
                            const canDelete = isSuperAdmin() && !isCurrentUser && u.role !== ROLE_SUPER_ADMIN;

                            return (
                                <div
                                    key={u.id}
                                    className={`flex items-center justify-between p-4 rounded-lg border ${
                                        !u.is_active ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'
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
                                            </div>
                                            <p className="text-sm text-slate-500">{u.email}</p>
                                            <p className="text-xs text-slate-400">
                                                Dernière connexion: {formatDate(u.last_login)}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        {/* Role selector */}
                                        {canEditRole ? (
                                            <Select
                                                value={u.role}
                                                onValueChange={(val) => handleRoleChange(u.id, val)}
                                            >
                                                <SelectTrigger className="w-40" data-testid={`role-select-${u.id}`}>
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
                                        ) : (
                                            <Badge className={roleInfo.color}>{roleInfo.label}</Badge>
                                        )}

                                        {/* Activate/Deactivate button */}
                                        {canToggleActive && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleToggleActive(u.id, u.is_active)}
                                                className={u.is_active ? "hover:bg-amber-50 hover:text-amber-600" : "hover:bg-green-50 hover:text-green-600"}
                                                title={u.is_active ? "Désactiver" : "Activer"}
                                            >
                                                {u.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                                            </Button>
                                        )}

                                        {/* Delete button (super admin only) */}
                                        {canDelete && (
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleDelete(u.id)}
                                                className="hover:bg-red-50 hover:text-red-600"
                                                title="Supprimer"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        )}
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

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!deleteDialogUser} onOpenChange={() => setDeleteDialogUser(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Supprimer définitivement ?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Cette action est irréversible. L'utilisateur <strong>{deleteDialogUser?.name}</strong> et toutes ses données seront supprimés.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
                            Supprimer
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
