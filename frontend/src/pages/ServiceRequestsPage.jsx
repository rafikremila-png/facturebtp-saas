import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Phone,
  Mail,
  Building,
  Globe,
  Search,
  TrendingUp,
  Zap,
  Users,
  Palette,
  Filter,
  RefreshCw,
  MessageSquare,
  Calendar,
  ChevronRight,
  Plus,
  Send
} from 'lucide-react';
import { useAuth, ROLE_ADMIN, ROLE_SUPER_ADMIN } from "@/context/AuthContext";

// Status configuration with colors
const STATUS_CONFIG = {
  pending: { label: 'En attente', color: 'bg-orange-500 text-white', icon: Clock },
  in_progress: { label: 'En cours', color: 'bg-blue-500 text-white', icon: Loader2 },
  completed: { label: 'Terminé', color: 'bg-green-500 text-white', icon: CheckCircle },
  cancelled: { label: 'Annulé', color: 'bg-red-500 text-white', icon: XCircle },
};

// Icon mapping for categories
const CATEGORY_ICONS = {
  'Globe': Globe,
  'Search': Search,
  'TrendingUp': TrendingUp,
  'Zap': Zap,
  'Users': Users,
  'Palette': Palette,
};

export default function ServiceRequestsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === ROLE_ADMIN || user?.role === ROLE_SUPER_ADMIN;
  
  // Data states
  const [categories, setCategories] = useState([]);
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  
  // Modal states
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showNewRequestModal, setShowNewRequestModal] = useState(false);
  const [updating, setUpdating] = useState(false);
  
  // Admin update states
  const [newStatus, setNewStatus] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  
  // New request form states
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [requestForm, setRequestForm] = useState({
    company_name: '',
    contact_email: '',
    phone: '',
    message: '',
    quantity: 1,
    urgency: 'standard'
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter, categoryFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load categories
      const categoriesRes = await api.get('/service-categories');
      setCategories(categoriesRes.data);
      
      // Load requests based on user role
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (categoryFilter !== 'all') params.category_id = categoryFilter;
      
      const endpoint = isAdmin ? '/service-requests' : '/service-requests/me';
      const requestsRes = await api.get(endpoint, { params });
      setRequests(requestsRes.data);
      
      // Load stats for admin
      if (isAdmin) {
        try {
          const statsRes = await api.get('/service-requests/stats');
          setStats(statsRes.data);
        } catch (e) {
          // Stats endpoint might fail, ignore
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (request) => {
    setSelectedRequest(request);
    setNewStatus(request.status);
    setAdminNotes(request.admin_notes || '');
    setShowDetailModal(true);
  };

  const handleUpdateStatus = async () => {
    if (!selectedRequest || !newStatus) return;
    
    setUpdating(true);
    try {
      await api.put(`/service-requests/${selectedRequest.id}/status`, {
        status: newStatus,
        admin_notes: adminNotes
      });
      toast.success('Statut mis à jour');
      setShowDetailModal(false);
      loadData();
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setUpdating(false);
    }
  };

  const handleSelectCategory = (category) => {
    setSelectedCategory(category);
    setSelectedService(null);
  };

  const handleSelectService = (service) => {
    setSelectedService(service);
  };

  const handleSubmitRequest = async () => {
    if (!selectedCategory || !selectedService) {
      toast.error('Veuillez sélectionner une catégorie et un service');
      return;
    }
    
    if (!requestForm.company_name || !requestForm.contact_email || !requestForm.phone) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }
    
    setSubmitting(true);
    try {
      await api.post('/service-requests', {
        category_id: selectedCategory.id,
        service_id: selectedService.id,
        ...requestForm
      });
      
      toast.success('Demande envoyée avec succès');
      setShowNewRequestModal(false);
      resetNewRequestForm();
      loadData();
    } catch (error) {
      console.error('Error submitting request:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'envoi de la demande');
    } finally {
      setSubmitting(false);
    }
  };

  const resetNewRequestForm = () => {
    setSelectedCategory(null);
    setSelectedService(null);
    setRequestForm({
      company_name: '',
      contact_email: '',
      phone: '',
      message: '',
      quantity: 1,
      urgency: 'standard'
    });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCategoryIcon = (iconName) => {
    const IconComponent = CATEGORY_ICONS[iconName] || Globe;
    return IconComponent;
  };

  // Filtered requests
  const filteredRequests = requests;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="service-requests-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-['Barlow_Condensed'] flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-orange-600" />
            {isAdmin ? 'Gestion des demandes' : 'Mes demandes de service'}
          </h1>
          <p className="text-slate-500 mt-1">
            {isAdmin 
              ? `${requests.length} demande(s) - Gérez les demandes de services`
              : 'Demandez des services professionnels pour votre entreprise'
            }
          </p>
        </div>
        <Button 
          onClick={() => setShowNewRequestModal(true)}
          className="bg-orange-600 hover:bg-orange-700"
          data-testid="new-request-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nouvelle demande
        </Button>
      </div>

      {/* Admin Stats */}
      {isAdmin && stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                <p className="text-sm text-slate-500">Total</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-orange-200 bg-orange-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">{stats.pending}</p>
                <p className="text-sm text-orange-700">En attente</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{stats.in_progress}</p>
                <p className="text-sm text-blue-700">En cours</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
                <p className="text-sm text-green-700">Terminées</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{stats.cancelled}</p>
                <p className="text-sm text-red-700">Annulées</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Label className="text-xs text-slate-500 mb-2 block">Filtrer par statut</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger data-testid="filter-status">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Tous les statuts" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous les statuts</SelectItem>
                  <SelectItem value="pending">En attente</SelectItem>
                  <SelectItem value="in_progress">En cours</SelectItem>
                  <SelectItem value="completed">Terminé</SelectItem>
                  <SelectItem value="cancelled">Annulé</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Label className="text-xs text-slate-500 mb-2 block">Filtrer par catégorie</Label>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger data-testid="filter-category">
                  <SelectValue placeholder="Toutes les catégories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Toutes les catégories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={loadData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Actualiser
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Requests List */}
      {filteredRequests.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                Aucune demande
              </h3>
              <p className="text-slate-500 mb-4">
                {statusFilter !== 'all' || categoryFilter !== 'all'
                  ? 'Aucune demande ne correspond aux filtres'
                  : 'Commencez par créer une nouvelle demande de service'
                }
              </p>
              <Button 
                onClick={() => setShowNewRequestModal(true)}
                className="bg-orange-600 hover:bg-orange-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nouvelle demande
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredRequests.map((request) => {
            const statusInfo = STATUS_CONFIG[request.status] || STATUS_CONFIG.pending;
            const StatusIcon = statusInfo.icon;
            
            return (
              <Card 
                key={request.id} 
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleViewDetails(request)}
                data-testid={`request-${request.id}`}
              >
                <CardContent className="pt-6">
                  <div className="flex flex-col md:flex-row md:items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-2">
                        <h3 className="font-semibold text-slate-900">
                          {request.service_name || 'Service'}
                        </h3>
                        <Badge className={statusInfo.color} data-testid={`status-badge-${request.id}`}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusInfo.label}
                        </Badge>
                        {request.urgency === 'express' && (
                          <Badge className="bg-purple-500 text-white">Express</Badge>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-slate-500 flex-wrap">
                        <span className="flex items-center gap-1">
                          <Building className="w-3 h-3" />
                          {request.company_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Mail className="w-3 h-3" />
                          {request.contact_email}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(request.created_at)}
                        </span>
                      </div>
                      
                      {request.message && (
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">
                          {request.message}
                        </p>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {request.service_price && (
                        <span className="text-lg font-bold text-orange-600">
                          {request.service_price}€
                        </span>
                      )}
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detail Modal (Admin) */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Barlow_Condensed'] text-xl">
              Détails de la demande
            </DialogTitle>
          </DialogHeader>
          
          {selectedRequest && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-500">Service</Label>
                  <p className="font-medium">{selectedRequest.service_name || 'N/A'}</p>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Statut actuel</Label>
                  <Badge className={STATUS_CONFIG[selectedRequest.status]?.color || 'bg-gray-500 text-white'}>
                    {STATUS_CONFIG[selectedRequest.status]?.label || selectedRequest.status}
                  </Badge>
                </div>
              </div>
              
              <div>
                <Label className="text-xs text-slate-500">Entreprise</Label>
                <p className="font-medium">{selectedRequest.company_name}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-500">Email</Label>
                  <p>{selectedRequest.contact_email}</p>
                </div>
                <div>
                  <Label className="text-xs text-slate-500">Téléphone</Label>
                  <p>{selectedRequest.phone}</p>
                </div>
              </div>
              
              {selectedRequest.message && (
                <div>
                  <Label className="text-xs text-slate-500">Message</Label>
                  <p className="text-sm">{selectedRequest.message}</p>
                </div>
              )}
              
              {isAdmin && (
                <>
                  <div className="border-t pt-4">
                    <Label htmlFor="newStatus">Changer le statut</Label>
                    <Select value={newStatus} onValueChange={setNewStatus}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">En attente</SelectItem>
                        <SelectItem value="in_progress">En cours</SelectItem>
                        <SelectItem value="completed">Terminé</SelectItem>
                        <SelectItem value="cancelled">Annulé</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="adminNotes">Notes admin</Label>
                    <Textarea
                      id="adminNotes"
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      placeholder="Notes internes..."
                      rows={3}
                    />
                  </div>
                </>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>
              Fermer
            </Button>
            {isAdmin && (
              <Button 
                onClick={handleUpdateStatus}
                disabled={updating}
                className="bg-orange-600 hover:bg-orange-700"
              >
                {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Mettre à jour
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Request Modal */}
      <Dialog open={showNewRequestModal} onOpenChange={setShowNewRequestModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
              <Plus className="w-5 h-5 text-orange-600" />
              Nouvelle demande de service
            </DialogTitle>
            <DialogDescription>
              Sélectionnez une catégorie, puis un service
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {/* Step indicator */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <div className={`flex items-center gap-2 ${!selectedCategory ? 'text-orange-600' : 'text-slate-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${!selectedCategory ? 'bg-orange-600 text-white' : 'bg-slate-200'}`}>1</div>
                <span className="text-sm font-medium">Catégorie</span>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-300" />
              <div className={`flex items-center gap-2 ${selectedCategory && !selectedService ? 'text-orange-600' : 'text-slate-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${selectedCategory && !selectedService ? 'bg-orange-600 text-white' : 'bg-slate-200'}`}>2</div>
                <span className="text-sm font-medium">Service</span>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-300" />
              <div className={`flex items-center gap-2 ${selectedService ? 'text-orange-600' : 'text-slate-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${selectedService ? 'bg-orange-600 text-white' : 'bg-slate-200'}`}>3</div>
                <span className="text-sm font-medium">Détails</span>
              </div>
            </div>

            {/* Step 1: Category Selection */}
            {!selectedCategory && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {categories.map((category) => {
                  const IconComponent = getCategoryIcon(category.icon);
                  return (
                    <Card 
                      key={category.id}
                      className="cursor-pointer hover:border-orange-500 hover:shadow-md transition-all"
                      onClick={() => handleSelectCategory(category)}
                    >
                      <CardContent className="pt-6 text-center">
                        <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                          <IconComponent className="w-6 h-6 text-orange-600" />
                        </div>
                        <h3 className="font-medium text-slate-900">{category.name}</h3>
                        <p className="text-xs text-slate-500 mt-1">{category.services?.length || 0} services</p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Step 2: Service Selection */}
            {selectedCategory && !selectedService && (
              <div>
                <Button 
                  variant="ghost" 
                  onClick={() => setSelectedCategory(null)}
                  className="mb-4"
                >
                  ← Retour aux catégories
                </Button>
                
                <h3 className="font-medium text-lg mb-4">{selectedCategory.name}</h3>
                
                <div className="space-y-3">
                  {selectedCategory.services?.map((service) => (
                    <Card 
                      key={service.id}
                      className={`cursor-pointer hover:border-orange-500 transition-all ${service.is_recommended ? 'border-orange-300 bg-orange-50' : ''}`}
                      onClick={() => handleSelectService(service)}
                    >
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium">{service.name}</h4>
                              {service.is_recommended && (
                                <Badge className="bg-orange-500 text-white text-xs">Recommandé</Badge>
                              )}
                            </div>
                            <p className="text-sm text-slate-500 mt-1">{service.description}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-orange-600">{service.price_label}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Request Details */}
            {selectedService && (
              <div>
                <Button 
                  variant="ghost" 
                  onClick={() => setSelectedService(null)}
                  className="mb-4"
                >
                  ← Retour aux services
                </Button>
                
                <Card className="mb-6 bg-orange-50 border-orange-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-500">{selectedCategory.name}</p>
                        <h4 className="font-medium">{selectedService.name}</h4>
                      </div>
                      <p className="font-bold text-orange-600">{selectedService.price_label}</p>
                    </div>
                  </CardContent>
                </Card>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="company_name">Nom de l'entreprise *</Label>
                    <Input
                      id="company_name"
                      value={requestForm.company_name}
                      onChange={(e) => setRequestForm({...requestForm, company_name: e.target.value})}
                      placeholder="Votre entreprise"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="contact_email">Email *</Label>
                      <Input
                        id="contact_email"
                        type="email"
                        value={requestForm.contact_email}
                        onChange={(e) => setRequestForm({...requestForm, contact_email: e.target.value})}
                        placeholder="email@exemple.fr"
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">Téléphone *</Label>
                      <Input
                        id="phone"
                        value={requestForm.phone}
                        onChange={(e) => setRequestForm({...requestForm, phone: e.target.value})}
                        placeholder="06 XX XX XX XX"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="message">Message (optionnel)</Label>
                    <Textarea
                      id="message"
                      value={requestForm.message}
                      onChange={(e) => setRequestForm({...requestForm, message: e.target.value})}
                      placeholder="Décrivez votre besoin..."
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label>Urgence</Label>
                    <Select 
                      value={requestForm.urgency} 
                      onValueChange={(v) => setRequestForm({...requestForm, urgency: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard</SelectItem>
                        <SelectItem value="express">Express (+30%)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowNewRequestModal(false);
              resetNewRequestForm();
            }}>
              Annuler
            </Button>
            {selectedService && (
              <Button 
                onClick={handleSubmitRequest}
                disabled={submitting}
                className="bg-orange-600 hover:bg-orange-700"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Envoyer la demande
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
