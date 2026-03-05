import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { 
    FolderKanban, Plus, Search, Edit2, Trash2, MapPin, Calendar, 
    Users, Euro, Clock, MoreVertical, Eye, Play, Pause, CheckCircle,
    XCircle, AlertTriangle, TrendingUp, Building2, FileText, Receipt
} from "lucide-react";
import { toast } from "sonner";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Project statuses
const PROJECT_STATUSES = {
    planning: { label: "Planification", color: "bg-blue-100 text-blue-800", icon: Clock },
    in_progress: { label: "En cours", color: "bg-green-100 text-green-800", icon: Play },
    on_hold: { label: "En pause", color: "bg-amber-100 text-amber-800", icon: Pause },
    completed: { label: "Terminé", color: "bg-slate-100 text-slate-800", icon: CheckCircle },
    cancelled: { label: "Annulé", color: "bg-red-100 text-red-800", icon: XCircle }
};

export default function ProjectsPage() {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    
    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [selectedProject, setSelectedProject] = useState(null);
    const [saving, setSaving] = useState(false);
    
    // Form state
    const [formData, setFormData] = useState({
        project_name: "",
        description: "",
        client_id: "",
        address: "",
        city: "",
        postal_code: "",
        status: "planning",
        start_date: "",
        end_date: "",
        budget: 0,
        estimated_cost: 0,
        permit_number: "",
        insurance_number: ""
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [projectsRes, clientsRes] = await Promise.all([
                api.get("/projects"),
                api.get("/clients")
            ]);
            
            setProjects(projectsRes.data);
            setClients(clientsRes.data);
        } catch (error) {
            console.error("Erreur chargement:", error);
            toast.error("Erreur lors du chargement des chantiers");
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!formData.project_name.trim()) {
            toast.error("Le nom du chantier est obligatoire");
            return;
        }
        
        setSaving(true);
        try {
            const payload = {
                ...formData,
                client_id: formData.client_id === "none" || !formData.client_id ? null : formData.client_id,
                budget: parseFloat(formData.budget) || 0,
                estimated_cost: parseFloat(formData.estimated_cost) || 0,
                start_date: formData.start_date || null,
                end_date: formData.end_date || null
            };
            
            await api.post("/projects", payload);
            toast.success("Chantier créé avec succès");
            setShowCreateModal(false);
            resetForm();
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la création");
        } finally {
            setSaving(false);
        }
    };

    const handleUpdate = async () => {
        if (!selectedProject || !formData.project_name.trim()) {
            toast.error("Le nom du chantier est obligatoire");
            return;
        }
        
        setSaving(true);
        try {
            const payload = {
                ...formData,
                client_id: formData.client_id === "none" || !formData.client_id ? null : formData.client_id,
                budget: parseFloat(formData.budget) || 0,
                estimated_cost: parseFloat(formData.estimated_cost) || 0,
                start_date: formData.start_date || null,
                end_date: formData.end_date || null
            };
            
            await api.put(`/projects/${selectedProject.id}`, payload);
            toast.success("Chantier mis à jour");
            setShowEditModal(false);
            setSelectedProject(null);
            resetForm();
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la mise à jour");
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!selectedProject) return;
        
        try {
            await api.delete(`/projects/${selectedProject.id}`);
            toast.success("Chantier supprimé");
            setShowDeleteDialog(false);
            setSelectedProject(null);
            loadData();
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de la suppression");
        }
    };

    const handleStatusChange = async (project, newStatus) => {
        try {
            await api.put(`/projects/${project.id}`, { status: newStatus });
            toast.success("Statut mis à jour");
            loadData();
        } catch (error) {
            toast.error("Erreur lors de la mise à jour du statut");
        }
    };

    const resetForm = () => {
        setFormData({
            project_name: "",
            description: "",
            client_id: "",
            address: "",
            city: "",
            postal_code: "",
            status: "planning",
            start_date: "",
            end_date: "",
            budget: 0,
            estimated_cost: 0,
            permit_number: "",
            insurance_number: ""
        });
    };

    const openEditModal = (project) => {
        setSelectedProject(project);
        setFormData({
            project_name: project.project_name,
            description: project.description || "",
            client_id: project.client_id || "",
            address: project.address || "",
            city: project.city || "",
            postal_code: project.postal_code || "",
            status: project.status,
            start_date: project.start_date ? project.start_date.split("T")[0] : "",
            end_date: project.end_date ? project.end_date.split("T")[0] : "",
            budget: project.budget || 0,
            estimated_cost: project.estimated_cost || 0,
            permit_number: project.permit_number || "",
            insurance_number: project.insurance_number || ""
        });
        setShowEditModal(true);
    };

    // Filter projects
    const filteredProjects = projects.filter(project => {
        const matchesSearch = !searchQuery || 
            project.project_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (project.address && project.address.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (project.city && project.city.toLowerCase().includes(searchQuery.toLowerCase()));
        
        const matchesStatus = statusFilter === "all" || project.status === statusFilter;
        
        return matchesSearch && matchesStatus;
    });

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            maximumFractionDigits: 0
        }).format(amount || 0);
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    };

    const getClientName = (clientId) => {
        const client = clients.find(c => c.id === clientId);
        return client ? (client.company_name || client.name) : "Non attribué";
    };

    const calculateProgress = (project) => {
        if (!project.budget || project.budget === 0) return 0;
        return Math.min(100, Math.round((project.total_invoiced / project.budget) * 100));
    };

    // Stats
    const stats = {
        total: projects.length,
        in_progress: projects.filter(p => p.status === "in_progress").length,
        total_budget: projects.reduce((sum, p) => sum + (p.budget || 0), 0),
        total_invoiced: projects.reduce((sum, p) => sum + (p.total_invoiced || 0), 0)
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6" data-testid="projects-page">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
                        <FolderKanban className="w-8 h-8 text-orange-600" />
                        Chantiers
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Gérez vos projets de construction ({projects.length} chantiers)
                    </p>
                </div>
                <Button 
                    onClick={() => setShowCreateModal(true)}
                    className="bg-orange-600 hover:bg-orange-700"
                    data-testid="create-project-btn"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Nouveau chantier
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Total chantiers</p>
                                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                            </div>
                            <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
                                <FolderKanban className="w-6 h-6 text-slate-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">En cours</p>
                                <p className="text-2xl font-bold text-green-600">{stats.in_progress}</p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                <Play className="w-6 h-6 text-green-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Budget total</p>
                                <p className="text-2xl font-bold text-slate-900">{formatCurrency(stats.total_budget)}</p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Euro className="w-6 h-6 text-blue-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Facturé</p>
                                <p className="text-2xl font-bold text-orange-600">{formatCurrency(stats.total_invoiced)}</p>
                            </div>
                            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-orange-600" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <Input
                                placeholder="Rechercher un chantier..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                                data-testid="search-projects"
                            />
                        </div>
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-full md:w-48" data-testid="filter-status">
                                <SelectValue placeholder="Statut" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Tous les statuts</SelectItem>
                                {Object.entries(PROJECT_STATUSES).map(([key, { label }]) => (
                                    <SelectItem key={key} value={key}>{label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            {/* Projects List */}
            {filteredProjects.length === 0 ? (
                <Card>
                    <CardContent className="py-12">
                        <div className="text-center">
                            <FolderKanban className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-slate-900 mb-2">
                                Aucun chantier trouvé
                            </h3>
                            <p className="text-slate-500 mb-4">
                                {searchQuery || statusFilter !== "all" 
                                    ? "Essayez de modifier vos filtres"
                                    : "Commencez par créer votre premier chantier"
                                }
                            </p>
                            {!searchQuery && statusFilter === "all" && (
                                <Button 
                                    onClick={() => setShowCreateModal(true)}
                                    className="bg-orange-600 hover:bg-orange-700"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Créer un chantier
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {filteredProjects.map((project) => {
                        const statusInfo = PROJECT_STATUSES[project.status] || PROJECT_STATUSES.planning;
                        const StatusIcon = statusInfo.icon;
                        const progress = calculateProgress(project);
                        
                        return (
                            <Card 
                                key={project.id} 
                                className="hover:shadow-md transition-shadow"
                                data-testid={`project-${project.id}`}
                            >
                                <CardContent className="pt-6">
                                    <div className="flex flex-col md:flex-row md:items-start gap-4">
                                        {/* Project Info */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start gap-3">
                                                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                                    <Building2 className="w-6 h-6 text-orange-600" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <h3 className="font-semibold text-lg text-slate-900 truncate">
                                                            {project.project_name}
                                                        </h3>
                                                        <Badge className={statusInfo.color}>
                                                            <StatusIcon className="w-3 h-3 mr-1" />
                                                            {statusInfo.label}
                                                        </Badge>
                                                    </div>
                                                    
                                                    {(project.address || project.city) && (
                                                        <div className="flex items-center gap-1 text-sm text-slate-500 mt-1">
                                                            <MapPin className="w-3 h-3" />
                                                            {[project.address, project.postal_code, project.city].filter(Boolean).join(", ")}
                                                        </div>
                                                    )}
                                                    
                                                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 flex-wrap">
                                                        <div className="flex items-center gap-1">
                                                            <Users className="w-3 h-3" />
                                                            {getClientName(project.client_id)}
                                                        </div>
                                                        {project.start_date && (
                                                            <div className="flex items-center gap-1">
                                                                <Calendar className="w-3 h-3" />
                                                                {formatDate(project.start_date)}
                                                                {project.end_date && ` → ${formatDate(project.end_date)}`}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            {/* Progress bar */}
                                            {project.budget > 0 && (
                                                <div className="mt-4">
                                                    <div className="flex items-center justify-between text-sm mb-1">
                                                        <span className="text-slate-500">Avancement facturation</span>
                                                        <span className="font-medium">{progress}%</span>
                                                    </div>
                                                    <Progress value={progress} className="h-2" />
                                                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                                                        <span>Facturé: {formatCurrency(project.total_invoiced)}</span>
                                                        <span>Budget: {formatCurrency(project.budget)}</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        
                                        {/* Actions */}
                                        <div className="flex items-center gap-2 md:flex-col md:items-end">
                                            <div className="text-right hidden md:block">
                                                <p className="text-2xl font-bold text-slate-900">
                                                    {formatCurrency(project.budget)}
                                                </p>
                                                <p className="text-xs text-slate-500">Budget</p>
                                            </div>
                                            
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="outline" size="icon">
                                                        <MoreVertical className="w-4 h-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem onClick={() => openEditModal(project)}>
                                                        <Edit2 className="w-4 h-4 mr-2" />
                                                        Modifier
                                                    </DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem onClick={() => navigate(`/devis/new?project_id=${project.id}`)}>
                                                        <FileText className="w-4 h-4 mr-2" />
                                                        Créer un devis
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => navigate(`/factures/new?project_id=${project.id}`)}>
                                                        <Receipt className="w-4 h-4 mr-2" />
                                                        Créer une facture
                                                    </DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    {project.status !== "in_progress" && (
                                                        <DropdownMenuItem onClick={() => handleStatusChange(project, "in_progress")}>
                                                            <Play className="w-4 h-4 mr-2 text-green-600" />
                                                            Démarrer
                                                        </DropdownMenuItem>
                                                    )}
                                                    {project.status === "in_progress" && (
                                                        <DropdownMenuItem onClick={() => handleStatusChange(project, "on_hold")}>
                                                            <Pause className="w-4 h-4 mr-2 text-amber-600" />
                                                            Mettre en pause
                                                        </DropdownMenuItem>
                                                    )}
                                                    {project.status !== "completed" && (
                                                        <DropdownMenuItem onClick={() => handleStatusChange(project, "completed")}>
                                                            <CheckCircle className="w-4 h-4 mr-2 text-slate-600" />
                                                            Terminer
                                                        </DropdownMenuItem>
                                                    )}
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem 
                                                        onClick={() => {
                                                            setSelectedProject(project);
                                                            setShowDeleteDialog(true);
                                                        }}
                                                        className="text-red-600"
                                                    >
                                                        <Trash2 className="w-4 h-4 mr-2" />
                                                        Supprimer
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}

            {/* Create Modal */}
            <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <Plus className="w-5 h-5 text-orange-600" />
                            Nouveau chantier
                        </DialogTitle>
                        <DialogDescription>
                            Créez un nouveau projet de construction
                        </DialogDescription>
                    </DialogHeader>
                    
                    <div className="space-y-6 py-4">
                        {/* Basic Info */}
                        <div className="space-y-4">
                            <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                <Building2 className="w-4 h-4" />
                                Informations générales
                            </h3>
                            
                            <div className="space-y-2">
                                <Label htmlFor="project_name">Nom du chantier *</Label>
                                <Input
                                    id="project_name"
                                    placeholder="Ex: Rénovation appartement Paris 15"
                                    value={formData.project_name}
                                    onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                                    data-testid="project-name"
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label htmlFor="description">Description</Label>
                                <Textarea
                                    id="description"
                                    placeholder="Description du projet..."
                                    value={formData.description}
                                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                                    rows={2}
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label htmlFor="client_id">Client</Label>
                                <Select 
                                    value={formData.client_id} 
                                    onValueChange={(v) => setFormData({...formData, client_id: v})}
                                >
                                    <SelectTrigger data-testid="project-client">
                                        <SelectValue placeholder="Sélectionner un client" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="none">Aucun client</SelectItem>
                                        {clients.map((client) => (
                                            <SelectItem key={client.id} value={client.id}>
                                                {client.company_name || client.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        
                        {/* Location */}
                        <div className="space-y-4">
                            <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                <MapPin className="w-4 h-4" />
                                Localisation
                            </h3>
                            
                            <div className="space-y-2">
                                <Label htmlFor="address">Adresse du chantier</Label>
                                <Input
                                    id="address"
                                    placeholder="123 rue de la construction"
                                    value={formData.address}
                                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                                />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="postal_code">Code postal</Label>
                                    <Input
                                        id="postal_code"
                                        placeholder="75015"
                                        value={formData.postal_code}
                                        onChange={(e) => setFormData({...formData, postal_code: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="city">Ville</Label>
                                    <Input
                                        id="city"
                                        placeholder="Paris"
                                        value={formData.city}
                                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                        
                        {/* Timeline */}
                        <div className="space-y-4">
                            <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                <Calendar className="w-4 h-4" />
                                Planning
                            </h3>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="start_date">Date de début</Label>
                                    <Input
                                        id="start_date"
                                        type="date"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="end_date">Date de fin prévue</Label>
                                    <Input
                                        id="end_date"
                                        type="date"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                        
                        {/* Budget */}
                        <div className="space-y-4">
                            <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                <Euro className="w-4 h-4" />
                                Budget
                            </h3>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="budget">Budget total (€)</Label>
                                    <Input
                                        id="budget"
                                        type="number"
                                        min="0"
                                        step="100"
                                        value={formData.budget}
                                        onChange={(e) => setFormData({...formData, budget: e.target.value})}
                                        data-testid="project-budget"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="estimated_cost">Coût estimé (€)</Label>
                                    <Input
                                        id="estimated_cost"
                                        type="number"
                                        min="0"
                                        step="100"
                                        value={formData.estimated_cost}
                                        onChange={(e) => setFormData({...formData, estimated_cost: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                        
                        {/* BTP Specific */}
                        <div className="space-y-4">
                            <h3 className="font-medium text-slate-900 flex items-center gap-2">
                                <FileText className="w-4 h-4" />
                                Documents BTP
                            </h3>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="permit_number">N° permis de construire</Label>
                                    <Input
                                        id="permit_number"
                                        placeholder="PC XXXXX"
                                        value={formData.permit_number}
                                        onChange={(e) => setFormData({...formData, permit_number: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="insurance_number">N° assurance décennale</Label>
                                    <Input
                                        id="insurance_number"
                                        placeholder="DEC XXXXX"
                                        value={formData.insurance_number}
                                        onChange={(e) => setFormData({...formData, insurance_number: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleCreate}
                            disabled={saving}
                            className="bg-orange-600 hover:bg-orange-700"
                            data-testid="save-project-btn"
                        >
                            {saving ? "Création..." : "Créer le chantier"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Edit Modal */}
            <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
                            <Edit2 className="w-5 h-5 text-orange-600" />
                            Modifier le chantier
                        </DialogTitle>
                    </DialogHeader>
                    
                    <div className="space-y-6 py-4">
                        {/* Same form fields as create modal */}
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label>Nom du chantier *</Label>
                                <Input
                                    value={formData.project_name}
                                    onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                                />
                            </div>
                            
                            <div className="space-y-2">
                                <Label>Description</Label>
                                <Textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                                    rows={2}
                                />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Client</Label>
                                    <Select 
                                        value={formData.client_id} 
                                        onValueChange={(v) => setFormData({...formData, client_id: v})}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Sélectionner" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="none">Aucun client</SelectItem>
                                            {clients.map((client) => (
                                                <SelectItem key={client.id} value={client.id}>
                                                    {client.company_name || client.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Statut</Label>
                                    <Select 
                                        value={formData.status} 
                                        onValueChange={(v) => setFormData({...formData, status: v})}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {Object.entries(PROJECT_STATUSES).map(([key, { label }]) => (
                                                <SelectItem key={key} value={key}>{label}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            
                            <div className="space-y-2">
                                <Label>Adresse</Label>
                                <Input
                                    value={formData.address}
                                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                                />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Code postal</Label>
                                    <Input
                                        value={formData.postal_code}
                                        onChange={(e) => setFormData({...formData, postal_code: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Ville</Label>
                                    <Input
                                        value={formData.city}
                                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                                    />
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Date de début</Label>
                                    <Input
                                        type="date"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Date de fin</Label>
                                    <Input
                                        type="date"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                                    />
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Budget (€)</Label>
                                    <Input
                                        type="number"
                                        min="0"
                                        value={formData.budget}
                                        onChange={(e) => setFormData({...formData, budget: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Coût estimé (€)</Label>
                                    <Input
                                        type="number"
                                        min="0"
                                        value={formData.estimated_cost}
                                        onChange={(e) => setFormData({...formData, estimated_cost: e.target.value})}
                                    />
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>N° permis</Label>
                                    <Input
                                        value={formData.permit_number}
                                        onChange={(e) => setFormData({...formData, permit_number: e.target.value})}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>N° assurance</Label>
                                    <Input
                                        value={formData.insurance_number}
                                        onChange={(e) => setFormData({...formData, insurance_number: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEditModal(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleUpdate}
                            disabled={saving}
                            className="bg-orange-600 hover:bg-orange-700"
                        >
                            {saving ? "Enregistrement..." : "Enregistrer"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation */}
            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Supprimer ce chantier ?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Cette action est irréversible. Le chantier "{selectedProject?.project_name}" et toutes ses données associées seront supprimés.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Annuler</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-red-600 hover:bg-red-700"
                        >
                            Supprimer
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
