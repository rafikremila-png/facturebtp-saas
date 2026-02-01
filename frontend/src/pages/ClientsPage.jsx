import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getClients, deleteClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, Search, Pencil, Trash2, Mail, Phone, MapPin, Users } from "lucide-react";
import { toast } from "sonner";

export default function ClientsPage() {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [deleteId, setDeleteId] = useState(null);

    useEffect(() => {
        loadClients();
    }, []);

    const loadClients = async () => {
        try {
            const response = await getClients();
            setClients(response.data);
        } catch (error) {
            toast.error("Erreur lors du chargement des clients");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteId) return;
        try {
            await deleteClient(deleteId);
            toast.success("Client supprimé avec succès");
            loadClients();
        } catch (error) {
            toast.error("Erreur lors de la suppression du client");
        } finally {
            setDeleteId(null);
        }
    };

    const filteredClients = clients.filter(client =>
        client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        client.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6" data-testid="clients-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                        Clients
                    </h1>
                    <p className="text-slate-500 mt-1">{clients.length} client(s) enregistré(s)</p>
                </div>
                <Link to="/clients/new">
                    <Button className="bg-orange-600 hover:bg-orange-700" data-testid="add-client-btn">
                        <Plus className="w-4 h-4 mr-2" />
                        Nouveau client
                    </Button>
                </Link>
            </div>

            {/* Search */}
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                    placeholder="Rechercher un client..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                    data-testid="search-input"
                />
            </div>

            {/* Table */}
            {filteredClients.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-slate-900">Aucun client</h3>
                        <p className="text-slate-500 mt-1">
                            {searchQuery 
                                ? "Aucun client ne correspond à votre recherche" 
                                : "Commencez par ajouter votre premier client"}
                        </p>
                        {!searchQuery && (
                            <Link to="/clients/new">
                                <Button className="mt-4 bg-orange-600 hover:bg-orange-700">
                                    <Plus className="w-4 h-4 mr-2" />
                                    Ajouter un client
                                </Button>
                            </Link>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <Card>
                    <CardContent className="p-0">
                        <Table>
                            <TableHeader>
                                <TableRow className="bg-slate-900 hover:bg-slate-900">
                                    <TableHead className="text-white font-semibold">Nom</TableHead>
                                    <TableHead className="text-white font-semibold">Email</TableHead>
                                    <TableHead className="text-white font-semibold">Téléphone</TableHead>
                                    <TableHead className="text-white font-semibold">Adresse</TableHead>
                                    <TableHead className="text-white font-semibold text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredClients.map((client, index) => (
                                    <TableRow 
                                        key={client.id} 
                                        className="table-row-hover"
                                        data-testid={`client-row-${index}`}
                                    >
                                        <TableCell className="font-medium">{client.name}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2 text-slate-600">
                                                <Mail className="w-4 h-4" />
                                                {client.email || "-"}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2 text-slate-600">
                                                <Phone className="w-4 h-4" />
                                                {client.phone || "-"}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2 text-slate-600 max-w-xs truncate">
                                                <MapPin className="w-4 h-4 flex-shrink-0" />
                                                {client.address || "-"}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-2">
                                                <Link to={`/clients/${client.id}/edit`}>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-orange-50 hover:text-orange-600"
                                                        data-testid={`edit-client-${index}`}
                                                    >
                                                        <Pencil className="w-4 h-4" />
                                                    </Button>
                                                </Link>
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    className="hover:bg-red-50 hover:text-red-600"
                                                    onClick={() => setDeleteId(client.id)}
                                                    data-testid={`delete-client-${index}`}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* Delete Dialog */}
            <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Confirmer la suppression</AlertDialogTitle>
                        <AlertDialogDescription>
                            Êtes-vous sûr de vouloir supprimer ce client ? Cette action est irréversible.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={handleDelete}
                            className="bg-red-600 hover:bg-red-700"
                            data-testid="confirm-delete-btn"
                        >
                            Supprimer
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
