import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getClients, deleteClient } from "@/lib/api";
import api from "@/lib/api";
import { exportClientsCSV } from "@/lib/csvExport";
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
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus, Search, Pencil, Trash2, Mail, Phone, MapPin, Users, MoreVertical, ExternalLink, Copy, PenTool, Link2, Check, Loader2, FileDown } from "lucide-react";
import { toast } from "sonner";

export default function ClientsPage() {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [deleteId, setDeleteId] = useState(null);
    
    // Portal link modal
    const [showPortalModal, setShowPortalModal] = useState(false);
    const [selectedClient, setSelectedClient] = useState(null);
    const [portalLink, setPortalLink] = useState("");
    const [generatingLink, setGeneratingLink] = useState(false);
    const [linkCopied, setLinkCopied] = useState(false);

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

    const handleGeneratePortalLink = async (client) => {
        setSelectedClient(client);
        setShowPortalModal(true);
        setPortalLink("");
        setLinkCopied(false);
        setGeneratingLink(true);
        
        try {
            // Use MongoDB-based endpoint for clients
            const response = await api.post(`/clients/${client.id}/portal-token`);
            const baseUrl = window.location.origin;
            const link = `${baseUrl}/portal/${response.data.token}`;
            setPortalLink(link);
        } catch (error) {
            console.error("Error generating portal link:", error);
            toast.error(error.response?.data?.detail || "Erreur lors de la génération du lien");
            setShowPortalModal(false);
        } finally {
            setGeneratingLink(false);
        }
    };

    const handleCopyLink = () => {
        if (portalLink) {
            navigator.clipboard.writeText(portalLink);
            setLinkCopied(true);
            toast.success("Lien copié dans le presse-papiers");
            setTimeout(() => setLinkCopied(false), 3000);
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
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => exportClientsCSV(clients)} data-testid="export-clients-csv">
                        <FileDown className="w-4 h-4 mr-2" />
                        Export CSV
                    </Button>
                    <Link to="/clients/new">
                        <Button className="bg-orange-600 hover:bg-orange-700" data-testid="add-client-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Nouveau client
                        </Button>
                    </Link>
                </div>
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
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button 
                                                            variant="ghost" 
                                                            size="icon"
                                                            className="hover:bg-slate-100"
                                                        >
                                                            <MoreVertical className="w-4 h-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuItem asChild>
                                                            <Link to={`/clients/${client.id}/edit`} className="flex items-center">
                                                                <Pencil className="w-4 h-4 mr-2" />
                                                                Modifier
                                                            </Link>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem 
                                                            onClick={() => handleGeneratePortalLink(client)}
                                                            data-testid={`portal-link-${index}`}
                                                        >
                                                            <PenTool className="w-4 h-4 mr-2 text-orange-600" />
                                                            <span className="text-orange-600 font-medium">Portail & Signature</span>
                                                        </DropdownMenuItem>
                                                        <DropdownMenuSeparator />
                                                        <DropdownMenuItem 
                                                            onClick={() => setDeleteId(client.id)}
                                                            className="text-red-600"
                                                        >
                                                            <Trash2 className="w-4 h-4 mr-2" />
                                                            Supprimer
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
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

            {/* Portal Link Modal */}
            <Dialog open={showPortalModal} onOpenChange={setShowPortalModal}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <PenTool className="w-5 h-5 text-orange-600" />
                            Portail Client & Signature
                        </DialogTitle>
                        <DialogDescription>
                            {selectedClient && (
                                <>Générez un lien d'accès au portail pour <strong>{selectedClient.name}</strong></>
                            )}
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="py-4 space-y-4">
                        {generatingLink ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
                            </div>
                        ) : portalLink ? (
                            <>
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <div className="flex items-center justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs text-slate-500 mb-1">Lien du portail (valide 7 jours)</p>
                                            <p className="text-sm font-mono truncate text-slate-700">{portalLink}</p>
                                        </div>
                                        <Button 
                                            variant="outline" 
                                            size="sm"
                                            onClick={handleCopyLink}
                                            className={linkCopied ? "bg-green-50 border-green-200" : ""}
                                        >
                                            {linkCopied ? (
                                                <>
                                                    <Check className="w-4 h-4 mr-1 text-green-600" />
                                                    Copié
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="w-4 h-4 mr-1" />
                                                    Copier
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </div>
                                
                                <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                                    <h4 className="font-medium text-orange-900 flex items-center gap-2 mb-2">
                                        <PenTool className="w-4 h-4" />
                                        Fonctionnalités du portail
                                    </h4>
                                    <ul className="text-sm text-orange-800 space-y-1">
                                        <li>• Voir tous les devis du client</li>
                                        <li>• <strong>Signer les devis électroniquement</strong></li>
                                        <li>• Voir toutes les factures</li>
                                        <li>• Télécharger les PDF</li>
                                    </ul>
                                </div>
                                
                                <div className="text-sm text-slate-500">
                                    <p>💡 Envoyez ce lien à votre client par email. Il pourra consulter ses documents et signer ses devis sans créer de compte.</p>
                                </div>
                            </>
                        ) : null}
                    </div>
                    
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowPortalModal(false)}>
                            Fermer
                        </Button>
                        {portalLink && (
                            <Button 
                                className="bg-orange-600 hover:bg-orange-700"
                                onClick={() => window.open(portalLink, '_blank')}
                            >
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Ouvrir le portail
                            </Button>
                        )}
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
