import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
    Zap, Droplets, Paintbrush, Network, Building2, 
    FileText, Calculator, Send, Shield, CheckCircle2,
    ArrowRight, Star, Clock, Users
} from "lucide-react";

const BUSINESS_CONFIG = {
    general: {
        title: "Logiciel devis et factures BTP",
        subtitle: "Pour tous les corps d'état du bâtiment",
        heroDescription: "Créez des devis et factures professionnels en quelques clics. Conforme aux normes françaises, simple et efficace.",
        icon: Building2,
        color: "orange",
        painPoints: [
            "Perdez-vous du temps à créer vos devis manuellement ?",
            "Vos factures respectent-elles les mentions légales obligatoires ?",
            "Suivez-vous efficacement vos paiements clients ?"
        ],
        features: [
            "Bibliothèque de 140+ articles prédéfinis par métier",
            "Kits de rénovation prêts à l'emploi",
            "PDF conformes aux normes françaises",
            "Suivi des paiements et relances"
        ],
        kits: ["Rénovation appartement clé en main", "Aménagement bureaux", "Construction neuve"],
        categories: ["Électricité", "Plomberie", "Peinture", "Menuiserie", "Maçonnerie", "Réseaux"]
    },
    electrician: {
        title: "Logiciel facturation électricien",
        subtitle: "Devis et factures pour électriciens professionnels",
        heroDescription: "Solution complète pour les électriciens : articles prédéfinis, conformité NFC 15-100, kits d'installation prêts à facturer.",
        icon: Zap,
        color: "yellow",
        painPoints: [
            "Calculez-vous encore vos devis électriques à la main ?",
            "Vos clients demandent des attestations de conformité ?",
            "Gérez-vous facilement vos situations de travaux ?"
        ],
        features: [
            "50+ articles électricité prédéfinis",
            "Prix suggérés par type d'intervention",
            "Kits installation/rénovation électrique",
            "Conformité mentions légales électricien"
        ],
        kits: ["Installation électrique appartement T3", "Rénovation tableau électrique", "Mise aux normes NFC 15-100"],
        categories: ["Installation", "Rénovation", "Dépannage", "Mise aux normes"]
    },
    plumber: {
        title: "Logiciel facturation plombier",
        subtitle: "Devis et factures pour plombiers chauffagistes",
        heroDescription: "Facturez vos interventions plomberie rapidement : articles prédéfinis, kits salle de bain, suivi des dépannages.",
        icon: Droplets,
        color: "blue",
        painPoints: [
            "Perdez-vous du temps à détailler chaque intervention ?",
            "Vos devis salle de bain sont-ils complets ?",
            "Suivez-vous les garanties sur vos installations ?"
        ],
        features: [
            "40+ articles plomberie/chauffage",
            "Kits salle de bain et chauffage",
            "Tarifs dépannage et installation",
            "Suivi retenue de garantie"
        ],
        kits: ["Rénovation salle de bain complète", "Installation chauffe-eau", "Remplacement radiateurs"],
        categories: ["Installation", "Dépannage", "Salle de bain", "Chauffage"]
    },
    painter: {
        title: "Logiciel facturation peintre",
        subtitle: "Devis et factures pour peintres en bâtiment",
        heroDescription: "Créez vos devis peinture en quelques clics : tarifs au m², préparation des supports, finitions incluses.",
        icon: Paintbrush,
        color: "purple",
        painPoints: [
            "Calculez-vous manuellement vos surfaces ?",
            "Oubliez-vous parfois la préparation dans vos devis ?",
            "Vos clients comprennent-ils le détail de vos prestations ?"
        ],
        features: [
            "Tarifs peinture au m² intégrés",
            "Articles préparation et finition",
            "Kits peinture appartement",
            "Distinction intérieur/extérieur"
        ],
        kits: ["Peinture appartement T3", "Ravalement façade", "Rénovation cage d'escalier"],
        categories: ["Intérieur", "Extérieur", "Préparation", "Décoration"]
    },
    it_installer: {
        title: "Logiciel facturation installateur réseaux",
        subtitle: "Devis et factures pour installateurs IT et courants faibles",
        heroDescription: "Facturez vos installations réseau professionnellement : câblage, baies, vidéosurveillance, configuration.",
        icon: Network,
        color: "cyan",
        painPoints: [
            "Détaillez-vous suffisamment vos prestations techniques ?",
            "Vos clients comprennent-ils la valeur de vos services ?",
            "Gérez-vous les contrats de maintenance ?"
        ],
        features: [
            "Articles câblage et infrastructure",
            "Kits installation bureau/entreprise",
            "Tarifs configuration et maintenance",
            "Prestations vidéosurveillance"
        ],
        kits: ["Installation réseau bureau complet", "Vidéosurveillance 4 caméras", "Infrastructure serveur PME"],
        categories: ["Câblage", "Sécurité", "Infrastructure", "Configuration"]
    }
};

const COLOR_CLASSES = {
    orange: { bg: "bg-orange-600", hover: "hover:bg-orange-700", light: "bg-orange-50", text: "text-orange-600", border: "border-orange-200" },
    yellow: { bg: "bg-yellow-500", hover: "hover:bg-yellow-600", light: "bg-yellow-50", text: "text-yellow-600", border: "border-yellow-200" },
    blue: { bg: "bg-blue-600", hover: "hover:bg-blue-700", light: "bg-blue-50", text: "text-blue-600", border: "border-blue-200" },
    purple: { bg: "bg-purple-600", hover: "hover:bg-purple-700", light: "bg-purple-50", text: "text-purple-600", border: "border-purple-200" },
    cyan: { bg: "bg-cyan-600", hover: "hover:bg-cyan-700", light: "bg-cyan-50", text: "text-cyan-600", border: "border-cyan-200" }
};

export default function LandingPage({ businessType = "general" }) {
    const navigate = useNavigate();
    const config = BUSINESS_CONFIG[businessType] || BUSINESS_CONFIG.general;
    const colors = COLOR_CLASSES[config.color];
    const Icon = config.icon;

    const handleCTA = () => {
        navigate(`/login?mode=register&business_type=${businessType}`);
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
            {/* Header */}
            <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${colors.light}`}>
                            <Icon className={`w-6 h-6 ${colors.text}`} />
                        </div>
                        <span className="font-['Barlow_Condensed'] text-xl font-bold text-slate-800">
                            BTP Facture
                        </span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" onClick={() => navigate("/login")}>
                            Connexion
                        </Button>
                        <Button className={`${colors.bg} ${colors.hover}`} onClick={handleCTA}>
                            Essai gratuit
                        </Button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="py-20 px-4">
                <div className="max-w-5xl mx-auto text-center">
                    <Badge className={`${colors.light} ${colors.text} border-0 mb-6`}>
                        14 jours d'essai gratuit • Sans carte bancaire
                    </Badge>
                    <h1 className="font-['Barlow_Condensed'] text-4xl md:text-6xl font-bold text-slate-900 mb-6">
                        {config.title}
                    </h1>
                    <p className="text-xl text-slate-600 mb-4">
                        {config.subtitle}
                    </p>
                    <p className="text-lg text-slate-500 max-w-2xl mx-auto mb-8">
                        {config.heroDescription}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Button size="lg" className={`${colors.bg} ${colors.hover} text-lg px-8`} onClick={handleCTA}>
                            Commencer gratuitement
                            <ArrowRight className="ml-2 w-5 h-5" />
                        </Button>
                        <Button size="lg" variant="outline" onClick={() => navigate("/login")}>
                            Voir une démo
                        </Button>
                    </div>
                    
                    {/* Trust badges */}
                    <div className="mt-12 flex flex-wrap justify-center gap-8 text-sm text-slate-500">
                        <div className="flex items-center gap-2">
                            <Shield className="w-5 h-5" />
                            <span>Conforme RGPD</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="w-5 h-5" />
                            <span>Mentions légales françaises</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Clock className="w-5 h-5" />
                            <span>Support réactif</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pain Points Section */}
            <section className={`py-16 px-4 ${colors.light}`}>
                <div className="max-w-5xl mx-auto">
                    <h2 className="font-['Barlow_Condensed'] text-3xl font-bold text-center mb-12">
                        Vous vous reconnaissez ?
                    </h2>
                    <div className="grid md:grid-cols-3 gap-6">
                        {config.painPoints.map((point, idx) => (
                            <Card key={idx} className="bg-white">
                                <CardContent className="p-6">
                                    <div className={`w-10 h-10 rounded-full ${colors.light} flex items-center justify-center mb-4`}>
                                        <span className={`font-bold ${colors.text}`}>{idx + 1}</span>
                                    </div>
                                    <p className="text-slate-700">{point}</p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-16 px-4">
                <div className="max-w-5xl mx-auto">
                    <h2 className="font-['Barlow_Condensed'] text-3xl font-bold text-center mb-4">
                        La solution pour votre métier
                    </h2>
                    <p className="text-center text-slate-500 mb-12">
                        Tout ce dont vous avez besoin pour facturer efficacement
                    </p>
                    
                    <div className="grid md:grid-cols-2 gap-6">
                        {config.features.map((feature, idx) => (
                            <div key={idx} className="flex items-start gap-4 p-4">
                                <div className={`p-2 rounded-lg ${colors.light}`}>
                                    <CheckCircle2 className={`w-5 h-5 ${colors.text}`} />
                                </div>
                                <span className="text-slate-700">{feature}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Kits Section */}
            <section className={`py-16 px-4 bg-slate-50`}>
                <div className="max-w-5xl mx-auto">
                    <h2 className="font-['Barlow_Condensed'] text-3xl font-bold text-center mb-4">
                        Kits prêts à l'emploi
                    </h2>
                    <p className="text-center text-slate-500 mb-12">
                        Gagnez du temps avec nos kits de facturation adaptés à votre métier
                    </p>
                    
                    <div className="grid md:grid-cols-3 gap-6">
                        {config.kits.map((kit, idx) => (
                            <Card key={idx} className={`${colors.border} border-2`}>
                                <CardContent className="p-6 text-center">
                                    <div className={`w-12 h-12 rounded-full ${colors.light} flex items-center justify-center mx-auto mb-4`}>
                                        <FileText className={`w-6 h-6 ${colors.text}`} />
                                    </div>
                                    <p className="font-medium text-slate-800">{kit}</p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </section>

            {/* Categories Section */}
            <section className="py-16 px-4">
                <div className="max-w-5xl mx-auto text-center">
                    <h2 className="font-['Barlow_Condensed'] text-3xl font-bold mb-4">
                        Bibliothèque d'articles
                    </h2>
                    <p className="text-slate-500 mb-8">
                        Des centaines d'articles prédéfinis pour facturer rapidement
                    </p>
                    <div className="flex flex-wrap justify-center gap-3">
                        {config.categories.map((cat, idx) => (
                            <Badge key={idx} variant="secondary" className="text-sm py-2 px-4">
                                {cat}
                            </Badge>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className={`py-20 px-4 ${colors.bg}`}>
                <div className="max-w-3xl mx-auto text-center text-white">
                    <h2 className="font-['Barlow_Condensed'] text-3xl md:text-4xl font-bold mb-6">
                        Prêt à simplifier votre facturation ?
                    </h2>
                    <p className="text-lg opacity-90 mb-8">
                        Rejoignez les professionnels qui gagnent du temps chaque jour
                    </p>
                    <Button 
                        size="lg" 
                        variant="secondary" 
                        className="text-lg px-8"
                        onClick={handleCTA}
                    >
                        Essayer gratuitement 14 jours
                        <ArrowRight className="ml-2 w-5 h-5" />
                    </Button>
                    <p className="mt-4 text-sm opacity-75">
                        Sans engagement • Sans carte bancaire
                    </p>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-4 bg-slate-900 text-slate-400">
                <div className="max-w-5xl mx-auto">
                    <div className="grid md:grid-cols-4 gap-8 mb-8">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Building2 className="w-5 h-5 text-orange-500" />
                                <span className="font-bold text-white">BTP Facture</span>
                            </div>
                            <p className="text-sm">
                                Logiciel de devis et facturation pour les professionnels du bâtiment.
                            </p>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-4">Métiers</h4>
                            <ul className="space-y-2 text-sm">
                                <li><a href="/logiciel-facturation-electricien" className="hover:text-white">Électricien</a></li>
                                <li><a href="/logiciel-facturation-plombier" className="hover:text-white">Plombier</a></li>
                                <li><a href="/logiciel-facturation-peintre" className="hover:text-white">Peintre</a></li>
                                <li><a href="/logiciel-facturation-installateur-reseau" className="hover:text-white">Installateur réseaux</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-4">Fonctionnalités</h4>
                            <ul className="space-y-2 text-sm">
                                <li>Devis professionnels</li>
                                <li>Factures conformes</li>
                                <li>Suivi des paiements</li>
                                <li>PDF personnalisés</li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-4">Légal</h4>
                            <ul className="space-y-2 text-sm">
                                <li>Mentions légales</li>
                                <li>CGU</li>
                                <li>Politique de confidentialité</li>
                            </ul>
                        </div>
                    </div>
                    <div className="border-t border-slate-800 pt-8 text-center text-sm">
                        © 2026 BTP Facture. Tous droits réservés.
                    </div>
                </div>
            </footer>
        </div>
    );
}
