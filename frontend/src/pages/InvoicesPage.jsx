import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getInvoices, deleteInvoice, downloadInvoicePdf, bulkDeleteInvoices, getClients } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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
import { Plus, Search, Eye, Pencil, Trash2, Download, Receipt, Users } from "lucide-react";
import { toast } from "sonner";

const statusLabels = {
    impaye: "Impayé",
    paye: "Payé",
    partiel: "Partiellement payé"
};

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState([]);
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [clientFilter, setClientFilter] = useState("all");
    const [deleteId, setDeleteId] = useState(null);
    const [selectedIds, setSelectedIds] = useState([]);
    const [showBulkDeleteDialog, setShowBulkDeleteDialog] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        loadInvoices();
    }, [statusFilter, clientFilter]);

    const loadData = async () => {
        try {
            const [invoicesRes, clientsRes] = await Promise.all([
                getInvoices(),
                getClients()
            ]);
            setInvoices(invoicesRes.data);
            setClients(clientsRes.data);
        } catch (error) {
            toast.error("Erreur lors du chargement des données");
        } finally {
            setLoading(false);
        }
    };

    const loadInvoices = async () => {
        try {
            const status = statusFilter !== "all" ? statusFilter : undefined;
            const clientId = clientFilter !== "all" ? clientFilter : undefined;
            const response = await getInvoices(status, clientId);
            setInvoices(response.data);
            setSelectedIds([]);
        } catch (error) {
            toast.error("Erreur lors du chargement des factures");
        }
    };

    const handleDelete = async () => {
        if (!deleteId) return;
        try {
            await deleteInvoice(deleteId);
            toast.success("Facture supprimée avec succès");
            loadInvoices();
        } catch (error) {
            toast.error("Erreur lors de la suppression de la facture");
        } finally {
            setDeleteId(null);
        }
    };

    const handleBulkDelete = async () => {
        if (selectedIds.length === 0) return;
        try {
            const response = await bulkDeleteInvoices(selectedIds);
            toast.success(response.data.message);
            loadInvoices();
        } catch (error) {
            toast.error("Erreur lors de la suppression des factures");
        } finally {
            setShowBulkDeleteDialog(false);
        }
    };

    const handleDownloadPdf = async (invoice) => {
        try {
            await downloadInvoicePdf(invoice.id, invoice.invoice_number);
            toast.success("PDF téléchargé");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du PDF");
        }
    };

    const filteredInvoices = invoices.filter(invoice => {
        const matchesSearch = 
            invoice.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
            invoice.client_name.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesSearch;
    });

    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedIds(filteredInvoices.map(inv => inv.id));
        } else {
            setSelectedIds([]);
        }
    };

    const handleSelectOne = (id, checked) => {
        if (checked) {
            setSelectedIds(prev => [...prev, id]);
        } else {
            setSelectedIds(prev => prev.filter(i => i !== id));
        }
    };

    const isAllSelected = filteredInvoices.length > 0 && selectedIds.length === filteredInvoices.length;
    const isSomeSelected = selectedIds.length > 0 && selectedIds.length < filteredInvoices.length;

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('fr-FR');
    };

    const formatCurrency = (amount) => {
        return amount.toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6" data-testid="invoices-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                        Factures
                    </h1>
                    <p className="text-slate-500 mt-1">{invoices.length} facture(s)</p>
                </div>
                <div className="flex gap-2">
                    {selectedIds.length > 0 && (
                        <Button 
                            variant="destructive"
                            onClick={() => setShowBulkDeleteDialog(true)}
                            data-testid="bulk-delete-btn"
                        >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Supprimer ({selectedIds.length})
                        </Button>
                    )}
                    <Link to="/factures/new">
                        <Button className="bg-orange-600 hover:bg-orange-700" data-testid="add-invoice-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Nouvelle facture
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                        placeholder="Rechercher une facture..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                        data-testid="search-input"
                    />
                </div>
                <Select value={clientFilter} onValueChange={setClientFilter}>
                    <SelectTrigger className="w-56" data-testid="client-filter">
                        <Users className="w-4 h-4 mr-2 text-slate-400" />
                        <SelectValue placeholder="Tous les clients" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Tous les clients</SelectItem>
                        {clients.map(client => (
                            <SelectItem key={client.id} value={client.id}>{client.name}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-48" data-testid="status-filter">
                        <SelectValue placeholder="Tous les statuts" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Tous les statuts</SelectItem>
                        <SelectItem value="impaye">Impayé</SelectItem>
                        <SelectItem value="paye">Payé</SelectItem>
                        <SelectItem value="partiel">Partiellement payé</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Table */}
            {filteredInvoices.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <Receipt className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-slate-900">Aucune facture</h3>
                        <p className="text-slate-500 mt-1">
                            {searchQuery || statusFilter !== "all"
                                ? "Aucune facture ne correspond à vos critères" 
                                : "Commencez par créer votre première facture"}
                        </p>
                        {!searchQuery && statusFilter === "all" && (
                            <Link to="/factures/new">
                                <Button className="mt-4 bg-orange-600 hover:bg-orange-700">
                                    <Plus className="w-4 h-4 mr-2" />
                                    Créer une facture
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
                                    <TableHead className="w-12">
                                        <Checkbox
                                            checked={isAllSelected}
                                            ref={(el) => {
                                                if (el) el.indeterminate = isSomeSelected;
                                            }}
                                            onCheckedChange={handleSelectAll}
                                            className="border-white data-[state=checked]:bg-orange-600 data-[state=checked]:border-orange-600"
                                            data-testid="select-all-checkbox"
                                        />
                                    </TableHead>
                                    <TableHead className="text-white font-semibold">N° Facture</TableHead>
                                    <TableHead className="text-white font-semibold">Client</TableHead>
                                    <TableHead className="text-white font-semibold">Date</TableHead>
                                    <TableHead className="text-white font-semibold">Montant TTC</TableHead>
                                    <TableHead className="text-white font-semibold">Statut</TableHead>
                                    <TableHead className="text-white font-semibold text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredInvoices.map((invoice, index) => (
                                    <TableRow 
                                        key={invoice.id} 
                                        className={`table-row-hover ${selectedIds.includes(invoice.id) ? 'bg-orange-50' : ''}`}
                                        data-testid={`invoice-row-${index}`}
                                    >
                                        <TableCell>
                                            <Checkbox
                                                checked={selectedIds.includes(invoice.id)}
                                                onCheckedChange={(checked) => handleSelectOne(invoice.id, checked)}
                                                data-testid={`select-invoice-${index}`}
                                            />
                                        </TableCell>
                                        <TableCell className="font-mono font-medium">{invoice.invoice_number}</TableCell>
                                        <TableCell className="font-medium">{invoice.client_name}</TableCell>
                                        <TableCell className="text-slate-600">{formatDate(invoice.issue_date)}</TableCell>
                                        <TableCell className="font-medium">{formatCurrency(invoice.total_ttc)}</TableCell>
                                        <TableCell>
                                            <span className={`status-badge status-${invoice.payment_status}`}>
                                                {statusLabels[invoice.payment_status]}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-1">
                                                <Link to={`/factures/${invoice.id}`}>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-blue-50 hover:text-blue-600"
                                                        data-testid={`view-invoice-${index}`}
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                </Link>
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    className="hover:bg-green-50 hover:text-green-600"
                                                    onClick={() => handleDownloadPdf(invoice)}
                                                    data-testid={`download-invoice-${index}`}
                                                >
                                                    <Download className="w-4 h-4" />
                                                </Button>
                                                <Link to={`/factures/${invoice.id}/edit`}>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-orange-50 hover:text-orange-600"
                                                        data-testid={`edit-invoice-${index}`}
                                                    >
                                                        <Pencil className="w-4 h-4" />
                                                    </Button>
                                                </Link>
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    className="hover:bg-red-50 hover:text-red-600"
                                                    onClick={() => setDeleteId(invoice.id)}
                                                    data-testid={`delete-invoice-${index}`}
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

            {/* Single Delete Dialog */}
            <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Confirmer la suppression</AlertDialogTitle>
                        <AlertDialogDescription>
                            Êtes-vous sûr de vouloir supprimer cette facture ? Cette action est irréversible.
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

            {/* Bulk Delete Dialog */}
            <AlertDialog open={showBulkDeleteDialog} onOpenChange={setShowBulkDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Suppression groupée</AlertDialogTitle>
                        <AlertDialogDescription>
                            Êtes-vous sûr de vouloir supprimer <strong>{selectedIds.length} facture(s)</strong> ? 
                            Cette action est irréversible et supprimera définitivement toutes les factures sélectionnées.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={handleBulkDelete}
                            className="bg-red-600 hover:bg-red-700"
                            data-testid="confirm-bulk-delete-btn"
                        >
                            Supprimer {selectedIds.length} facture(s)
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
