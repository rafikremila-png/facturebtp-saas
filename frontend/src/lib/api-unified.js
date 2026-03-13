/**
 * API Service - Unified interface for FastAPI (preview) or Supabase (production)
 * 
 * In production (Vercel), this uses direct Supabase queries.
 * In preview (with FastAPI backend), this uses axios to call the backend API.
 */

import axios from 'axios';
import { supabase } from '@/supabaseClient';
import supabaseService from './supabaseService';

// Detect if we have a FastAPI backend available
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const USE_FASTAPI = BACKEND_URL && !BACKEND_URL.includes('supabase');

console.log(`[API] Mode: ${USE_FASTAPI ? 'FastAPI Backend' : 'Supabase Direct'}`);
console.log(`[API] Backend URL: ${BACKEND_URL || 'None'}`);

// Axios instance for FastAPI backend (preview mode)
const axiosApi = axios.create({
    baseURL: `${BACKEND_URL}/api`,
});

// Add Supabase token to axios requests
axiosApi.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
});

axiosApi.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            const { data: { session } } = await supabase.auth.getSession();
            if (session) {
                console.log('[API] 401 error with active session - signing out');
                await supabase.auth.signOut();
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// ============== WRAPPER FUNCTIONS ==============
// These functions work with both FastAPI and Supabase

// Helper to wrap Supabase results in axios-like response
const wrapResponse = (data) => ({ data, status: 200 });

// ============== DASHBOARD ==============

export const getDashboard = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/dashboard');
    }
    const data = await supabaseService.dashboard.getStats();
    return wrapResponse(data);
};

// ============== TRIAL & SUBSCRIPTION ==============

export const getTrialStatus = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/trial/status');
    }
    const data = await supabaseService.trial.getStatus();
    return wrapResponse(data);
};

export const getUsageLimits = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/trial/limits');
    }
    const status = await supabaseService.trial.getStatus();
    return wrapResponse({
        quote_limit: status?.quote_limit || 5,
        invoice_limit: status?.invoice_limit || 5,
        quotes_used: status?.quotes_used || 0,
        invoices_used: status?.invoices_used || 0
    });
};

export const checkCanCreate = async (resourceType) => {
    if (USE_FASTAPI) {
        return axiosApi.post(`/trial/check-limit/${resourceType}`);
    }
    const result = await supabaseService.trial.checkLimit(resourceType);
    return wrapResponse(result);
};

export const getSubscriptionPlans = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/subscription/plans');
    }
    // Return static plans for Supabase mode
    return wrapResponse([
        {
            id: "essentiel",
            name: "Essentiel",
            price_monthly: 19,
            description: "Pour les artisans débutants",
            features: {
                unlimited_quotes: true,
                invoices_per_month: 30,
                article_library: true,
                manual_creation: true,
                users: 1,
                predefined_kits: false,
                smart_pricing: false,
                advanced_dashboard: false,
                priority_support: false
            }
        },
        {
            id: "pro",
            name: "Pro",
            price_monthly: 29,
            description: "Pour les professionnels actifs",
            popular: true,
            features: {
                unlimited_quotes: true,
                unlimited_invoices: true,
                article_library: true,
                manual_creation: true,
                users: 1,
                predefined_kits: true,
                smart_pricing: true,
                advanced_dashboard: false,
                priority_support: true
            }
        },
        {
            id: "business",
            name: "Business",
            price_monthly: 59,
            description: "Pour les entreprises en croissance",
            features: {
                unlimited_quotes: true,
                unlimited_invoices: true,
                article_library: true,
                manual_creation: true,
                users: 10,
                predefined_kits: true,
                smart_pricing: true,
                advanced_dashboard: true,
                priority_support: true
            }
        }
    ]);
};

// ============== CLIENTS ==============

export const getClients = async (params) => {
    if (USE_FASTAPI) {
        return axiosApi.get('/clients', { params });
    }
    const data = await supabaseService.clients.getAll();
    return wrapResponse(data);
};

export const getClient = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/clients/${id}`);
    }
    const data = await supabaseService.clients.getById(id);
    return wrapResponse(data);
};

export const createClient = async (clientData) => {
    if (USE_FASTAPI) {
        return axiosApi.post('/clients', clientData);
    }
    const data = await supabaseService.clients.create(clientData);
    return wrapResponse(data);
};

export const updateClient = async (id, clientData) => {
    if (USE_FASTAPI) {
        return axiosApi.put(`/clients/${id}`, clientData);
    }
    const data = await supabaseService.clients.update(id, clientData);
    return wrapResponse(data);
};

export const deleteClient = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.delete(`/clients/${id}`);
    }
    await supabaseService.clients.delete(id);
    return wrapResponse({ success: true });
};

// ============== QUOTES ==============

export const getQuotes = async (params) => {
    if (USE_FASTAPI) {
        return axiosApi.get('/quotes', { params });
    }
    const data = await supabaseService.quotes.getAll(params);
    return wrapResponse(data);
};

export const getQuote = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/quotes/${id}`);
    }
    const data = await supabaseService.quotes.getById(id);
    return wrapResponse(data);
};

export const createQuote = async (quoteData) => {
    if (USE_FASTAPI) {
        return axiosApi.post('/quotes', quoteData);
    }
    const data = await supabaseService.quotes.create(quoteData);
    return wrapResponse(data);
};

export const updateQuote = async (id, quoteData) => {
    if (USE_FASTAPI) {
        return axiosApi.put(`/quotes/${id}`, quoteData);
    }
    const data = await supabaseService.quotes.update(id, quoteData);
    return wrapResponse(data);
};

export const deleteQuote = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.delete(`/quotes/${id}`);
    }
    await supabaseService.quotes.delete(id);
    return wrapResponse({ success: true });
};

export const convertQuoteToInvoice = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.post(`/quotes/${id}/convert`);
    }
    const data = await supabaseService.quotes.convertToInvoice(id);
    return wrapResponse(data);
};

export const getQuotePDF = (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/quotes/${id}/pdf`, { responseType: 'blob' });
    }
    // For Supabase mode, PDF generation would need Edge Function
    throw new Error('PDF generation requires Edge Function in production');
};

// ============== INVOICES ==============

export const getInvoices = async (params) => {
    if (USE_FASTAPI) {
        return axiosApi.get('/invoices', { params });
    }
    const data = await supabaseService.invoices.getAll(params);
    return wrapResponse(data);
};

export const getInvoice = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/invoices/${id}`);
    }
    const data = await supabaseService.invoices.getById(id);
    return wrapResponse(data);
};

export const createInvoice = async (invoiceData) => {
    if (USE_FASTAPI) {
        return axiosApi.post('/invoices', invoiceData);
    }
    const data = await supabaseService.invoices.create(invoiceData);
    return wrapResponse(data);
};

export const updateInvoice = async (id, invoiceData) => {
    if (USE_FASTAPI) {
        return axiosApi.put(`/invoices/${id}`, invoiceData);
    }
    const data = await supabaseService.invoices.update(id, invoiceData);
    return wrapResponse(data);
};

export const deleteInvoice = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.delete(`/invoices/${id}`);
    }
    await supabaseService.invoices.delete(id);
    return wrapResponse({ success: true });
};

export const markInvoicePaid = async (id, amount) => {
    if (USE_FASTAPI) {
        return axiosApi.post(`/invoices/${id}/payment`, { amount });
    }
    const data = await supabaseService.invoices.markAsPaid(id, amount);
    return wrapResponse(data);
};

export const getInvoicePDF = (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/invoices/${id}/pdf`, { responseType: 'blob' });
    }
    throw new Error('PDF generation requires Edge Function in production');
};

// ============== SETTINGS ==============

export const getSettings = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/settings');
    }
    const data = await supabaseService.settings.get();
    return wrapResponse(data || {});
};

export const updateSettings = async (settingsData) => {
    if (USE_FASTAPI) {
        return axiosApi.put('/settings', settingsData);
    }
    const data = await supabaseService.settings.update(settingsData);
    return wrapResponse(data);
};

export const uploadLogo = async (file) => {
    if (USE_FASTAPI) {
        const formData = new FormData();
        formData.append('file', file);
        return axiosApi.post('/settings/logo', formData);
    }
    const url = await supabaseService.settings.uploadLogo(file);
    return wrapResponse({ url });
};

// ============== FINANCIAL REPORTS ==============

export const getFinancialReport = async (params) => {
    if (USE_FASTAPI) {
        return axiosApi.get('/reports/financial', { params });
    }
    const data = await supabaseService.dashboard.getFinancialReport(params?.period);
    return wrapResponse(data);
};

// ============== PREDEFINED ITEMS ==============

export const getCategories = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/categories');
    }
    const data = await supabaseService.predefinedItems.getCategories();
    return wrapResponse(data);
};

export const getPredefinedItems = async (category) => {
    if (USE_FASTAPI) {
        return axiosApi.get('/predefined-items', { params: { category } });
    }
    const data = await supabaseService.predefinedItems.getByCategory(category);
    return wrapResponse(data);
};

export const createPredefinedItem = async (itemData) => {
    if (USE_FASTAPI) {
        return axiosApi.post('/predefined-items', itemData);
    }
    const data = await supabaseService.predefinedItems.create(itemData);
    return wrapResponse(data);
};

export const updatePredefinedItem = async (id, itemData) => {
    if (USE_FASTAPI) {
        return axiosApi.put(`/predefined-items/${id}`, itemData);
    }
    const data = await supabaseService.predefinedItems.update(id, itemData);
    return wrapResponse(data);
};

export const deletePredefinedItem = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.delete(`/predefined-items/${id}`);
    }
    await supabaseService.predefinedItems.delete(id);
    return wrapResponse({ success: true });
};

// ============== KITS ==============

export const getKits = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/kits');
    }
    const data = await supabaseService.kits.getAll();
    return wrapResponse(data);
};

export const getKit = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.get(`/kits/${id}`);
    }
    const data = await supabaseService.kits.getById(id);
    return wrapResponse(data);
};

export const createKit = async (kitData) => {
    if (USE_FASTAPI) {
        return axiosApi.post('/kits', kitData);
    }
    const data = await supabaseService.kits.create(kitData);
    return wrapResponse(data);
};

export const updateKit = async (id, kitData) => {
    if (USE_FASTAPI) {
        return axiosApi.put(`/kits/${id}`, kitData);
    }
    const data = await supabaseService.kits.update(id, kitData);
    return wrapResponse(data);
};

export const deleteKit = async (id) => {
    if (USE_FASTAPI) {
        return axiosApi.delete(`/kits/${id}`);
    }
    await supabaseService.kits.delete(id);
    return wrapResponse({ success: true });
};

// ============== SUBSCRIPTION STATUS ==============

export const getSubscriptionStatus = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/subscription/status');
    }
    const status = await supabaseService.trial.getStatus();
    return wrapResponse({
        plan: status?.plan || 'trial',
        plan_name: status?.plan === 'trial' ? 'Essai' : status?.plan,
        is_trial: status?.is_trial,
        is_active: true,
        trial_days_remaining: status?.days_remaining,
        invoices_this_month: status?.invoices_used,
        invoices_limit: status?.invoice_limit
    });
};

// ============== PROFILE ==============

export const getProfile = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/auth/profile');
    }
    const user = await supabaseService.auth.getUser();
    return wrapResponse(user);
};

export const updateProfile = async (profileData) => {
    if (USE_FASTAPI) {
        return axiosApi.put('/auth/profile', profileData);
    }
    const { data: { user } } = await supabase.auth.getUser();
    const { data } = await supabase
        .from('users')
        .update(profileData)
        .eq('id', user.id)
        .select()
        .single();
    return wrapResponse(data);
};

export const getProfileCompletion = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/profile/completion');
    }
    const user = await supabaseService.auth.getUser();
    const fields = ['name', 'phone', 'company_name', 'address', 'siret'];
    const completed = fields.filter(f => user && user[f]).length;
    return wrapResponse({
        percentage: Math.round((completed / fields.length) * 100),
        completed_fields: completed,
        total_fields: fields.length
    });
};

// ============== SAAS USAGE ==============

export const getSaasUsage = async () => {
    if (USE_FASTAPI) {
        return axiosApi.get('/saas/usage');
    }
    const status = await supabaseService.trial.getStatus();
    return wrapResponse({
        quotes_used: status?.quotes_used || 0,
        quotes_limit: status?.quote_limit || 5,
        invoices_used: status?.invoices_used || 0,
        invoices_limit: status?.invoice_limit || 5
    });
};

// Export axios instance for backward compatibility
export const api = axiosApi;
export default api;
