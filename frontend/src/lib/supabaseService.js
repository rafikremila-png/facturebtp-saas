/**
 * Supabase API Service
 * Replaces all FastAPI backend calls with direct Supabase queries
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// ============== AUTHENTICATION ==============

export const authService = {
    async signUp(email, password, userData = {}) {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: userData
            }
        });
        if (error) throw error;
        
        // Create user profile
        if (data.user) {
            await supabase.from('users').upsert({
                id: data.user.id,
                email: data.user.email,
                name: userData.name || '',
                role: 'user',
                subscription_plan: 'trial',
                trial_status: 'trial',
                trial_started_at: new Date().toISOString(),
                trial_ends_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                quote_limit: 5,
                invoice_limit: 5
            });
        }
        
        return data;
    },

    async signIn(email, password) {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });
        if (error) throw error;
        return data;
    },

    async signOut() {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
    },

    async getSession() {
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        return data.session;
    },

    async getUser() {
        const { data: { user }, error } = await supabase.auth.getUser();
        if (error) throw error;
        
        if (user) {
            // Get full profile from users table
            const { data: profile } = await supabase
                .from('users')
                .select('*')
                .eq('id', user.id)
                .single();
            
            return { ...user, ...profile };
        }
        return null;
    },

    onAuthStateChange(callback) {
        return supabase.auth.onAuthStateChange(callback);
    }
};

// ============== CLIENTS ==============

export const clientsService = {
    async getAll() {
        const { data, error } = await supabase
            .from('clients')
            .select('*')
            .order('created_at', { ascending: false });
        if (error) throw error;
        return data;
    },

    async getById(id) {
        const { data, error } = await supabase
            .from('clients')
            .select('*')
            .eq('id', id)
            .single();
        if (error) throw error;
        return data;
    },

    async create(clientData) {
        const { data: { user } } = await supabase.auth.getUser();
        const { data, error } = await supabase
            .from('clients')
            .insert({ ...clientData, user_id: user.id })
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async update(id, clientData) {
        const { data, error } = await supabase
            .from('clients')
            .update(clientData)
            .eq('id', id)
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async delete(id) {
        const { error } = await supabase
            .from('clients')
            .delete()
            .eq('id', id);
        if (error) throw error;
    }
};

// ============== QUOTES ==============

export const quotesService = {
    async getAll(filters = {}) {
        let query = supabase
            .from('quotes')
            .select('*, clients(name, email)')
            .order('created_at', { ascending: false });
        
        if (filters.status) {
            query = query.eq('status', filters.status);
        }
        if (filters.client_id) {
            query = query.eq('client_id', filters.client_id);
        }
        
        const { data, error } = await query;
        if (error) throw error;
        return data;
    },

    async getById(id) {
        const { data, error } = await supabase
            .from('quotes')
            .select('*, clients(*)')
            .eq('id', id)
            .single();
        if (error) throw error;
        return data;
    },

    async create(quoteData) {
        const { data: { user } } = await supabase.auth.getUser();
        
        // Check trial limits
        const canCreate = await trialService.checkLimit('quote');
        if (!canCreate.allowed) {
            throw new Error(canCreate.message);
        }
        
        // Generate quote number
        const quoteNumber = await this.generateNumber();
        
        const { data, error } = await supabase
            .from('quotes')
            .insert({ 
                ...quoteData, 
                user_id: user.id,
                quote_number: quoteNumber
            })
            .select()
            .single();
        if (error) throw error;
        
        // Increment counter
        await trialService.incrementUsage('quotes_created');
        
        return data;
    },

    async update(id, quoteData) {
        const { data, error } = await supabase
            .from('quotes')
            .update(quoteData)
            .eq('id', id)
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async delete(id) {
        const { error } = await supabase
            .from('quotes')
            .delete()
            .eq('id', id);
        if (error) throw error;
    },

    async generateNumber() {
        const year = new Date().getFullYear();
        const { data: { user } } = await supabase.auth.getUser();
        
        // Get or create counter
        const { data: counter } = await supabase
            .from('counters')
            .select('current_value')
            .eq('user_id', user.id)
            .eq('counter_type', 'quote')
            .eq('year', year)
            .single();
        
        const nextValue = (counter?.current_value || 0) + 1;
        
        await supabase
            .from('counters')
            .upsert({
                user_id: user.id,
                counter_type: 'quote',
                year: year,
                current_value: nextValue
            });
        
        return `DEV-${year}-${String(nextValue).padStart(4, '0')}`;
    },

    async convertToInvoice(quoteId) {
        const quote = await this.getById(quoteId);
        if (!quote) throw new Error('Devis non trouvé');
        
        const invoiceData = {
            client_id: quote.client_id,
            client_name: quote.client_name,
            client_email: quote.client_email,
            client_address: quote.client_address,
            items: quote.items,
            total_ht: quote.total_ht,
            total_tva: quote.total_tva,
            total_ttc: quote.total_ttc,
            notes: quote.notes,
            quote_id: quoteId,
            payment_status: 'unpaid',
            due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        };
        
        const invoice = await invoicesService.create(invoiceData);
        
        // Update quote status
        await this.update(quoteId, { status: 'accepted' });
        
        return invoice;
    }
};

// ============== INVOICES ==============

export const invoicesService = {
    async getAll(filters = {}) {
        let query = supabase
            .from('invoices')
            .select('*, clients(name, email)')
            .order('created_at', { ascending: false });
        
        if (filters.payment_status) {
            query = query.eq('payment_status', filters.payment_status);
        }
        if (filters.client_id) {
            query = query.eq('client_id', filters.client_id);
        }
        
        const { data, error } = await query;
        if (error) throw error;
        return data;
    },

    async getById(id) {
        const { data, error } = await supabase
            .from('invoices')
            .select('*, clients(*)')
            .eq('id', id)
            .single();
        if (error) throw error;
        return data;
    },

    async create(invoiceData) {
        const { data: { user } } = await supabase.auth.getUser();
        
        // Check trial limits
        const canCreate = await trialService.checkLimit('invoice');
        if (!canCreate.allowed) {
            throw new Error(canCreate.message);
        }
        
        // Generate invoice number
        const invoiceNumber = await this.generateNumber();
        
        const { data, error } = await supabase
            .from('invoices')
            .insert({ 
                ...invoiceData, 
                user_id: user.id,
                invoice_number: invoiceNumber
            })
            .select()
            .single();
        if (error) throw error;
        
        // Increment counter
        await trialService.incrementUsage('invoices_created');
        
        return data;
    },

    async update(id, invoiceData) {
        const { data, error } = await supabase
            .from('invoices')
            .update(invoiceData)
            .eq('id', id)
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async delete(id) {
        const { error } = await supabase
            .from('invoices')
            .delete()
            .eq('id', id);
        if (error) throw error;
    },

    async generateNumber() {
        const year = new Date().getFullYear();
        const { data: { user } } = await supabase.auth.getUser();
        
        const { data: counter } = await supabase
            .from('counters')
            .select('current_value')
            .eq('user_id', user.id)
            .eq('counter_type', 'invoice')
            .eq('year', year)
            .single();
        
        const nextValue = (counter?.current_value || 0) + 1;
        
        await supabase
            .from('counters')
            .upsert({
                user_id: user.id,
                counter_type: 'invoice',
                year: year,
                current_value: nextValue
            });
        
        return `FAC-${year}-${String(nextValue).padStart(4, '0')}`;
    },

    async markAsPaid(id, amount = null) {
        const invoice = await this.getById(id);
        const paidAmount = amount || invoice.total_ttc;
        
        const status = paidAmount >= invoice.total_ttc ? 'paid' : 'partial';
        
        return this.update(id, {
            payment_status: status,
            paid_amount: paidAmount,
            paid_at: new Date().toISOString()
        });
    }
};

// ============== SETTINGS ==============

export const settingsService = {
    async get() {
        const { data: { user } } = await supabase.auth.getUser();
        const { data, error } = await supabase
            .from('settings')
            .select('*')
            .eq('user_id', user.id)
            .single();
        
        if (error && error.code !== 'PGRST116') throw error;
        return data;
    },

    async update(settingsData) {
        const { data: { user } } = await supabase.auth.getUser();
        
        const { data, error } = await supabase
            .from('settings')
            .upsert({ ...settingsData, user_id: user.id })
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async uploadLogo(file) {
        const { data: { user } } = await supabase.auth.getUser();
        const fileName = `logos/${user.id}/${Date.now()}_${file.name}`;
        
        const { data, error } = await supabase.storage
            .from('documents')
            .upload(fileName, file);
        if (error) throw error;
        
        const { data: { publicUrl } } = supabase.storage
            .from('documents')
            .getPublicUrl(fileName);
        
        await this.update({ company_logo_url: publicUrl });
        
        return publicUrl;
    }
};

// ============== TRIAL & SUBSCRIPTION ==============

export const trialService = {
    async getStatus() {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return null;
        
        const { data: profile } = await supabase
            .from('users')
            .select('*')
            .eq('id', user.id)
            .single();
        
        if (!profile) return null;
        
        const now = new Date();
        const trialEnds = new Date(profile.trial_ends_at);
        const daysRemaining = Math.max(0, Math.ceil((trialEnds - now) / (1000 * 60 * 60 * 24)));
        
        return {
            plan: profile.subscription_plan || 'trial',
            status: profile.trial_status || 'trial',
            is_trial: profile.trial_status === 'trial',
            trial_ends_at: profile.trial_ends_at,
            days_remaining: daysRemaining,
            quote_limit: profile.quote_limit || 5,
            invoice_limit: profile.invoice_limit || 5,
            quotes_used: profile.quotes_created || 0,
            invoices_used: profile.invoices_created || 0,
            is_super_admin: profile.role === 'super_admin'
        };
    },

    async checkLimit(resourceType) {
        const status = await this.getStatus();
        
        // Super admin has unlimited access
        if (status.is_super_admin) {
            return { allowed: true, message: 'OK' };
        }
        
        // Check if trial expired
        if (status.is_trial && status.days_remaining <= 0) {
            return { 
                allowed: false, 
                message: 'Votre période d\'essai est terminée. Passez à un plan payant pour continuer.'
            };
        }
        
        // Check limits
        if (resourceType === 'quote') {
            if (status.quotes_used >= status.quote_limit) {
                return {
                    allowed: false,
                    message: `Limite de devis atteinte (${status.quotes_used}/${status.quote_limit}). Passez à un plan supérieur.`
                };
            }
        } else if (resourceType === 'invoice') {
            if (status.invoices_used >= status.invoice_limit) {
                return {
                    allowed: false,
                    message: `Limite de factures atteinte (${status.invoices_used}/${status.invoice_limit}). Passez à un plan supérieur.`
                };
            }
        }
        
        return { allowed: true, message: 'OK' };
    },

    async incrementUsage(field) {
        const { data: { user } } = await supabase.auth.getUser();
        
        const { data: profile } = await supabase
            .from('users')
            .select(field)
            .eq('id', user.id)
            .single();
        
        await supabase
            .from('users')
            .update({ [field]: (profile[field] || 0) + 1 })
            .eq('id', user.id);
    }
};

// ============== DASHBOARD ==============

export const dashboardService = {
    async getStats() {
        const { data: { user } } = await supabase.auth.getUser();
        
        // Get counts
        const [clientsResult, quotesResult, invoicesResult] = await Promise.all([
            supabase.from('clients').select('id', { count: 'exact' }).eq('user_id', user.id),
            supabase.from('quotes').select('id', { count: 'exact' }).eq('user_id', user.id),
            supabase.from('invoices').select('id, total_ttc, paid_amount, payment_status', { count: 'exact' }).eq('user_id', user.id)
        ]);
        
        const invoices = invoicesResult.data || [];
        const paidInvoices = invoices.filter(i => i.payment_status === 'paid' || i.payment_status === 'paye');
        const unpaidInvoices = invoices.filter(i => i.payment_status === 'unpaid' || i.payment_status === 'impaye');
        
        const totalTurnover = paidInvoices.reduce((sum, i) => sum + (i.total_ttc || 0), 0);
        const unpaidAmount = unpaidInvoices.reduce((sum, i) => sum + ((i.total_ttc || 0) - (i.paid_amount || 0)), 0);
        
        return {
            total_clients: clientsResult.count || 0,
            total_quotes: quotesResult.count || 0,
            total_invoices: invoicesResult.count || 0,
            total_turnover: totalTurnover,
            unpaid_invoices_count: unpaidInvoices.length,
            unpaid_invoices_amount: unpaidAmount
        };
    },

    async getFinancialReport(period = 'year') {
        const { data: { user } } = await supabase.auth.getUser();
        
        let startDate = new Date();
        if (period === 'month') startDate.setMonth(startDate.getMonth() - 1);
        else if (period === 'quarter') startDate.setMonth(startDate.getMonth() - 3);
        else if (period === 'year') startDate.setFullYear(startDate.getFullYear() - 1);
        
        const { data: invoices } = await supabase
            .from('invoices')
            .select('*')
            .eq('user_id', user.id)
            .gte('created_at', startDate.toISOString());
        
        const total_revenue = invoices?.reduce((sum, i) => sum + (i.total_ttc || 0), 0) || 0;
        const total_paid = invoices?.reduce((sum, i) => sum + (i.paid_amount || 0), 0) || 0;
        
        return {
            total_revenue,
            total_paid,
            total_pending: total_revenue - total_paid,
            total_overdue: 0,
            collection_rate: total_revenue > 0 ? (total_paid / total_revenue * 100) : 0,
            invoices_by_status: {},
            monthly_revenue: [],
            recent_payments: []
        };
    }
};

// ============== PREDEFINED ITEMS & KITS ==============

export const predefinedItemsService = {
    async getCategories() {
        const { data, error } = await supabase
            .from('predefined_items')
            .select('category')
            .order('category');
        if (error) throw error;
        
        const categories = [...new Set(data?.map(d => d.category) || [])];
        return categories;
    },

    async getByCategory(category) {
        let query = supabase
            .from('predefined_items')
            .select('*')
            .order('description');
        
        if (category) {
            query = query.eq('category', category);
        }
        
        const { data, error } = await query;
        if (error) throw error;
        return data;
    },

    async create(itemData) {
        const { data: { user } } = await supabase.auth.getUser();
        const { data, error } = await supabase
            .from('predefined_items')
            .insert({ ...itemData, user_id: user.id })
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async update(id, itemData) {
        const { data, error } = await supabase
            .from('predefined_items')
            .update(itemData)
            .eq('id', id)
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async delete(id) {
        const { error } = await supabase
            .from('predefined_items')
            .delete()
            .eq('id', id);
        if (error) throw error;
    }
};

export const kitsService = {
    async getAll() {
        const { data, error } = await supabase
            .from('kits')
            .select('*')
            .order('name');
        if (error) throw error;
        return data;
    },

    async getById(id) {
        const { data, error } = await supabase
            .from('kits')
            .select('*')
            .eq('id', id)
            .single();
        if (error) throw error;
        return data;
    },

    async create(kitData) {
        const { data: { user } } = await supabase.auth.getUser();
        const { data, error } = await supabase
            .from('kits')
            .insert({ ...kitData, user_id: user.id })
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async update(id, kitData) {
        const { data, error } = await supabase
            .from('kits')
            .update(kitData)
            .eq('id', id)
            .select()
            .single();
        if (error) throw error;
        return data;
    },

    async delete(id) {
        const { error } = await supabase
            .from('kits')
            .delete()
            .eq('id', id);
        if (error) throw error;
    }
};

// Export default
export default {
    supabase,
    auth: authService,
    clients: clientsService,
    quotes: quotesService,
    invoices: invoicesService,
    settings: settingsService,
    trial: trialService,
    dashboard: dashboardService,
    predefinedItems: predefinedItemsService,
    kits: kitsService
};
