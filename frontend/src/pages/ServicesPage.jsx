import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
  Settings, 
  Star,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Upload,
  Euro,
  Phone,
  Mail,
  Building,
  MessageSquare
} from 'lucide-react';

const SERVICE_ICONS = {
  Globe: Globe,
  CreditCard: CreditCard,
  FileText: FileText,
  Settings: Settings,
};

const STATUS_CONFIG = {
  new: { label: 'Nouveau', color: 'bg-blue-100 text-blue-800', icon: AlertCircle },
  contacted: { label: 'Contacté', color: 'bg-yellow-100 text-yellow-800', icon: Phone },
  in_progress: { label: 'En cours', color: 'bg-purple-100 text-purple-800', icon: Clock },
  completed: { label: 'Terminé', color: 'bg-green-100 text-green-800', icon: CheckCircle },
  cancelled: { label: 'Annulé', color: 'bg-red-100 text-red-800', icon: XCircle },
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
        className={`relative overflow-hidden transition-all hover:shadow-lg ${
          isRecommended ? 'border-2 border-orange-500 shadow-orange-100' : ''
        }`}
      >
        {isRecommended && (
          <div className="absolute top-0 right-0 bg-orange-500 text-white px-3 py-1 text-xs font-semibold flex items-center gap-1">
            <Star className="h-3 w-3" />
            Recommandé
          </div>
        )}
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">{service.name}</CardTitle>
          <CardDescription>{service.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-2xl font-bold text-orange-600">
              <Euro className="h-5 w-5" />
              {service.price}
            </div>
            <Button 
              onClick={() => handleRequestService(service, categoryName)}
              className={isRecommended ? 'bg-orange-500 hover:bg-orange-600' : ''}
              data-testid={`request-${service.id}`}
            >
              Demander
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">{service.price_label}</p>
        </CardContent>
      </Card>
    );
  };

  const renderCategory = (categoryKey, category) => {
    const IconComponent = SERVICE_ICONS[category.icon] || Settings;
    
    return (
      <div key={categoryKey} className="space-y-4">
        <div className="flex items-center gap-3 border-b pb-2">
          <div className="p-2 bg-orange-100 rounded-lg">
            <IconComponent className="h-5 w-5 text-orange-600" />
          </div>
          <h2 className="text-xl font-semibold">{category.name}</h2>
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
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Aucune demande</h3>
            <p className="text-muted-foreground text-center">
              Vous n'avez pas encore fait de demande de service.
            </p>
            <Button 
              className="mt-4"
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
            <Card key={request.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold">{request.service_type}</h3>
                    <p className="text-sm text-muted-foreground">{request.service_category}</p>
                    {request.message && (
                      <p className="text-sm mt-2 text-gray-600">"{request.message}"</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge className={statusConfig.color}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {statusConfig.label}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(request.created_at).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
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
    <div className="space-y-6" data-testid="services-page">
      {/* Header */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold">Services Pro</h1>
        <p className="text-muted-foreground mt-1">
          Services professionnels pour développer votre activité BTP
        </p>
      </div>

      {/* Website Banner */}
      {settings && !settings.website && (
        <Card className="bg-gradient-to-r from-orange-50 to-amber-50 border-orange-200">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-full">
                <Globe className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-medium">Vous n'avez pas encore de site web professionnel</h3>
                <p className="text-sm text-muted-foreground">
                  Augmentez votre visibilité et attirez plus de clients
                </p>
              </div>
            </div>
            <Button 
              onClick={() => {
                const webService = catalog.website_visibility?.services[0];
                if (webService) {
                  handleRequestService(webService, 'Site Web & Visibilité');
                }
              }}
              className="bg-orange-500 hover:bg-orange-600"
            >
              Créer mon site
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="services" data-testid="tab-services">
            Services
          </TabsTrigger>
          <TabsTrigger value="requests" data-testid="tab-requests">
            Mes demandes
            {myRequests.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {myRequests.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="services" className="space-y-8 mt-6">
          {Object.entries(catalog).map(([key, category]) => renderCategory(key, category))}
        </TabsContent>

        <TabsContent value="requests" className="mt-6">
          {renderMyRequests()}
        </TabsContent>
      </Tabs>

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
                <p className="text-xs text-muted-foreground">
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
