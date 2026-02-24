import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth, ROLE_ADMIN, ROLE_SUPER_ADMIN } from "@/context/AuthContext";
import { 
    LayoutDashboard, 
    Users, 
    FileText, 
    Receipt, 
    Settings, 
    LogOut,
    Building2,
    Menu,
    X,
    UserCog,
    Shield,
    Crown
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const navItems = [
    { to: "/", icon: LayoutDashboard, label: "Tableau de bord", exact: true },
    { to: "/clients", icon: Users, label: "Clients" },
    { to: "/devis", icon: FileText, label: "Devis" },
    { to: "/factures", icon: Receipt, label: "Factures" },
    { to: "/parametres", icon: Settings, label: "Paramètres" },
];

// Admin-only navigation items
const adminNavItems = [
    { to: "/utilisateurs", icon: UserCog, label: "Utilisateurs", adminOnly: true },
];

const ROLE_BADGES = {
    [ROLE_SUPER_ADMIN]: { label: "Super Admin", color: "bg-purple-600", icon: Crown },
    [ROLE_ADMIN]: { label: "Admin", color: "bg-blue-600", icon: Shield },
};

export const Layout = () => {
    const { user, logout, isAdmin } = useAuth();
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate("/login");
    };

    const userRoleBadge = ROLE_BADGES[user?.role];

    return (
        <div className="min-h-screen bg-slate-50" data-testid="app-layout">
            {/* Mobile menu button */}
            <div className="lg:hidden fixed top-4 left-4 z-50">
                <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    className="bg-white shadow-md"
                    data-testid="mobile-menu-btn"
                >
                    {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </Button>
            </div>

            {/* Sidebar */}
            <aside 
                className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
                    mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
                data-testid="sidebar"
            >
                {/* Logo */}
                <div className="flex items-center gap-3 px-6 py-6 border-b border-slate-800">
                    <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
                        <Building2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white font-['Barlow_Condensed']">BTP Facture</h1>
                        <p className="text-xs text-slate-400">Gestion devis & factures</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="px-4 py-6 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.exact}
                            onClick={() => setMobileMenuOpen(false)}
                            className={({ isActive }) =>
                                `sidebar-link ${isActive ? 'active' : ''}`
                            }
                            data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                            <item.icon className="w-5 h-5" />
                            <span className="font-medium">{item.label}</span>
                        </NavLink>
                    ))}
                    
                    {/* Admin-only section */}
                    {isAdmin() && (
                        <>
                            <div className="pt-4 pb-2">
                                <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                    Administration
                                </p>
                            </div>
                            {adminNavItems.map((item) => (
                                <NavLink
                                    key={item.to}
                                    to={item.to}
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={({ isActive }) =>
                                        `sidebar-link ${isActive ? 'active' : ''}`
                                    }
                                    data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                                >
                                    <item.icon className="w-5 h-5" />
                                    <span className="font-medium">{item.label}</span>
                                </NavLink>
                            ))}
                        </>
                    )}
                </nav>

                {/* User section */}
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">
                    <div className="flex items-center gap-3 px-2 mb-4">
                        <div className={`w-9 h-9 ${userRoleBadge?.color || 'bg-slate-700'} rounded-full flex items-center justify-center`}>
                            {userRoleBadge ? (
                                <userRoleBadge.icon className="w-4 h-4 text-white" />
                            ) : (
                                <span className="text-sm font-medium text-white">
                                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                                </span>
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">{user?.name}</p>
                            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                            {userRoleBadge && (
                                <Badge className={`${userRoleBadge.color} text-white text-[10px] mt-1`}>
                                    {userRoleBadge.label}
                                </Badge>
                            )}
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                        data-testid="logout-btn"
                    >
                        <LogOut className="w-5 h-5" />
                        <span className="font-medium">Déconnexion</span>
                    </button>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {mobileMenuOpen && (
                <div 
                    className="fixed inset-0 bg-black/50 z-30 lg:hidden"
                    onClick={() => setMobileMenuOpen(false)}
                />
            )}

            {/* Main content */}
            <main className="lg:ml-64 min-h-screen">
                <div className="p-6 lg:p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default Layout;
