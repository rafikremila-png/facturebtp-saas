import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Mail, Lock, User, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const { login, register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            if (isLogin) {
                await login(email, password);
                toast.success("Connexion réussie !");
            } else {
                await register(email, password, name);
                toast.success("Compte créé avec succès !");
            }
            navigate("/");
        } catch (error) {
            const message = error.response?.data?.detail || "Une erreur est survenue";
            toast.error(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex" data-testid="login-page">
            {/* Left side - Form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
                <div className="w-full max-w-md animate-fade-in">
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center shadow-lg">
                            <Building2 className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900 font-['Barlow_Condensed']">BTP Facture</h1>
                            <p className="text-sm text-slate-500">Gestion de devis et factures</p>
                        </div>
                    </div>

                    <Card className="shadow-xl border-0">
                        <CardHeader className="space-y-1 pb-4">
                            <CardTitle className="text-2xl font-['Barlow_Condensed']">
                                {isLogin ? "Connexion" : "Créer un compte"}
                            </CardTitle>
                            <CardDescription>
                                {isLogin 
                                    ? "Entrez vos identifiants pour accéder à votre espace" 
                                    : "Remplissez le formulaire pour créer votre compte"}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                {!isLogin && (
                                    <div className="space-y-2">
                                        <Label htmlFor="name">Nom complet</Label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                            <Input
                                                id="name"
                                                type="text"
                                                placeholder="Jean Dupont"
                                                value={name}
                                                onChange={(e) => setName(e.target.value)}
                                                className="pl-10"
                                                required={!isLogin}
                                                data-testid="name-input"
                                            />
                                        </div>
                                    </div>
                                )}
                                
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="vous@exemple.fr"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="pl-10"
                                            required
                                            data-testid="email-input"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="password">Mot de passe</Label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="password"
                                            type={showPassword ? "text" : "password"}
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="pl-10 pr-10"
                                            required
                                            data-testid="password-input"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                                        >
                                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>

                                <Button 
                                    type="submit" 
                                    className="w-full bg-orange-600 hover:bg-orange-700"
                                    disabled={loading}
                                    data-testid="submit-btn"
                                >
                                    {loading ? (
                                        <span className="flex items-center gap-2">
                                            <span className="spinner w-4 h-4"></span>
                                            Chargement...
                                        </span>
                                    ) : (
                                        isLogin ? "Se connecter" : "Créer le compte"
                                    )}
                                </Button>
                            </form>

                            <div className="mt-6 text-center">
                                <button
                                    type="button"
                                    onClick={() => setIsLogin(!isLogin)}
                                    className="text-sm text-slate-600 hover:text-orange-600 transition-colors"
                                    data-testid="toggle-auth-mode"
                                >
                                    {isLogin 
                                        ? "Pas encore de compte ? Créer un compte" 
                                        : "Déjà un compte ? Se connecter"}
                                </button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Right side - Image */}
            <div 
                className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
                style={{ backgroundImage: "url('https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=2070&auto=format&fit=crop')" }}
            >
                <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm"></div>
                <div className="absolute inset-0 flex items-center justify-center p-12">
                    <div className="text-center text-white max-w-lg">
                        <h2 className="text-4xl font-bold mb-4 font-['Barlow_Condensed']">
                            Gérez votre activité BTP simplement
                        </h2>
                        <p className="text-lg text-slate-300">
                            Créez des devis professionnels, transformez-les en factures d'un clic, 
                            et suivez vos paiements en temps réel.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
