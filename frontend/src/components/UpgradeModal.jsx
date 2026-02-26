import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Crown, AlertTriangle, Zap } from 'lucide-react';

export default function UpgradeModal({ 
  open, 
  onOpenChange, 
  title = "Mise à niveau requise",
  message = "Veuillez mettre à niveau votre abonnement pour continuer.",
  type = "limit" // "limit" | "expired" | "error"
}) {
  const icons = {
    limit: <Crown className="h-12 w-12 text-orange-500" />,
    expired: <AlertTriangle className="h-12 w-12 text-red-500" />,
    error: <AlertTriangle className="h-12 w-12 text-gray-500" />,
  };

  const buttonColors = {
    limit: "bg-orange-500 hover:bg-orange-600",
    expired: "bg-red-500 hover:bg-red-600",
    error: "bg-gray-500 hover:bg-gray-600",
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader className="text-center">
          <div className="flex justify-center mb-4">
            {icons[type] || icons.limit}
          </div>
          <DialogTitle className="text-xl text-center">{title}</DialogTitle>
          <DialogDescription className="text-center pt-2">
            {message}
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <h4 className="font-medium text-sm text-gray-700">Avantages Premium :</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-orange-500" />
                Factures illimitées
              </li>
              <li className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-orange-500" />
                Devis illimités
              </li>
              <li className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-orange-500" />
                Support prioritaire
              </li>
              <li className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-orange-500" />
                Export comptable
              </li>
            </ul>
          </div>
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            className="w-full sm:w-auto"
          >
            Plus tard
          </Button>
          <Button 
            className={`w-full sm:w-auto ${buttonColors[type] || buttonColors.limit}`}
            onClick={() => {
              // TODO: Navigate to upgrade page when Stripe is integrated
              window.location.href = '/parametres';
            }}
          >
            <Crown className="h-4 w-4 mr-2" />
            Mettre à niveau
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
