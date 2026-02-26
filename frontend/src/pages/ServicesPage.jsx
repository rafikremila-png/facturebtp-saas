import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Globe, 
  CreditCard, 
  FileText, 
  Monitor,
  Star,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Upload,
  Phone,
  Mail,
  Building,
  MessageSquare,
  ShoppingBag,
  Send,
  Settings
} from 'lucide-react';

const SERVICE_ICONS = {
  Globe: Globe,
  CreditCard: CreditCard,
  FileText: FileText,
  Settings: Monitor,
};

const STATUS_CONFIG = {
  new: { label: 'Nouveau', color: 'bg-blue-100 text-blue-800', icon: AlertCircle },
  contacted: { label: 'Contacté', color: 'bg-yellow-100 text-yellow-800', icon: Phone },
  in_progress: { label: 'En cours', color: 'bg-purple-100 text-purple-800', icon: Clock },
  completed: { label: 'Terminé', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  cancelled: { label: 'Annulé', color: 'bg-red-100 text-red-800', icon: XCircle },
};

const ICON_COLORS = {
  website_visibility: 'bg-orange-100 text-orange-600',
  business_cards: 'bg-orange-100 text-orange-600',
  flyers_marketing: 'bg-orange-100 text-orange-600',
  it_support: 'bg-orange-100 text-orange-600',
};

export default function ServicesPage() {
  const { user } = useAuth();
  const [catalog, setCatalog] = useState({});
  const [myRequests, setMyRequests] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState(null);
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('services');
  
  // Form state
  const [formData, setFormData] = useState({
    quantity: '',
    urgency: 'standard',
    message: '',
    logo: null,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [catalogRes, requestsRes, settingsRes] = await Promise.all([
        api.get('/services/catalog'),
        api.get('/services/requests/me'),
        api.get('/settings'),
      ]);
      setCatalog(catalogRes.data);
      setMyRequests(requestsRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestService = (service, categoryName) => {
    setSelectedService({ ...service, categoryName });
    setFormData({
      quantity: '',
      urgency: 'standard',
      message: '',
      logo: null,
    });
    setShowRequestModal(true);
  };

  const handleSubmitRequest = async () => {
    if (!selectedService) return;
    
    try {
      setSubmitting(true);
      
      let logoBase64 = null;
      if (formData.logo) {
        logoBase64 = await convertToBase64(formData.logo);
      }
      
      await api.post('/services/request', {
        service_type: selectedService.name,
        service_category: selectedService.categoryName,
        company_name: settings?.company_name || user?.company_name || '',
        contact_email: user?.email || '',
        phone: user?.phone || settings?.phone || '',
        quantity: formData.quantity ? parseInt(formData.quantity) : null,
        urgency: formData.urgency,
        message: formData.message || null,
        logo_base64: logoBase64,
      });
      
      toast.success('Demande envoyée avec succès !');
      setShowRequestModal(false);
      
      // Refresh requests
      const requestsRes = await api.get('/services/requests/me');
      setMyRequests(requestsRes.data);
      setActiveTab('requests');
      
    } catch (error) {
      console.error('Error submitting request:', error);
      toast.error('Erreur lors de l\'envoi de la demande');
    } finally {
      setSubmitting(false);
    }
  };

  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const renderServiceCard = (service, categoryName) => {
    const isRecommended = service.recommended;
    
    return (
      <Card 
        key={service.id} 
        className={`relative overflow-hidden transition-all hover:shadow-lg bg-white ${
          isRecommended ? 'border-2 border-orange-400' : 'border border-gray-200'
        }`}
      >
        {isRecommended && (
          <div className="absolute top-3 right-3">
            <Badge className="bg-orange-100 text-orange-600 border-orange-300 flex items-center gap-1 text-xs font-medium">
              <Star className="h-3 w-3 fill-orange-500" />
              Recommandé
            </Badge>
          </div>
        )}
        <CardContent className="p-5">
          <h3 className="font-semibold text-gray-900 text-base mb-1 pr-24">{service.name}</h3>
          <p className="text-sm text-gray-500 mb-4">{service.description}</p>
          
          <div className="flex items-end justify-between">
            <div>
              <p className="text-xs text-gray-400 mb-1">À partir de</p>
              <div className="text-2xl font-bold text-gray-900">
                {service.price} €
              </div>
            </div>
            <Button 
              onClick={() => handleRequestService(service, categoryName)}
              className="bg-orange-500 hover:bg-orange-600 text-white flex items-center gap-2"
              data-testid={`request-${service.id}`}
            >
              <Send className="h-4 w-4" />
              Demandeur
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderCategory = (categoryKey, category) => {
    const IconComponent = SERVICE_ICONS[category.icon] || Monitor;
    const iconColorClass = ICON_COLORS[categoryKey] || 'bg-orange-100 text-orange-600';
    
    return (
      <div key={categoryKey} className="space-y-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${iconColorClass}`}>
            <IconComponent className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">{category.name}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {category.services.map(service => renderServiceCard(service, category.name))}
        </div>
      </div>
    );
  };

  const renderMyRequests = () => {
    if (myRequests.length === 0) {
      return (
        <Card className="bg-white">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium mb-2 text-gray-900">Aucune demande</h3>
            <p className="text-gray-500 text-center">
              Vous n'avez pas encore fait de demande de service.
            </p>
            <Button 
              className="mt-4 bg-orange-500 hover:bg-orange-600"
              onClick={() => setActiveTab('services')}
            >
              Découvrir nos services
            </Button>
          </CardContent>
        </Card>
      );
    }

    return (
      <div className="space-y-4">
        {myRequests.map(request => {
          const statusConfig = STATUS_CONFIG[request.status] || STATUS_CONFIG.new;
          const StatusIcon = statusConfig.icon;
          
          return (
            <Card key={request.id} className="bg-white">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-gray-900">{request.service_type}</h3>
                    <p className="text-sm text-gray-500">{request.service_category}</p>
                    {request.message && (
                      <p className="text-sm mt-2 text-gray-600">"{request.message}"</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge className={statusConfig.color}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {statusConfig.label}
                    </Badge>
                    <span className="text-xs text-gray-400">
                      {new Date(request.created_at).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {request.urgency === 'express' ? 'Express' : 'Standard'}
                  </span>
                  {request.quantity && (
                    <span>Quantité: {request.quantity}</span>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
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
    <div className="space-y-6 bg-gray-50 min-h-screen p-6" data-testid="services-page">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ShoppingBag className="h-7 w-7 text-gray-900" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Services Pro</h1>
          <p className="text-gray-500 text-sm">
            Services pour professionnels développer votre activité BTP
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setActiveTab('services')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === 'services' 
              ? 'bg-white text-gray-900 shadow-sm border border-gray-200' 
              : 'text-gray-500 hover:bg-gray-100'
          }`}
          data-testid="tab-services"
        >
          <Settings className="h-4 w-4" />
          Services
        </button>
        <button
          onClick={() => setActiveTab('requests')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === 'requests' 
              ? 'bg-white text-gray-900 shadow-sm border border-gray-200' 
              : 'text-gray-500 hover:bg-gray-100'
          }`}
          data-testid="tab-requests"
        >
          <Clock className="h-4 w-4" />
          Mes demandes
          {myRequests.length > 0 && (
            <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
              {myRequests.length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      {activeTab === 'services' ? (
        <div className="space-y-8">
          {/* Website Banner */}
          {settings && !settings.website && (
            <Card className="bg-gradient-to-r from-orange-50 to-amber-50 border-orange-200">
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-full">
                    <Globe className="h-5 w-5 text-orange-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Vous n'avez pas encore de site web professionnel</h3>
                    <p className="text-sm text-gray-500">
                      Augmentez votre visibilité et attirez plus de clients
                    </p>
                  </div>
                </div>
                <Button 
                  onClick={() => {
                    const webService = catalog.website_visibility?.services[0];
                    if (webService) {
                      handleRequestService(webService, 'Sites Web et Visibilité');
                    }
                  }}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  Créer mon site
                </Button>
              </CardContent>
            </Card>
          )}
          
          {Object.entries(catalog).map(([key, category]) => renderCategory(key, category))}
        </div>
      ) : (
        renderMyRequests()
      )}

      {/* Request Modal */}
      <Dialog open={showRequestModal} onOpenChange={setShowRequestModal}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Demander un service</DialogTitle>
            <DialogDescription>
              {selectedService?.name} - {selectedService?.categoryName}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Company Info (auto-filled) */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Entreprise
                </Label>
                <Input 
                  value={settings?.company_name || user?.company_name || ''} 
                  disabled 
                  className="bg-gray-50"
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email
                </Label>
                <Input 
                  value={user?.email || ''} 
                  disabled 
                  className="bg-gray-50"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Téléphone
              </Label>
              <Input 
                value={user?.phone || settings?.phone || ''} 
                disabled 
                className="bg-gray-50"
              />
            </div>

            {/* Quantity (for printing services) */}
            {(selectedService?.id?.includes('print') || selectedService?.id?.includes('pack')) && (
              <div className="space-y-2">
                <Label>Quantité (optionnel)</Label>
                <Input 
                  type="number"
                  placeholder="Ex: 500, 1000..."
                  value={formData.quantity}
                  onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                />
              </div>
            )}

            {/* Urgency */}
            <div className="space-y-2">
              <Label>Urgence</Label>
              <Select 
                value={formData.urgency} 
                onValueChange={(value) => setFormData({...formData, urgency: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="standard">Standard (délai normal)</SelectItem>
                  <SelectItem value="express">Express (prioritaire)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Message */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Message (optionnel)
              </Label>
              <Textarea 
                placeholder="Décrivez votre besoin ou ajoutez des précisions..."
                value={formData.message}
                onChange={(e) => setFormData({...formData, message: e.target.value})}
                rows={3}
              />
            </div>

            {/* Logo Upload */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Logo (optionnel)
              </Label>
              <Input 
                type="file"
                accept="image/*"
                onChange={(e) => setFormData({...formData, logo: e.target.files[0]})}
              />
              {formData.logo && (
                <p className="text-xs text-gray-500">
                  Fichier sélectionné: {formData.logo.name}
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRequestModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSubmitRequest} 
              disabled={submitting}
              className="bg-orange-500 hover:bg-orange-600"
              data-testid="submit-request"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Envoi...
                </>
              ) : (
                'Envoyer la demande'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
