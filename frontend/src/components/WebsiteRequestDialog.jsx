import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Globe, Briefcase, Target, Euro, Clock, CheckCircle } from "lucide-react";
import { toast } from "sonner";

const BUDGET_OPTIONS = [
    { value: "500-1000", label: "500 € - 1 000 €" },
    { value: "1000-2500", label: "1 000 € - 2 500 €" },
    { value: "2500-5000", label: "2 500 € - 5 000 €" },
    { value: "5000-10000", label: "5 000 € - 10 000 €" },
    { value: "10000+", label: "Plus de 10 000 €" },
    { value: "a-definir", label: "À définir" }
];

const TIMELINE_OPTIONS = [
    { value: "urgent", label: "Urgent (< 2 semaines)" },
    { value: "1-mois", label: "1 mois" },
    { value: "2-3-mois", label: "2-3 mois" },
    { value: "flexible", label: "Flexible" }
];

export default function WebsiteRequestDialog({ open, onOpenChange }) {
    const [step, setStep] = useState("form"); // form, success
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        activity_type: "",
        objective: "",
        budget: "",
        timeline: "",
        additional_notes: ""
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.activity_type || !formData.objective || !formData.budget || !formData.timeline) {
            toast.error("Veuillez remplir tous les champs obligatoires");
            return;
        }

        setLoading(true);
        try {
            await api.post("/website-requests", formData);
            setStep("success");
        } catch (error) {
            toast.error(error.response?.data?.detail || "Erreur lors de l'envoi de la demande");
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setStep("form");
        setFormData({
            activity_type: "",
            objective: "",
            budget: "",
            timeline: "",
            additional_notes: ""
        });
        onOpenChange(false);
    };

    const renderSuccessStep = () => (
        <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Demande envoyée !</h3>
            <p className="text-slate-500 mb-6">
                Nous avons bien reçu votre demande de création de site web. 
                Notre équipe vous contactera dans les 24-48h.
            </p>
            <Button onClick={handleClose} className="bg-orange-600 hover:bg-orange-700">
                Fermer
            </Button>
        </div>
    );

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="max-w-xl" data-testid="website-request-dialog">
                {step === "success" ? renderSuccessStep() : (
                    <>
                        <DialogHeader>
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                    <Globe className="w-5 h-5 text-orange-600" />
                                </div>
                                <div>
                                    <DialogTitle className="font-['Barlow_Condensed']">
                                        Demande de création de site web
                                    </DialogTitle>
                                    <DialogDescription>
                                        Décrivez votre projet et nous vous contacterons rapidement
                                    </DialogDescription>
                                </div>
                            </div>
                        </DialogHeader>

                        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                            <div className="space-y-2">
                                <Label htmlFor="activity_type" className="flex items-center gap-2">
                                    <Briefcase className="w-4 h-4 text-slate-400" />
                                    Type d'activité *
                                </Label>
                                <Input
                                    id="activity_type"
                                    placeholder="Ex: Maçonnerie, Plomberie, Électricité..."
                                    value={formData.activity_type}
                                    onChange={(e) => setFormData({ ...formData, activity_type: e.target.value })}
                                    required
                                    data-testid="activity-type-input"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="objective" className="flex items-center gap-2">
                                    <Target className="w-4 h-4 text-slate-400" />
                                    Objectif du site *
                                </Label>
                                <Textarea
                                    id="objective"
                                    placeholder="Décrivez ce que vous attendez de votre site web (vitrine, prise de RDV, devis en ligne...)"
                                    value={formData.objective}
                                    onChange={(e) => setFormData({ ...formData, objective: e.target.value })}
                                    rows={3}
                                    required
                                    data-testid="objective-input"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label className="flex items-center gap-2">
                                        <Euro className="w-4 h-4 text-slate-400" />
                                        Budget estimé *
                                    </Label>
                                    <Select
                                        value={formData.budget}
                                        onValueChange={(val) => setFormData({ ...formData, budget: val })}
                                    >
                                        <SelectTrigger data-testid="budget-select">
                                            <SelectValue placeholder="Sélectionner" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {BUDGET_OPTIONS.map((opt) => (
                                                <SelectItem key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label className="flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-slate-400" />
                                        Délai souhaité *
                                    </Label>
                                    <Select
                                        value={formData.timeline}
                                        onValueChange={(val) => setFormData({ ...formData, timeline: val })}
                                    >
                                        <SelectTrigger data-testid="timeline-select">
                                            <SelectValue placeholder="Sélectionner" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {TIMELINE_OPTIONS.map((opt) => (
                                                <SelectItem key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="notes">Notes additionnelles</Label>
                                <Textarea
                                    id="notes"
                                    placeholder="Informations complémentaires, inspirations, fonctionnalités souhaitées..."
                                    value={formData.additional_notes}
                                    onChange={(e) => setFormData({ ...formData, additional_notes: e.target.value })}
                                    rows={2}
                                    data-testid="notes-input"
                                />
                            </div>

                            <DialogFooter>
                                <Button type="button" variant="outline" onClick={handleClose}>
                                    Annuler
                                </Button>
                                <Button 
                                    type="submit" 
                                    disabled={loading}
                                    className="bg-orange-600 hover:bg-orange-700"
                                    data-testid="submit-request-btn"
                                >
                                    {loading ? "Envoi en cours..." : "Envoyer la demande"}
                                </Button>
                            </DialogFooter>
                        </form>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
