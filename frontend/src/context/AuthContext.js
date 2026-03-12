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
    const [error, setError] = useState(null);

    // Fetch user profile from database
    const fetchUserProfile = useCallback(async (userId) => {
        try {
            const { data, error } = await supabase
                .from('users')
                .select('*')
                .eq('id', userId)
                .single();
            
            if (error) {
                console.error('Error fetching user profile:', error);
                return null;
            }
            setUserProfile(data);
            return data;
        } catch (error) {
            console.error('Error fetching user profile:', error);
            return null;
        }
    }, []);

    // Initialize auth state
    useEffect(() => {
        let mounted = true;

        const initAuth = async () => {
            try {
                // Get initial session
                const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
                
                if (sessionError) {
                    console.error('Session error:', sessionError);
                    if (mounted) {
                        setError(sessionError.message);
                        setLoading(false);
                    }
                    return;
                }

                if (mounted) {
                    setSession(currentSession);
                    setUser(currentSession?.user ?? null);
                    
                    if (currentSession?.user) {
                        await fetchUserProfile(currentSession.user.id);
                    }
                    setLoading(false);
                }
            } catch (err) {
                console.error('Auth init error:', err);
                if (mounted) {
                    setError(err.message);
                    setLoading(false);
                }
            }
        };

        initAuth();

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, newSession) => {
                console.log('Auth event:', event);
                if (mounted) {
                    setSession(newSession);
                    setUser(newSession?.user ?? null);
                    
                    if (newSession?.user) {
                        await fetchUserProfile(newSession.user.id);
                    } else {
                        setUserProfile(null);
                    }
                }
            }
        );

        return () => {
            mounted = false;
            subscription?.unsubscribe();
        };
    }, [fetchUserProfile]);

    // Login with email/password
    const login = async (email, password) => {
        try {
            setError(null);
            const { data, error: loginError } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            
            if (loginError) throw loginError;
            
            // Fetch user profile after login
            if (data?.user) {
                const profile = await fetchUserProfile(data.user.id);
                return { user: data.user, profile };
            }
            
            return data;
        } catch (err) {
            console.error('Login error:', err);
            setError(err.message);
            throw err;
        }
    };

    // Register new user
    const register = async (email, password, userData = {}) => {
        try {
            setError(null);
            
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
            if (authData?.user) {
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
                }
            }
            
            return authData;
        } catch (err) {
            console.error('Register error:', err);
            setError(err.message);
            throw err;
        }
    };

    // Logout
    const logout = async () => {
        try {
            const { error: logoutError } = await supabase.auth.signOut();
            if (logoutError) throw logoutError;
            setUser(null);
            setSession(null);
            setUserProfile(null);
        } catch (err) {
            console.error('Logout error:', err);
            // Clear state anyway
            setUser(null);
            setSession(null);
            setUserProfile(null);
        }
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
        error,
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
