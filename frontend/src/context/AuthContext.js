import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase } from '@/supabaseClient';

const AuthContext = createContext(null);

// Role constants
export const ROLE_SUPER_ADMIN = "super_admin";
export const ROLE_ADMIN = "admin";
export const ROLE_USER = "user";

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [userProfile, setUserProfile] = useState(null);

    // Fetch user profile from database
    const fetchUserProfile = useCallback(async (userId) => {
        try {
            const { data, error } = await supabase
                .from('users')
                .select('*')
                .eq('id', userId)
                .single();
            
            if (error) throw error;
            setUserProfile(data);
            return data;
        } catch (error) {
            console.error('Error fetching user profile:', error);
            return null;
        }
    }, []);

    // Initialize auth state
    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            if (session?.user) {
                fetchUserProfile(session.user.id);
            }
            setLoading(false);
        });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, session) => {
                console.log('Auth event:', event);
                setSession(session);
                setUser(session?.user ?? null);
                
                if (session?.user) {
                    await fetchUserProfile(session.user.id);
                } else {
                    setUserProfile(null);
                }
                setLoading(false);
            }
        );

        return () => subscription.unsubscribe();
    }, [fetchUserProfile]);

    // Login with email/password
    const login = async (email, password) => {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        
        if (error) throw error;
        
        // Fetch user profile after login
        if (data.user) {
            const profile = await fetchUserProfile(data.user.id);
            return { user: data.user, profile };
        }
        
        return data;
    };

    // Register new user
    const register = async (email, password, userData = {}) => {
        // 1. Create auth user
        const { data: authData, error: authError } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    name: userData.name,
                    phone: userData.phone,
                }
            }
        });
        
        if (authError) throw authError;
        
        // 2. Create user profile in database
        if (authData.user) {
            const { error: profileError } = await supabase
                .from('users')
                .insert({
                    id: authData.user.id,
                    email: email,
                    name: userData.name || '',
                    phone: userData.phone || '',
                    company_name: userData.company_name || '',
                    address: userData.address || '',
                    role: ROLE_USER,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                });
            
            if (profileError) {
                console.error('Error creating profile:', profileError);
                // Profile might already exist if user was created before
            }
        }
        
        return authData;
    };

    // Logout
    const logout = async () => {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
        setUser(null);
        setSession(null);
        setUserProfile(null);
    };

    // Role helper functions
    const isAdmin = () => {
        return userProfile?.role === ROLE_ADMIN || userProfile?.role === ROLE_SUPER_ADMIN;
    };

    const isSuperAdmin = () => {
        return userProfile?.role === ROLE_SUPER_ADMIN;
    };

    const hasRole = (roles) => {
        if (!userProfile?.role) return false;
        if (Array.isArray(roles)) {
            return roles.includes(userProfile.role);
        }
        return userProfile.role === roles;
    };

    // Combined user data (auth + profile)
    const fullUser = userProfile ? {
        ...user,
        ...userProfile,
        id: user?.id || userProfile?.id,
    } : user;

    const value = {
        user: fullUser,
        session,
        token: session?.access_token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isAdmin,
        isSuperAdmin,
        hasRole,
        userRole: userProfile?.role || ROLE_USER,
        refreshProfile: () => user && fetchUserProfile(user.id),
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
