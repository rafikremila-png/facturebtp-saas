import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
    User, Building2, Scale, CreditCard, CheckCircle, XCircle, 
    ChevronRight, AlertCircle, TrendingUp, Award
} from "lucide-react";

const CATEGORY_INFO = {
    profil: { 
        label: "Profil", 
        icon: User, 
        color: "text-blue-600",
        bgColor: "bg-blue-100"
    },
    entreprise: { 
        label: "Entreprise", 
        icon: Building2, 
        color: "text-orange-600",
        bgColor: "bg-orange-100"
    },
    legal: { 
        label: "Légal", 
        icon: Scale, 
        color: "text-purple-600",
        bgColor: "bg-purple-100"
    },
    bancaire: { 
        label: "Bancaire", 
        icon: CreditCard, 
        color: "text-green-600",
        bgColor: "bg-green-100"
    }
};

export default function ProfileCompletionCard({ compact = false }) {
    const [completion, setCompletion] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadCompletion();
    }, []);

    const loadCompletion = async () => {
        try {
            const response = await api.get("/profile/completion");
            setCompletion(response.data);
        } catch (error) {
            console.error("Erreur chargement complétion:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Card>
                <CardContent className="py-8">
                    <div className="flex items-center justify-center">
                        <div className="spinner"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!completion) return null;

    const { completion_percentage, items, summary } = completion;
    const missingItems = items.filter(item => !item.completed);

    // Compact version for sidebar/header
    if (compact) {
        return (
            <Link to="/profil" className="block">
                <div className="flex items-center gap-3 p-3 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                    <div className="relative">
                        <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                            <span className="text-sm font-bold text-white">{completion_percentage}%</span>
                        </div>
                        <svg className="absolute inset-0 w-10 h-10 -rotate-90">
                            <circle
                                cx="20"
                                cy="20"
                                r="18"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="3"
                                className="text-slate-600"
                            />
                            <circle
                                cx="20"
                                cy="20"
                                r="18"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="3"
                                strokeDasharray={`${(completion_percentage / 100) * 113} 113`}
                                className="text-orange-500"
                            />
                        </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">Profil</p>
                        <p className="text-xs text-slate-400">
                            {missingItems.length > 0 
                                ? `${missingItems.length} info${missingItems.length > 1 ? 's' : ''} manquante${missingItems.length > 1 ? 's' : ''}`
                                : "Complet !"
                            }
                        </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                </div>
            </Link>
        );
    }

    // Full card version
    return (
        <Card data-testid="profile-completion-card">
            <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                    <div>
                        <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                            {completion_percentage === 100 ? (
                                <Award className="w-5 h-5 text-green-600" />
                            ) : (
                                <TrendingUp className="w-5 h-5 text-orange-600" />
                            )}
                            Complétion du profil
                        </CardTitle>
                        <CardDescription>
                            {completion_percentage === 100 
                                ? "Félicitations ! Votre profil est complet"
                                : "Complétez votre profil pour une meilleure expérience"
                            }
                        </CardDescription>
                    </div>
                    <div className="text-right">
                        <span className={`text-3xl font-bold ${completion_percentage === 100 ? 'text-green-600' : 'text-orange-600'}`}>
                            {completion_percentage}%
                        </span>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Progress bar */}
                <Progress value={completion_percentage} className="h-2" />
                
                {/* Category summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(CATEGORY_INFO).map(([key, info]) => {
                        const CategoryIcon = info.icon;
                        const completed = summary[key] || 0;
                        const total = summary[`${key}_total`] || 0;
                        const isComplete = completed === total && total > 0;
                        
                        return (
                            <div 
                                key={key}
                                className={`p-3 rounded-lg border ${isComplete ? 'bg-green-50 border-green-200' : 'bg-slate-50 border-slate-200'}`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <div className={`w-6 h-6 rounded ${info.bgColor} flex items-center justify-center`}>
                                        <CategoryIcon className={`w-3 h-3 ${info.color}`} />
                                    </div>
                                    <span className="text-xs font-medium text-slate-600">{info.label}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-bold text-slate-900">
                                        {completed}/{total}
                                    </span>
                                    {isComplete ? (
                                        <CheckCircle className="w-4 h-4 text-green-600" />
                                    ) : (
                                        <XCircle className="w-4 h-4 text-slate-300" />
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
                
                {/* Missing items */}
                {missingItems.length > 0 && (
                    <div className="space-y-2">
                        <h4 className="text-sm font-medium text-slate-700 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-amber-500" />
                            Informations manquantes ({missingItems.length})
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {missingItems.slice(0, 5).map((item) => {
                                const catInfo = CATEGORY_INFO[item.category];
                                return (
                                    <Badge 
                                        key={item.key} 
                                        variant="outline"
                                        className="text-xs"
                                    >
                                        {item.label}
                                    </Badge>
                                );
                            })}
                            {missingItems.length > 5 && (
                                <Badge variant="outline" className="text-xs">
                                    +{missingItems.length - 5} autres
                                </Badge>
                            )}
                        </div>
                    </div>
                )}
                
                {/* Action button */}
                {completion_percentage < 100 && (
                    <Link to="/parametres">
                        <Button className="w-full bg-orange-600 hover:bg-orange-700">
                            Compléter mon profil
                            <ChevronRight className="w-4 h-4 ml-2" />
                        </Button>
                    </Link>
                )}
            </CardContent>
        </Card>
    );
}
