import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Mail, Lock, User, Eye, EyeOff, Phone, Building, MapPin, ArrowLeft, CheckCircle, Loader2 } from "lucide-react";

export default function LoginPage() {
    const [searchParams] = useSearchParams();
    const [isLogin, setIsLogin] = useState(true);
    const [step, setStep] = useState("form"); // form, success
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [address, setAddress] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const { login, register, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate("/");
        }
    }, [isAuthenticated, navigate]);

    // Handle URL parameters for registration
    useEffect(() => {
        const mode = searchParams.get("mode");
        if (mode === "register") {
            setIsLogin(false);
        }
    }, [searchParams]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        // Add timeout for login operation
        const timeoutId = setTimeout(() => {
            setLoading(false);
            toast.error("La connexion prend trop de temps. Veuillez réessayer.");
        }, 15000);
        
        try {
            if (isLogin) {
                console.log('[Login] Attempting login:', email);
                await login(email, password);
                clearTimeout(timeoutId);
                toast.success("Connexion réussie !");
                navigate("/");
            } else {
                // Register
                console.log('[Login] Attempting registration:', email);
                const result = await register(email, password, {
                    name,
                    phone,
                    company_name: companyName,
                    address
                });
                clearTimeout(timeoutId);
                
                // Check if email confirmation is required
                if (result?.user && !result?.session) {
                    toast.success("Compte créé ! Vérifiez votre email pour confirmer.");
                    setStep("success");
                } else {
                    toast.success("Compte créé avec succès !");
                    navigate("/");
                }
            }
        } catch (error) {
            clearTimeout(timeoutId);
            console.error("[Login] Auth error:", error);
            const message = error.message || "Une erreur est survenue";
            
            // Translate common Supabase errors
            if (message.includes("Invalid login credentials")) {
                toast.error("Email ou mot de passe incorrect");
            } else if (message.includes("Email not confirmed")) {
                toast.error("Veuillez confirmer votre email");
            } else if (message.includes("User already registered")) {
                toast.error("Cet email est déjà utilisé");
            } else if (message.includes("Password should be")) {
                toast.error("Le mot de passe doit contenir au moins 6 caractères");
            } else {
                toast.error(message);
            }
        } finally {
            setLoading(false);
        }
    };

    const renderSuccessStep = () => (
        <div className="animate-fade-in text-center">
            <Card className="shadow-xl border-0">
                <CardContent className="py-12">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-10 h-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Vérifiez votre email</h2>
                    <p className="text-slate-500 mb-4">
                        Un email de confirmation a été envoyé à <strong>{email}</strong>
                    </p>
                    <p className="text-sm text-slate-400">
                        Cliquez sur le lien dans l'email pour activer votre compte.
                    </p>
                    <Button
                        variant="outline"
                        className="mt-6"
                        onClick={() => {
                            setStep("form");
                            setIsLogin(true);
                        }}
                    >
                        Retour à la connexion
                    </Button>
                </CardContent>
            </Card>
        </div>
    );

    const renderForm = () => (
        <div className="animate-fade-in">
            <Card className="shadow-xl border-0">
                <CardHeader className="space-y-1 pb-4">
                    <CardTitle className="text-2xl font-['Barlow_Condensed']">
                        {isLogin ? "Connexion" : "Créer un compte"}
                    </CardTitle>
                    <CardDescription>
                        {isLogin 
                            ? "Entrez vos identifiants pour accéder à votre compte"
                            : "Remplissez le formulaire pour créer votre compte"
                        }
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Registration fields */}
                        {!isLogin && (
                            <>
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

                                <div className="space-y-2">
                                    <Label htmlFor="phone">Téléphone</Label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="phone"
                                            type="tel"
                                            placeholder="06 12 34 56 78"
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                            className="pl-10"
                                            data-testid="phone-input"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="companyName">Nom de l'entreprise</Label>
                                    <div className="relative">
                                        <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="companyName"
                                            type="text"
                                            placeholder="Mon Entreprise BTP"
                                            value={companyName}
                                            onChange={(e) => setCompanyName(e.target.value)}
                                            className="pl-10"
                                            data-testid="company-input"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="address">Adresse</Label>
                                    <div className="relative">
                                        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="address"
                                            type="text"
                                            placeholder="123 Rue de la Construction"
                                            value={address}
                                            onChange={(e) => setAddress(e.target.value)}
                                            className="pl-10"
                                            data-testid="address-input"
                                        />
                                    </div>
                                </div>
                            </>
                        )}

                        {/* Email field */}
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

                        {/* Password field */}
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
                                    minLength={6}
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
                            {!isLogin && (
                                <p className="text-xs text-slate-500">
                                    Minimum 6 caractères
                                </p>
                            )}
                        </div>

                        {/* Submit button */}
                        <Button
                            type="submit"
                            className="w-full bg-orange-600 hover:bg-orange-700"
                            disabled={loading}
                            data-testid="submit-btn"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    {isLogin ? "Connexion..." : "Création..."}
                                </>
                            ) : (
                                isLogin ? "Se connecter" : "Créer le compte"
                            )}
                        </Button>

                        {/* Toggle login/register */}
                        <div className="text-center pt-4">
                            <button
                                type="button"
                                onClick={() => setIsLogin(!isLogin)}
                                className="text-sm text-orange-600 hover:text-orange-700"
                            >
                                {isLogin ? "Créer un compte" : "Déjà un compte ? Se connecter"}
                            </button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex">
            {/* Left side - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
                <div className="w-full max-w-md">
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center">
                            <Building2 className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold font-['Barlow_Condensed'] text-slate-900">
                                BTP Facture
                            </h1>
                            <p className="text-sm text-slate-500">Gestion devis & factures</p>
                        </div>
                    </div>

                    {/* Form or Success */}
                    {step === "success" ? renderSuccessStep() : renderForm()}
                </div>
            </div>

            {/* Right side - Image/Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-orange-500 to-orange-700 items-center justify-center p-12">
                <div className="text-center text-white max-w-lg">
                    <Building2 className="w-20 h-20 mx-auto mb-8 opacity-90" />
                    <h2 className="text-4xl font-bold font-['Barlow_Condensed'] mb-4">
                        Gérez votre activité BTP simplement
                    </h2>
                    <p className="text-lg opacity-90">
                        Devis, factures, clients et projets — tout en un seul endroit.
                    </p>
                    <div className="mt-12 grid grid-cols-3 gap-6 text-center">
                        <div>
                            <div className="text-3xl font-bold">100%</div>
                            <div className="text-sm opacity-80">Cloud</div>
                        </div>
                        <div>
                            <div className="text-3xl font-bold">24/7</div>
                            <div className="text-sm opacity-80">Accessible</div>
                        </div>
                        <div>
                            <div className="text-3xl font-bold">SSL</div>
                            <div className="text-sm opacity-80">Sécurisé</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
