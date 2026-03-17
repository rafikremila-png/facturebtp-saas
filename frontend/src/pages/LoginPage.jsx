import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Mail, Lock, User, Eye, EyeOff, Phone, Building, MapPin, ArrowLeft, CheckCircle, Loader2, ShieldCheck, RefreshCw } from "lucide-react";

function OtpInput({ value, onChange }) {
    const inputsRef = useRef([]);

    const handleChange = (index, digit) => {
        if (!/^\d?$/.test(digit)) return;
        const arr = value.split('');
        arr[index] = digit;
        const next = arr.join('').slice(0, 6);
        onChange(next);
        if (digit && index < 5) {
            inputsRef.current[index + 1]?.focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !value[index] && index > 0) {
            inputsRef.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        onChange(pasted);
        const focusIdx = Math.min(pasted.length, 5);
        inputsRef.current[focusIdx]?.focus();
    };

    return (
        <div className="flex gap-2 justify-center" data-testid="otp-input-group">
            {[0, 1, 2, 3, 4, 5].map((i) => (
                <input
                    key={i}
                    ref={(el) => (inputsRef.current[i] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={value[i] || ''}
                    onChange={(e) => handleChange(i, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    onPaste={i === 0 ? handlePaste : undefined}
                    className="w-12 h-14 text-center text-2xl font-bold border-2 border-slate-200 rounded-lg focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition-all"
                    data-testid={`otp-digit-${i}`}
                />
            ))}
        </div>
    );
}

export default function LoginPage() {
    const [searchParams] = useSearchParams();
    const [isLogin, setIsLogin] = useState(true);
    const [step, setStep] = useState("form"); // form, verify, success
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [address, setAddress] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [otpCode, setOtpCode] = useState("");
    const [resendCooldown, setResendCooldown] = useState(0);
    const { login, register, verifyOtp, resendVerification, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/");
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        const mode = searchParams.get("mode");
        if (mode === "register") {
            setIsLogin(false);
        }
    }, [searchParams]);

    // Resend cooldown timer
    useEffect(() => {
        if (resendCooldown <= 0) return;
        const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
        return () => clearTimeout(timer);
    }, [resendCooldown]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const timeoutId = setTimeout(() => {
            setLoading(false);
            toast.error("La connexion prend trop de temps. Veuillez réessayer.");
        }, 15000);

        try {
            if (isLogin) {
                await login(email, password);
                clearTimeout(timeoutId);
                toast.success("Connexion réussie !");
                navigate("/");
            } else {
                const result = await register(email, password, {
                    name,
                    phone,
                    company_name: companyName,
                    address,
                });
                clearTimeout(timeoutId);

                if (result?.needs_verification) {
                    toast.success("Un code de vérification a été envoyé à votre email.");
                    setStep("verify");
                    setResendCooldown(60);
                } else {
                    toast.success("Compte créé avec succès !");
                    navigate("/");
                }
            }
        } catch (error) {
            clearTimeout(timeoutId);
            const message = error.message || "Une erreur est survenue";

            if (message.includes("Invalid login credentials")) {
                toast.error("Email ou mot de passe incorrect");
            } else if (message.includes("Email not confirmed")) {
                toast.error("Veuillez vérifier votre email avec le code reçu");
                setStep("verify");
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

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        if (otpCode.length !== 6) {
            toast.error("Veuillez entrer le code à 6 chiffres");
            return;
        }

        setLoading(true);
        try {
            await verifyOtp(email, otpCode);
            toast.success("Email vérifié ! Bienvenue sur BTP Facture.");
            setStep("success");
            setTimeout(() => navigate("/"), 1500);
        } catch (error) {
            const message = error.message || "";
            // Messages d'erreur du backend français
            if (message.includes("expiré") || message.includes("expired")) {
                toast.error("Code expiré. Veuillez demander un nouveau code.");
            } else if (message.includes("incorrect") || message.includes("invalid") || message.includes("Invalid")) {
                toast.error("Code incorrect. Vérifiez et réessayez.");
            } else if (message.includes("non trouvé") || message.includes("not found")) {
                toast.error("Session expirée. Veuillez recommencer l'inscription.");
                setStep("form");
                setIsLogin(false);
            } else if (message.includes("déjà utilisé") || message.includes("already")) {
                toast.error("Cet email est déjà enregistré. Essayez de vous connecter.");
                setStep("form");
                setIsLogin(true);
            } else {
                toast.error(message || "Erreur de vérification. Veuillez réessayer.");
            }
            setOtpCode("");
        } finally {
            setLoading(false);
        }
    };

    const handleResendCode = async () => {
        if (resendCooldown > 0) return;

        setLoading(true);
        try {
            await resendVerification(email);
            toast.success("Nouveau code envoyé !");
            setResendCooldown(60);
            setOtpCode("");
        } catch (error) {
            toast.error("Erreur lors de l'envoi. Veuillez réessayer.");
        } finally {
            setLoading(false);
        }
    };

    // ===== VERIFY STEP =====
    const renderVerifyStep = () => (
        <div className="animate-fade-in">
            <Card className="shadow-xl border-0">
                <CardHeader className="text-center pb-2">
                    <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <ShieldCheck className="w-8 h-8 text-orange-600" />
                    </div>
                    <CardTitle className="text-2xl font-['Barlow_Condensed']">
                        Vérification de l'email
                    </CardTitle>
                    <CardDescription>
                        Un code à 6 chiffres a été envoyé à <strong className="text-slate-700">{email}</strong>
                    </CardDescription>
                    <p className="text-xs text-slate-400 mt-1">Le code expire dans 10 minutes</p>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleVerifyOtp} className="space-y-6">
                        <OtpInput value={otpCode} onChange={setOtpCode} />

                        <Button
                            type="submit"
                            className="w-full bg-orange-600 hover:bg-orange-700"
                            disabled={loading || otpCode.length !== 6}
                            data-testid="verify-otp-btn"
                        >
                            {loading ? (
                                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Vérification...</>
                            ) : (
                                "Vérifier le code"
                            )}
                        </Button>

                        <div className="text-center space-y-3">
                            <p className="text-sm text-slate-500">
                                Vous n'avez pas reçu le code ?
                            </p>
                            <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={handleResendCode}
                                disabled={resendCooldown > 0 || loading}
                                className="text-orange-600 hover:text-orange-700"
                                data-testid="resend-code-btn"
                            >
                                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                {resendCooldown > 0
                                    ? `Renvoyer dans ${resendCooldown}s`
                                    : "Renvoyer le code"
                                }
                            </Button>
                        </div>

                        <div className="text-center pt-2">
                            <button
                                type="button"
                                onClick={() => {
                                    setStep("form");
                                    setOtpCode("");
                                }}
                                className="text-sm text-slate-500 hover:text-slate-700 inline-flex items-center gap-1"
                            >
                                <ArrowLeft className="w-3 h-3" />
                                Modifier l'email
                            </button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );

    // ===== SUCCESS STEP =====
    const renderSuccessStep = () => (
        <div className="animate-fade-in text-center">
            <Card className="shadow-xl border-0">
                <CardContent className="py-12">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle className="w-10 h-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Email vérifié !</h2>
                    <p className="text-slate-500 mb-4">
                        Votre compte est maintenant actif.
                    </p>
                    <p className="text-sm text-slate-400">
                        Redirection vers votre tableau de bord...
                    </p>
                </CardContent>
            </Card>
        </div>
    );

    // ===== FORM STEP =====
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

    const renderStep = () => {
        if (step === "verify") return renderVerifyStep();
        if (step === "success") return renderSuccessStep();
        return renderForm();
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex">
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
                <div className="w-full max-w-md">
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

                    {renderStep()}
                </div>
            </div>

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
