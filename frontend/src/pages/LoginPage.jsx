import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Mail, Lock, User, Eye, EyeOff, Phone, Building, MapPin, ArrowLeft, CheckCircle } from "lucide-react";
import OTPInput from "@/components/OTPInput";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LoginPage() {
    const [searchParams] = useSearchParams();
    const [isLogin, setIsLogin] = useState(true);
    const [step, setStep] = useState("form"); // form, otp, success
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [address, setAddress] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [otpCode, setOtpCode] = useState("");
    const { login } = useAuth();
    const navigate = useNavigate();

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
        
        try {
            if (isLogin) {
                await login(email, password);
                toast.success("Connexion réussie !");
                navigate("/");
            } else {
                // Register - this will require OTP verification
                await axios.post(`${API}/auth/register`, {
                    email,
                    password,
                    name,
                    phone,
                    company_name: companyName,
                    address,
                    business_type: businessType
                });
                toast.success("Code de vérification envoyé par email");
                setStep("otp");
            }
        } catch (error) {
            const message = error.response?.data?.detail || "Une erreur est survenue";
            
            // If email not verified, show OTP step
            if (error.response?.status === 403 && message.includes("non vérifié")) {
                toast.info("Vérifiez votre email avec le code envoyé");
                setStep("otp");
            } else {
                toast.error(message);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOTP = async () => {
        if (otpCode.length !== 6) {
            toast.error("Entrez le code à 6 chiffres");
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API}/auth/verify-email`, {
                email,
                otp_code: otpCode,
                otp_type: "registration"
            });

            // Store token and redirect
            localStorage.setItem("token", response.data.access_token);
            toast.success("Email vérifié ! Bienvenue !");
            setStep("success");
            
            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        } catch (error) {
            toast.error(error.response?.data?.detail || "Code invalide ou expiré");
        } finally {
            setLoading(false);
        }
    };

    const handleResendOTP = async () => {
        setLoading(true);
        try {
            await axios.post(`${API}/auth/resend-otp`, {
                email,
                otp_type: "registration"
            });
            toast.success("Nouveau code envoyé !");
        } catch (error) {
            toast.error("Erreur lors de l'envoi du code");
        } finally {
            setLoading(false);
        }
    };

    const renderOTPStep = () => (
        <div className="animate-fade-in">
            <button
                type="button"
                onClick={() => setStep("form")}
                className="flex items-center gap-2 text-slate-600 hover:text-orange-600 mb-6"
            >
                <ArrowLeft className="w-4 h-4" />
                Retour
            </button>

            <Card className="shadow-xl border-0">
                <CardHeader className="space-y-1 pb-4 text-center">
                    <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Mail className="w-8 h-8 text-orange-600" />
                    </div>
                    <CardTitle className="text-2xl font-['Barlow_Condensed']">
                        Vérifiez votre email
                    </CardTitle>
                    <CardDescription>
                        Un code à 6 chiffres a été envoyé à <strong>{email}</strong>
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <OTPInput
                        length={6}
                        value={otpCode}
                        onChange={setOtpCode}
                        disabled={loading}
                    />

                    <Button
                        onClick={handleVerifyOTP}
                        className="w-full bg-orange-600 hover:bg-orange-700"
                        disabled={loading || otpCode.length !== 6}
                        data-testid="verify-otp-btn"
                    >
                        {loading ? "Vérification..." : "Vérifier le code"}
                    </Button>

                    <div className="text-center">
                        <button
                            type="button"
                            onClick={handleResendOTP}
                            disabled={loading}
                            className="text-sm text-slate-600 hover:text-orange-600"
                        >
                            Renvoyer le code
                        </button>
                    </div>

                    <p className="text-xs text-slate-500 text-center">
                        Le code expire dans 10 minutes
                    </p>
                </CardContent>
            </Card>
        </div>
    );

    const renderSuccessStep = () => (
        <div className="animate-fade-in text-center">
            <Card className="shadow-xl border-0">
                <CardContent className="py-12">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-10 h-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Compte activé !</h2>
                    <p className="text-slate-500">Redirection vers votre tableau de bord...</p>
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
                            ? "Entrez vos identifiants pour accéder à votre espace" 
                            : "Remplissez le formulaire pour créer votre compte"}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="name">Nom complet *</Label>
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
                                    <Label htmlFor="phone">Téléphone *</Label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            id="phone"
                                            type="tel"
                                            placeholder="06 12 34 56 78"
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                            className="pl-10"
                                            required={!isLogin}
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
                        
                        <div className="space-y-2">
                            <Label htmlFor="email">Email *</Label>
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
                            <Label htmlFor="password">Mot de passe *</Label>
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
                            {!isLogin && (
                                <p className="text-xs text-slate-500">
                                    Min. 8 caractères, 1 majuscule, 1 minuscule, 1 chiffre
                                </p>
                            )}
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
                            onClick={() => {
                                setIsLogin(!isLogin);
                                setStep("form");
                            }}
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
    );

    return (
        <div className="min-h-screen flex" data-testid="login-page">
            {/* Left side - Form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
                <div className="w-full max-w-md">
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

                    {step === "form" && renderForm()}
                    {step === "otp" && renderOTPStep()}
                    {step === "success" && renderSuccessStep()}
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
