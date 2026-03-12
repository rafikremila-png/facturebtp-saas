import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { supabase, isSupabaseConfigured } from '@/supabaseClient';

const AuthContext = createContext(null);

// Role constants
export const ROLE_SUPER_ADMIN = "super_admin";
export const ROLE_ADMIN = "admin";
export const ROLE_USER = "user";

// Timeout for auth operations (5 seconds)
const AUTH_TIMEOUT = 5000;

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [userProfile, setUserProfile] = useState(null);
    const [error, setError] = useState(null);
    const [authReady, setAuthReady] = useState(false);
    const initAttempted = useRef(false);

    // Debug logger
    const log = (message, data = null) => {
        const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
        if (data) {
            console.log(`[Auth ${timestamp}] ${message}`, data);
        } else {
            console.log(`[Auth ${timestamp}] ${message}`);
        }
    };

    // Fetch user profile from database with timeout
    const fetchUserProfile = useCallback(async (userId) => {
        if (!userId) return null;
        
        log('Fetching user profile...', { userId });
        
        try {
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Profile fetch timeout')), AUTH_TIMEOUT)
            );

            const fetchPromise = supabase
                .from('users')
                .select('*')
                .eq('id', userId)
                .single();

            const { data, error } = await Promise.race([fetchPromise, timeoutPromise]);
            
            if (error) {
                log('Profile fetch error:', error);
                return null;
            }
            
            log('Profile fetched successfully:', { email: data?.email, role: data?.role });
            setUserProfile(data);
            return data;
        } catch (err) {
            log('Profile fetch exception:', err.message);
            return null;
        }
    }, []);

    // Initialize auth state
    useEffect(() => {
        // Prevent double initialization
        if (initAttempted.current) return;
        initAttempted.current = true;

        let mounted = true;
        let timeoutId = null;

        const initAuth = async () => {
            log('Initializing authentication...');
            
            // Set a safety timeout to prevent infinite loading
            timeoutId = setTimeout(() => {
                if (mounted && loading) {
                    log('Auth initialization timeout - forcing completion');
                    setLoading(false);
                    setAuthReady(true);
                }
            }, AUTH_TIMEOUT);

            // Check if Supabase is configured
            if (!isSupabaseConfigured) {
                log('Supabase not configured - skipping auth');
                if (mounted) {
                    setLoading(false);
                    setAuthReady(true);
                }
                return;
            }

            try {
                // Get initial session
                log('Getting session...');
                const { data: { session: currentSession }, error: sessionError } = await supabase.auth.getSession();
                
                if (sessionError) {
                    log('Session error:', sessionError);
                    if (mounted) {
                        setError(sessionError.message);
                        setLoading(false);
                        setAuthReady(true);
                    }
                    return;
                }

                log('Session result:', { hasSession: !!currentSession, email: currentSession?.user?.email });

                if (mounted) {
                    setSession(currentSession);
                    setUser(currentSession?.user ?? null);
                    
                    if (currentSession?.user) {
                        // Fetch profile but don't block on it
                        fetchUserProfile(currentSession.user.id).finally(() => {
                            if (mounted) {
                                setLoading(false);
                                setAuthReady(true);
                            }
                        });
                    } else {
                        setLoading(false);
                        setAuthReady(true);
                    }
                }
            } catch (err) {
                log('Auth init exception:', err.message);
                if (mounted) {
                    setError(err.message);
                    setLoading(false);
                    setAuthReady(true);
                }
            }
        };

        initAuth();

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, newSession) => {
                log('Auth state changed:', { event, hasSession: !!newSession });
                
                if (mounted) {
                    setSession(newSession);
                    setUser(newSession?.user ?? null);
                    
                    if (newSession?.user) {
                        fetchUserProfile(newSession.user.id);
                    } else {
                        setUserProfile(null);
                    }
                    
                    // Ensure loading is false after any auth change
                    setLoading(false);
                    setAuthReady(true);
                }
            }
        );

        return () => {
            mounted = false;
            if (timeoutId) clearTimeout(timeoutId);
            subscription?.unsubscribe();
        };
    }, [fetchUserProfile]);

    // Login with email/password
    const login = async (email, password) => {
        log('Login attempt:', { email });
        
        try {
            setError(null);
            
            const { data, error: loginError } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            
            if (loginError) {
                log('Login error:', loginError);
                throw loginError;
            }
            
            log('Login successful:', { userId: data?.user?.id });
            
            // Fetch user profile after login
            if (data?.user) {
                const profile = await fetchUserProfile(data.user.id);
                return { user: data.user, profile };
            }
            
            return data;
        } catch (err) {
            log('Login exception:', err.message);
            setError(err.message);
            throw err;
        }
    };

    // Register new user
    const register = async (email, password, userData = {}) => {
        log('Register attempt:', { email });
        
        try {
            setError(null);
            
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
            
            if (authError) {
                log('Register error:', authError);
                throw authError;
            }
            
            log('Register successful:', { userId: authData?.user?.id });
            
            // Create user profile in database
            if (authData?.user) {
                try {
                    await supabase
                        .from('users')
                        .insert({
                            id: authData.user.id,
                            email: email,
                            name: userData.name || '',
                            phone: userData.phone || '',
                            company_name: userData.company_name || '',
                            address: userData.address || '',
                            role: ROLE_USER,
                            subscription_plan: 'trial',
                            subscription_status: 'trial_active',
                            trial_status: 'active',
                            quote_limit: 5,
                            invoice_limit: 5,
                            created_at: new Date().toISOString(),
                            updated_at: new Date().toISOString(),
                        });
                    log('Profile created successfully');
                } catch (profileError) {
                    log('Profile creation error:', profileError);
                }
            }
            
            return authData;
        } catch (err) {
            log('Register exception:', err.message);
            setError(err.message);
            throw err;
        }
    };

    // Logout
    const logout = async () => {
        log('Logout attempt');
        
        try {
            await supabase.auth.signOut();
            log('Logout successful');
        } catch (err) {
            log('Logout error:', err.message);
        } finally {
            // Always clear state
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
        authReady,
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
