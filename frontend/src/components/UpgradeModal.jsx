import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Crown, AlertTriangle, Zap, FileText, TrendingUp } from 'lucide-react';

/**
 * Unified Upgrade Modal Component
 * Used for both quote and invoice limit reached scenarios
 */
export default function UpgradeModal({ 
  open, 
  onOpenChange, 
  title = "Mise à niveau requise",
  message = "Veuillez mettre à niveau votre abonnement pour continuer.",
  type = "limit", // "limit" | "expired" | "trial_expired" | "error"
  documentType = "document", // "devis" | "facture" | "document"
  usage = null, // { current: number, limit: number }
}) {
  const navigate = useNavigate();
  
  const icons = {
    limit: <Crown className="h-12 w-12 text-orange-500" />,
    expired: <AlertTriangle className="h-12 w-12 text-red-500" />,
    trial_expired: <AlertTriangle className="h-12 w-12 text-red-500" />,
    error: <AlertTriangle className="h-12 w-12 text-gray-500" />,
  };

  const buttonColors = {
    limit: "bg-orange-600 hover:bg-orange-700",
    expired: "bg-red-600 hover:bg-red-700",
    trial_expired: "bg-red-600 hover:bg-red-700",
    error: "bg-gray-500 hover:bg-gray-600",
  };

  // Build dynamic message if usage provided
  const displayMessage = usage 
    ? `Limite atteinte (${usage.current}/${usage.limit} ${documentType}${usage.limit > 1 ? 's' : ''}). Passez au plan supérieur pour continuer.`
    : message;

  const handleUpgrade = () => {
    onOpenChange(false);
    // Navigate to billing page (not settings)
    navigate('/facturation');
  };

  const handleViewPricing = () => {
    onOpenChange(false);
    navigate('/tarifs');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]" data-testid="upgrade-modal">
        <DialogHeader className="text-center">
          <div className="flex justify-center mb-4">
            {icons[type] || icons.limit}
          </div>
          <DialogTitle className="text-xl text-center" data-testid="upgrade-modal-title">
            {title}
          </DialogTitle>
          <DialogDescription className="text-center pt-2" data-testid="upgrade-modal-message">
            {displayMessage}
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-4 space-y-3 border border-orange-100">
            <h4 className="font-semibold text-sm text-gray-800">Passez au plan Pro :</h4>
            <ul className="text-sm text-gray-600 space-y-2">
              <li className="flex items-center gap-2">
                <div className="w-5 h-5 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Zap className="h-3 w-3 text-orange-600" />
                </div>
                <span>Devis et factures <strong>illimités</strong></span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-5 h-5 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <FileText className="h-3 w-3 text-orange-600" />
                </div>
                <span>Relances automatiques impayés</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-5 h-5 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="h-3 w-3 text-orange-600" />
                </div>
                <span>Export comptable CSV</span>
              </li>
            </ul>
            <div className="pt-2 border-t border-orange-200">
              <p className="text-center text-sm">
                <span className="text-gray-500">À partir de</span>{' '}
                <span className="text-2xl font-bold text-orange-600">19€</span>
                <span className="text-gray-500">/mois</span>
              </p>
            </div>
          </div>
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            className="w-full sm:w-auto"
            data-testid="upgrade-modal-later-btn"
          >
            Plus tard
          </Button>
          <Button 
            variant="outline"
            onClick={handleViewPricing}
            className="w-full sm:w-auto"
            data-testid="upgrade-modal-pricing-btn"
          >
            Voir les tarifs
          </Button>
          <Button 
            className={`w-full sm:w-auto ${buttonColors[type] || buttonColors.limit}`}
            onClick={handleUpgrade}
            data-testid="upgrade-modal-upgrade-btn"
          >
            <Crown className="h-4 w-4 mr-2" />
            Mettre à niveau
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
