import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
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
  FileText,
  Filter,
  RefreshCw,
  MessageSquare,
  Calendar,
  Image,
  Zap
} from 'lucide-react';

const STATUS_CONFIG = {
  new: { label: 'Nouveau', color: 'bg-blue-100 text-blue-800', icon: AlertCircle },
  contacted: { label: 'Contacté', color: 'bg-yellow-100 text-yellow-800', icon: Phone },
  in_progress: { label: 'En cours', color: 'bg-purple-100 text-purple-800', icon: Clock },
  completed: { label: 'Terminé', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  cancelled: { label: 'Annulé', color: 'bg-red-100 text-red-800', icon: XCircle },
};

export default function ServiceRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [adminNotes, setAdminNotes] = useState('');

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [requestsRes, statsRes] = await Promise.all([
        api.get('/services/requests', {
          params: statusFilter !== 'all' ? { status: statusFilter } : {}
        }),
        api.get('/services/stats'),
      ]);
      setRequests(requestsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (request) => {
    try {
      const res = await api.get(`/services/requests/${request.id}`);
      setSelectedRequest(res.data);
      setNewStatus(res.data.status);
      setAdminNotes(res.data.admin_notes || '');
      setShowDetailModal(true);
    } catch (error) {
      console.error('Error loading request details:', error);
      toast.error('Erreur lors du chargement des détails');
    }
  };

  const handleUpdateStatus = async () => {
    if (!selectedRequest || !newStatus) return;
    
    try {
      setUpdating(true);
      await api.put(`/services/requests/${selectedRequest.id}/status`, {
        status: newStatus,
        admin_notes: adminNotes || null,
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

  const renderStatsCards = () => {
    if (!stats) return null;
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-muted-foreground">Total</div>
          </CardContent>
        </Card>
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-700">{stats.new}</div>
            <div className="text-sm text-blue-600">Nouveaux</div>
          </CardContent>
        </Card>
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-700">{stats.contacted}</div>
            <div className="text-sm text-yellow-600">Contactés</div>
          </CardContent>
        </Card>
        <Card className="border-purple-200 bg-purple-50">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-purple-700">{stats.in_progress}</div>
            <div className="text-sm text-purple-600">En cours</div>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-700">{stats.completed}</div>
            <div className="text-sm text-green-600">Terminés</div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="service-requests-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Demandes de Services</h1>
          <p className="text-muted-foreground mt-1">
            Gérez les demandes de services professionnels
          </p>
        </div>
        <Button variant="outline" onClick={loadData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Stats */}
      {renderStatsCards()}

      {/* Filter */}
      <div className="flex items-center gap-4">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filtrer par statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            <SelectItem value="new">Nouveaux</SelectItem>
            <SelectItem value="contacted">Contactés</SelectItem>
            <SelectItem value="in_progress">En cours</SelectItem>
            <SelectItem value="completed">Terminés</SelectItem>
            <SelectItem value="cancelled">Annulés</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Requests List */}
      {requests.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Aucune demande</h3>
            <p className="text-muted-foreground">
              {statusFilter !== 'all' 
                ? 'Aucune demande avec ce statut' 
                : 'Aucune demande de service pour le moment'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map(request => {
            const statusConfig = STATUS_CONFIG[request.status] || STATUS_CONFIG.new;
            const StatusIcon = statusConfig.icon;
            
            return (
              <Card key={request.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-lg">{request.service_type}</h3>
                        <Badge className={statusConfig.color}>
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                        {request.urgency === 'express' && (
                          <Badge variant="destructive" className="flex items-center gap-1">
                            <Zap className="h-3 w-3" />
                            Express
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{request.service_category}</p>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                        <div className="flex items-center gap-2">
                          <Building className="h-4 w-4 text-muted-foreground" />
                          <span>{request.company_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span>{request.contact_email}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span>{request.phone}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span>{new Date(request.created_at).toLocaleDateString('fr-FR')}</span>
                        </div>
                      </div>
                      
                      {request.message && (
                        <div className="flex items-start gap-2 mt-2 p-2 bg-gray-50 rounded">
                          <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5" />
                          <p className="text-sm text-gray-600">"{request.message}"</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col items-end gap-2 ml-4">
                      {request.has_logo && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Image className="h-3 w-3" />
                          Logo
                        </Badge>
                      )}
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleViewDetails(request)}
                        data-testid={`view-request-${request.id}`}
                      >
                        Gérer
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Détails de la demande</DialogTitle>
            <DialogDescription>
              {selectedRequest?.service_type} - {selectedRequest?.service_category}
            </DialogDescription>
          </DialogHeader>
          
          {selectedRequest && (
            <div className="space-y-4 py-4">
              {/* Contact Info */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Informations de contact</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Entreprise</div>
                    <div className="font-medium">{selectedRequest.company_name}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Email</div>
                    <div className="font-medium">{selectedRequest.contact_email}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Téléphone</div>
                    <div className="font-medium">{selectedRequest.phone}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Date</div>
                    <div className="font-medium">
                      {new Date(selectedRequest.created_at).toLocaleString('fr-FR')}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Request Details */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Détails de la demande</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Urgence</span>
                    <Badge variant={selectedRequest.urgency === 'express' ? 'destructive' : 'secondary'}>
                      {selectedRequest.urgency === 'express' ? 'Express' : 'Standard'}
                    </Badge>
                  </div>
                  {selectedRequest.quantity && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Quantité</span>
                      <span className="font-medium">{selectedRequest.quantity}</span>
                    </div>
                  )}
                  {selectedRequest.message && (
                    <div>
                      <div className="text-muted-foreground mb-1">Message</div>
                      <div className="p-2 bg-gray-50 rounded text-gray-700">
                        {selectedRequest.message}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Status Update */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Mettre à jour le statut</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Select value={newStatus} onValueChange={setNewStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new">Nouveau</SelectItem>
                      <SelectItem value="contacted">Contacté</SelectItem>
                      <SelectItem value="in_progress">En cours</SelectItem>
                      <SelectItem value="completed">Terminé</SelectItem>
                      <SelectItem value="cancelled">Annulé</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <div>
                    <label className="text-sm text-muted-foreground">Notes admin (optionnel)</label>
                    <Textarea 
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      placeholder="Notes internes..."
                      rows={2}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailModal(false)}>
              Fermer
            </Button>
            <Button 
              onClick={handleUpdateStatus} 
              disabled={updating}
              className="bg-orange-500 hover:bg-orange-600"
              data-testid="update-status"
            >
              {updating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Mise à jour...
                </>
              ) : (
                'Mettre à jour'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
