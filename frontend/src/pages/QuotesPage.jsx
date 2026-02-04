import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getQuotes, deleteQuote, downloadQuotePdf, bulkDeleteQuotes, getClients } from "@/lib/api";
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
import { Plus, Search, Eye, Pencil, Trash2, Download, FileText, Users } from "lucide-react";
import { toast } from "sonner";

const statusLabels = {
    brouillon: "Brouillon",
    envoye: "Envoyé",
    accepte: "Accepté",
    refuse: "Refusé",
    facture: "Facturé"
};

export default function QuotesPage() {
    const [quotes, setQuotes] = useState([]);
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
        loadQuotes();
    }, [statusFilter, clientFilter]);

    const loadData = async () => {
        try {
            const [quotesRes, clientsRes] = await Promise.all([
                getQuotes(),
                getClients()
            ]);
            setQuotes(quotesRes.data);
            setClients(clientsRes.data);
        } catch (error) {
            toast.error("Erreur lors du chargement des données");
        } finally {
            setLoading(false);
        }
    };

    const loadQuotes = async () => {
        try {
            const status = statusFilter !== "all" ? statusFilter : undefined;
            const clientId = clientFilter !== "all" ? clientFilter : undefined;
            const response = await getQuotes(status, clientId);
            setQuotes(response.data);
            setSelectedIds([]);
        } catch (error) {
            toast.error("Erreur lors du chargement des devis");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteId) return;
        try {
            await deleteQuote(deleteId);
            toast.success("Devis supprimé avec succès");
            loadQuotes();
        } catch (error) {
            toast.error("Erreur lors de la suppression du devis");
        } finally {
            setDeleteId(null);
        }
    };

    const handleBulkDelete = async () => {
        if (selectedIds.length === 0) return;
        try {
            const response = await bulkDeleteQuotes(selectedIds);
            toast.success(response.data.message);
            loadQuotes();
        } catch (error) {
            toast.error("Erreur lors de la suppression des devis");
        } finally {
            setShowBulkDeleteDialog(false);
        }
    };

    const handleDownloadPdf = async (quote) => {
        try {
            await downloadQuotePdf(quote.id, quote.quote_number);
            toast.success("PDF téléchargé");
        } catch (error) {
            toast.error("Erreur lors du téléchargement du PDF");
        }
    };

    const filteredQuotes = quotes.filter(quote => {
        const matchesSearch = 
            quote.quote_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
            quote.client_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === "all" || quote.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const handleSelectAll = (checked) => {
        if (checked) {
            setSelectedIds(filteredQuotes.map(q => q.id));
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

    const isAllSelected = filteredQuotes.length > 0 && selectedIds.length === filteredQuotes.length;
    const isSomeSelected = selectedIds.length > 0 && selectedIds.length < filteredQuotes.length;

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
        <div className="space-y-6" data-testid="quotes-page">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed']">
                        Devis
                    </h1>
                    <p className="text-slate-500 mt-1">{quotes.length} devis</p>
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
                    <Link to="/devis/new">
                        <Button className="bg-orange-600 hover:bg-orange-700" data-testid="add-quote-btn">
                            <Plus className="w-4 h-4 mr-2" />
                            Nouveau devis
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                        placeholder="Rechercher un devis..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                        data-testid="search-input"
                    />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-48" data-testid="status-filter">
                        <SelectValue placeholder="Tous les statuts" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">Tous les statuts</SelectItem>
                        <SelectItem value="brouillon">Brouillon</SelectItem>
                        <SelectItem value="envoye">Envoyé</SelectItem>
                        <SelectItem value="accepte">Accepté</SelectItem>
                        <SelectItem value="refuse">Refusé</SelectItem>
                        <SelectItem value="facture">Facturé</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Table */}
            {filteredQuotes.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-slate-900">Aucun devis</h3>
                        <p className="text-slate-500 mt-1">
                            {searchQuery || statusFilter !== "all"
                                ? "Aucun devis ne correspond à vos critères" 
                                : "Commencez par créer votre premier devis"}
                        </p>
                        {!searchQuery && statusFilter === "all" && (
                            <Link to="/devis/new">
                                <Button className="mt-4 bg-orange-600 hover:bg-orange-700">
                                    <Plus className="w-4 h-4 mr-2" />
                                    Créer un devis
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
                                    <TableHead className="text-white font-semibold">N° Devis</TableHead>
                                    <TableHead className="text-white font-semibold">Client</TableHead>
                                    <TableHead className="text-white font-semibold">Date</TableHead>
                                    <TableHead className="text-white font-semibold">Montant TTC</TableHead>
                                    <TableHead className="text-white font-semibold">Statut</TableHead>
                                    <TableHead className="text-white font-semibold text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredQuotes.map((quote, index) => (
                                    <TableRow 
                                        key={quote.id} 
                                        className={`table-row-hover ${selectedIds.includes(quote.id) ? 'bg-orange-50' : ''}`}
                                        data-testid={`quote-row-${index}`}
                                    >
                                        <TableCell>
                                            <Checkbox
                                                checked={selectedIds.includes(quote.id)}
                                                onCheckedChange={(checked) => handleSelectOne(quote.id, checked)}
                                                data-testid={`select-quote-${index}`}
                                            />
                                        </TableCell>
                                        <TableCell className="font-mono font-medium">{quote.quote_number}</TableCell>
                                        <TableCell className="font-medium">{quote.client_name}</TableCell>
                                        <TableCell className="text-slate-600">{formatDate(quote.issue_date)}</TableCell>
                                        <TableCell className="font-medium">{formatCurrency(quote.total_ttc)}</TableCell>
                                        <TableCell>
                                            <span className={`status-badge status-${quote.status}`}>
                                                {statusLabels[quote.status]}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-1">
                                                <Link to={`/devis/${quote.id}`}>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-blue-50 hover:text-blue-600"
                                                        data-testid={`view-quote-${index}`}
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                </Link>
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    className="hover:bg-green-50 hover:text-green-600"
                                                    onClick={() => handleDownloadPdf(quote)}
                                                    data-testid={`download-quote-${index}`}
                                                >
                                                    <Download className="w-4 h-4" />
                                                </Button>
                                                <Link to={`/devis/${quote.id}/edit`}>
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        className="hover:bg-orange-50 hover:text-orange-600"
                                                        data-testid={`edit-quote-${index}`}
                                                    >
                                                        <Pencil className="w-4 h-4" />
                                                    </Button>
                                                </Link>
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    className="hover:bg-red-50 hover:text-red-600"
                                                    onClick={() => setDeleteId(quote.id)}
                                                    data-testid={`delete-quote-${index}`}
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
                            Êtes-vous sûr de vouloir supprimer ce devis ? Cette action est irréversible.
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
                            Êtes-vous sûr de vouloir supprimer <strong>{selectedIds.length} devis</strong> ? 
                            Cette action est irréversible et supprimera définitivement tous les devis sélectionnés.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={handleBulkDelete}
                            className="bg-red-600 hover:bg-red-700"
                            data-testid="confirm-bulk-delete-btn"
                        >
                            Supprimer {selectedIds.length} devis
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
