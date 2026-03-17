/**
 * API layer - Supabase-only mode
 * Wraps supabaseService calls to match the axios response format ({ data: ... })
 * that all page components expect.
 */

import { supabase } from '@/supabaseClient';
import {
    clientsService,
    quotesService,
    invoicesService,
    settingsService,
    trialService,
    dashboardService,
    predefinedItemsService,
    kitsService,
    proServicesService,
} from '@/lib/supabaseService';

// Helper: wrap a promise result in axios-style { data: result }
const wrap = async (promise) => {
    const result = await promise;
    return { data: result };
};

// Helper: get current user id
const getUserId = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    return user?.id;
};

// Helper: get user profile from public.users
const getUserProfile = async (userId) => {
    const uid = userId || await getUserId();
    if (!uid) return null;
    const { data } = await supabase.from('users').select('*').eq('id', uid).single();
    return data;
};

// ============== DASHBOARD ==============
export const getDashboard = () => wrap(dashboardService.getStats());

// ============== TRIAL & LIMITS ==============
export const getTrialStatus = () => wrap(trialService.getStatus());

export const getUsageLimits = async () => {
    const status = await trialService.getStatus();
    return {
        data: {
            quote_limit: status?.quote_limit || 5,
            invoice_limit: status?.invoice_limit || 5,
            quotes_used: status?.quotes_used || 0,
            invoices_used: status?.invoices_used || 0,
        }
    };
};

export const checkCanCreate = async (resourceType) => {
    const result = await trialService.checkLimit(resourceType);
    return { data: result };
};

export const getSubscriptionPlans = async () => {
    return {
        data: [
            { id: 'trial', name: 'Essai', price_monthly: 0, price_yearly: 0, features: ['5 devis', '5 factures'] },
            { id: 'essentiel', name: 'Essentiel', price_monthly: 29, price_yearly: 290, features: ['Devis illimités', 'Factures illimitées'] },
            { id: 'pro', name: 'Pro', price_monthly: 49, price_yearly: 490, features: ['Tout Essentiel', 'Relances auto', 'Export CSV'] },
            { id: 'business', name: 'Business', price_monthly: 99, price_yearly: 990, features: ['Tout Pro', 'Multi-utilisateurs', 'API'] },
        ]
    };
};

// ============== CLIENTS ==============
export const getClients = () => wrap(clientsService.getAll());
export const getClient = (id) => wrap(clientsService.getById(id));
export const createClient = (data) => wrap(clientsService.create(data));
export const updateClient = (id, data) => wrap(clientsService.update(id, data));
export const deleteClient = (id) => wrap(clientsService.delete(id));

// ============== QUOTES ==============
export const getQuotes = async (status, clientId) => {
    const filters = {};
    if (status) filters.status = status;
    if (clientId) filters.client_id = clientId;
    return wrap(quotesService.getAll(filters));
};
export const getQuote = (id) => wrap(quotesService.getById(id));
export const createQuote = (data) => wrap(quotesService.create(data));
export const updateQuote = (id, data) => wrap(quotesService.update(id, data));
export const deleteQuote = (id) => wrap(quotesService.delete(id));
export const bulkDeleteQuotes = async (ids) => {
    for (const id of ids) { await quotesService.delete(id); }
    return { data: { deleted: ids.length } };
};
export const convertQuoteToInvoice = (id) => wrap(quotesService.convertToInvoice(id));

// PDF downloads - now handled by pdfGenerator.js directly in components
export const downloadQuotePdf = async (id) => {
    console.warn('[API] Use pdfGenerator.js directly for PDF generation');
    return { data: null };
};

// ============== INVOICES ==============
export const getInvoices = async (paymentStatus, clientId) => {
    const filters = {};
    if (paymentStatus) filters.payment_status = paymentStatus;
    if (clientId) filters.client_id = clientId;
    return wrap(invoicesService.getAll(filters));
};
export const getInvoice = (id) => wrap(invoicesService.getById(id));
export const createInvoice = (data) => wrap(invoicesService.create(data));
export const updateInvoice = (id, data) => wrap(invoicesService.update(id, data));
export const deleteInvoice = (id) => wrap(invoicesService.delete(id));
export const bulkDeleteInvoices = async (ids) => {
    for (const id of ids) { await invoicesService.delete(id); }
    return { data: { deleted: ids.length } };
};

export const downloadInvoicePdf = async (id) => {
    console.warn('[API] Use pdfGenerator.js directly for PDF generation');
    return { data: null };
};

// ============== RETENUE DE GARANTIE ==============
export const applyRetenueGarantie = async (invoiceId, data) => {
    return wrap(invoicesService.update(invoiceId, {
        retention_rate: data.rate || data.retention_rate,
        retention_amount: data.amount || data.retention_amount,
    }));
};
export const removeRetenueGarantie = async (invoiceId) => {
    return wrap(invoicesService.update(invoiceId, {
        retention_rate: null,
        retention_amount: null,
        retention_released: false,
    }));
};
export const releaseRetenueGarantie = async (invoiceId) => {
    return wrap(invoicesService.update(invoiceId, { retention_released: true }));
};
export const getQuoteRetenuesSummary = async (quoteId) => {
    return { data: { retenues: [], total_retained: 0, total_released: 0 } };
};

// ============== PROJECT FINANCIAL SUMMARY ==============
export const getProjectFinancialSummary = async (quoteId) => {
    const quote = await quotesService.getById(quoteId);
    return {
        data: {
            quote,
            invoices: [],
            total_invoiced: 0,
            total_paid: 0,
            remaining: quote?.total_ttc || 0,
        }
    };
};
export const getPublicFinancialSummary = async (shareToken) => {
    return { data: null };
};
export const downloadFinancialSummaryPdf = async () => {
    throw new Error('La génération de PDF sera disponible prochainement.');
};

// ============== SETTINGS ==============
export const getSettings = async () => {
    const data = await settingsService.get();
    // Mapper company_logo_url vers logo_base64 pour compatibilité frontend
    if (data && data.company_logo_url) {
        data.logo_base64 = data.company_logo_url;
    }
    return { data: data || {} };
};
export const updateSettings = (data) => wrap(settingsService.update(data));
export const uploadLogo = async (file) => {
    // Use backend endpoint to bypass Storage RLS
    const API_URL = process.env.REACT_APP_BACKEND_URL;
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session?.access_token) {
        throw new Error('Not authenticated');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/api/settings/upload-logo`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
    });
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.error || 'Upload failed');
    }
    
    return { data: { logo: result.url } };
};

// ============== PREDEFINED ITEMS ==============
export const getPredefinedCategories = async () => {
    const cats = await predefinedItemsService.getCategories();
    return { data: cats };
};
export const getPredefinedItems = async (category) => {
    const items = await predefinedItemsService.getByCategory(category);
    return { data: items };
};
export const createPredefinedItem = (data) => wrap(predefinedItemsService.create(data));
export const updatePredefinedItem = (id, data) => wrap(predefinedItemsService.update(id, data));
export const deletePredefinedItem = (id) => wrap(predefinedItemsService.delete(id));
export const resetPredefinedItems = async () => { return { data: { message: 'OK' } }; };

// ============== CATEGORIES (V3 - simplified) ==============
export const getDynamicCategories = async () => {
    const cats = await predefinedItemsService.getCategories();
    return { data: cats.map((c, i) => ({ id: i, name: c })) };
};
export const getDynamicCategoriesWithItems = async () => {
    const cats = await predefinedItemsService.getCategories();
    const result = [];
    for (const cat of cats) {
        const rawItems = await predefinedItemsService.getByCategory(cat);
        const items = (rawItems || []).map(item => ({
            ...item,
            name: item.description || item.name || '',
            smart_price: item.default_price || 0,
        }));
        result.push({ id: cat, name: cat, items });
    }
    return { data: result };
};
export const getDynamicCategoryItems = async (categoryId) => {
    return wrap(predefinedItemsService.getByCategory(categoryId));
};
export const searchCategoryItems = async (query) => {
    const { data } = await supabase
        .from('predefined_items')
        .select('*')
        .ilike('description', `%${query}%`)
        .limit(20);
    return { data: data || [] };
};
export const getBusinessTypes = async () => {
    return { data: ['Maçonnerie', 'Peinture', 'Plomberie', 'Électricité', 'Carrelage', 'Menuiserie', 'Rénovation générale'] };
};
export const getCategoriesV3 = getDynamicCategories;
export const getCategoriesWithItemsV3 = getDynamicCategoriesWithItems;
export const getCategoryV3 = getDynamicCategoryItems;
export const getCategoryItemsV3 = getDynamicCategoryItems;
export const getItemV3 = async (itemId) => {
    const { data } = await supabase.from('predefined_items').select('*').eq('id', itemId).single();
    return { data };
};
export const searchItemsV3 = searchCategoryItems;
export const getKitsV3 = async () => {
    const rawKits = await kitsService.getAll();
    const kits = (rawKits || []).map(k => ({
        ...k,
        business_type: 'general',
    }));
    return { data: kits };
};
export const getKitV3 = async (kitId) => {
    const rawKit = await kitsService.getById(kitId);
    const kitItems = Array.isArray(rawKit.items) ? rawKit.items : JSON.parse(rawKit.items || '[]');
    const expandedItems = kitItems.map(item => ({
        ...item,
        total: (item.quantity || 1) * (item.unit_price || 0),
    }));
    const totalHt = expandedItems.reduce((sum, i) => sum + i.total, 0);
    return { data: { ...rawKit, expanded_items: expandedItems, total_ht: totalHt } };
};
export const seedCategoriesV3 = async () => { return { data: { message: 'OK' } }; };

// ============== KITS ==============
export const getKits = () => wrap(kitsService.getAll());
export const getKit = (id) => wrap(kitsService.getById(id));
export const createKit = (data) => wrap(kitsService.create(data));
export const updateKit = (id, data) => wrap(kitsService.update(id, data));
export const deleteKit = (id) => wrap(kitsService.delete(id));
export const createKitFromQuote = async (quoteId, name, description = "") => {
    const quote = await quotesService.getById(quoteId);
    return wrap(kitsService.create({ name, description, items: quote?.items || [] }));
};
export const resetKits = async () => { return { data: { message: 'OK' } }; };

// ============== SHARE LINKS ==============
export const createQuoteShareLink = async (quoteId) => {
    const quote = await quotesService.getById(quoteId);
    if (quote?.share_token) return { data: { token: quote.share_token } };
    const token = crypto.randomUUID();
    await quotesService.update(quoteId, { share_token: token });
    return { data: { token } };
};
export const revokeQuoteShareLink = async (quoteId) => {
    await quotesService.update(quoteId, { share_token: null });
    return { data: { message: 'OK' } };
};
export const createInvoiceShareLink = async (invoiceId) => {
    const inv = await invoicesService.getById(invoiceId);
    if (inv?.share_token) return { data: { token: inv.share_token } };
    const token = crypto.randomUUID();
    await invoicesService.update(invoiceId, { share_token: token });
    return { data: { token } };
};
export const revokeInvoiceShareLink = async (invoiceId) => {
    await invoicesService.update(invoiceId, { share_token: null });
    return { data: { message: 'OK' } };
};

// ============== ACOMPTES & SITUATIONS ==============
export const createAcompte = async (quoteId, data) => {
    // Create a partial invoice from quote
    const quote = await quotesService.getById(quoteId);
    return wrap(invoicesService.create({
        client_id: quote?.client_id,
        client_name: quote?.client_name,
        quote_id: quoteId,
        items: [{ description: `Acompte - ${quote?.quote_number}`, quantity: 1, unit_price: data.amount || 0, vat_rate: 20 }],
        total_ht: data.amount || 0,
        total_ttc: (data.amount || 0) * 1.2,
        total_vat: (data.amount || 0) * 0.2,
        invoice_type: 'acompte',
        payment_status: 'unpaid',
    }));
};
export const getQuoteAcomptes = async (quoteId) => {
    const { data } = await supabase.from('invoices').select('*').eq('quote_id', quoteId).eq('invoice_type', 'acompte');
    return { data: data || [] };
};
export const getAcomptesSummary = async (quoteId) => {
    const { data: invoices } = await supabase.from('invoices').select('*').eq('quote_id', quoteId);
    const total = (invoices || []).reduce((s, i) => s + (i.total_ttc || 0), 0);
    return { data: { invoices: invoices || [], total_invoiced: total } };
};
export const createFinalInvoice = async (quoteId) => {
    const quote = await quotesService.getById(quoteId);
    return wrap(invoicesService.create({
        client_id: quote?.client_id,
        client_name: quote?.client_name,
        quote_id: quoteId,
        items: quote?.items,
        total_ht: quote?.total_ht,
        total_ttc: quote?.total_ttc,
        total_vat: quote?.total_vat,
        invoice_type: 'final',
        payment_status: 'unpaid',
    }));
};
export const createSituation = createAcompte;
export const getQuoteSituations = getQuoteAcomptes;
export const getSituationsSummary = getAcomptesSummary;
export const createSituationFinalInvoice = createFinalInvoice;

// ============== PUBLIC ENDPOINTS ==============
export const getPublicQuote = async (token) => {
    const { data } = await supabase.from('quotes').select('*').eq('share_token', token).single();
    return { data };
};
export const getPublicInvoice = async (token) => {
    const { data } = await supabase.from('invoices').select('*').eq('share_token', token).single();
    return { data };
};
export const downloadPublicQuotePdf = async () => {
    throw new Error('La génération de PDF sera disponible prochainement.');
};
export const downloadPublicInvoicePdf = async () => {
    throw new Error('La génération de PDF sera disponible prochainement.');
};

// ============== EMAIL ==============
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session?.access_token || ''}`,
    };
};

export const sendQuoteEmail = async (quoteId, clientEmail) => {
    // Quotes don't have a dedicated email endpoint yet - use invoice endpoint pattern
    throw new Error("L'envoi de devis par email sera disponible prochainement.");
};

export const sendInvoiceEmail = async (invoiceId, clientEmail) => {
    const headers = await getAuthHeaders();
    const resp = await fetch(`${BACKEND_URL}/api/email/invoice`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ invoice_id: invoiceId, client_email: clientEmail }),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Erreur lors de l'envoi de l'email");
    }
    return { data: await resp.json() };
};

export const sendPaymentConfirmation = async (invoiceId) => {
    const headers = await getAuthHeaders();
    const resp = await fetch(`${BACKEND_URL}/api/email/payment-confirmation`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ invoice_id: invoiceId }),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Erreur lors de l'envoi");
    }
    return { data: await resp.json() };
};

export const getEmailStatus = async () => {
    try {
        const resp = await fetch(`${BACKEND_URL}/api/email/status`);
        return { data: await resp.json() };
    } catch {
        return { data: { configured: false, provider: 'none' } };
    }
};

// ============== USER MANAGEMENT (ADMIN) ==============
export const getUsers = async () => {
    const { data } = await supabase.from('users').select('*').order('created_at', { ascending: false });
    return { data: data || [] };
};
export const getUser = async (userId) => {
    const { data } = await supabase.from('users').select('*').eq('id', userId).single();
    return { data };
};
export const updateUserRole = async (userId, role) => {
    const { data } = await supabase.from('users').update({ role }).eq('id', userId).select().single();
    return { data };
};
export const activateUser = async (userId) => {
    const { data } = await supabase.from('users').update({ is_active: true }).eq('id', userId).select().single();
    return { data };
};
export const deactivateUser = async (userId) => {
    const { data } = await supabase.from('users').update({ is_active: false }).eq('id', userId).select().single();
    return { data };
};
export const deleteUser = async (userId) => {
    await supabase.from('users').delete().eq('id', userId);
    return { data: { message: 'OK' } };
};

// ============== SUBSCRIPTION & BILLING ==============
export const getSubscriptionStatus = async () => {
    const status = await trialService.getStatus();
    return { data: status };
};
export const createCheckoutSession = async (planId, originUrl) => {
    // Stripe checkout stub - requires backend
    return { data: { url: originUrl + '?plan=' + planId, session_id: 'stub' } };
};
export const checkCheckoutStatus = async (sessionId) => {
    return { data: { status: 'pending' } };
};
export const cancelSubscription = async () => {
    return { data: { message: 'OK' } };
};
export const checkFeatureAccess = async (feature) => {
    return { data: { allowed: true } };
};
export const getSaaSPlans = getSubscriptionPlans;
export const getSaaSSubscription = getSubscriptionStatus;
export const getUsageStats = getUsageLimits;
export const createSaaSCheckout = createCheckoutSession;
export const cancelSaaSSubscription = cancelSubscription;
export const checkSaaSFeature = checkFeatureAccess;

// ============== REMINDERS ==============
export const getReminderStats = async () => {
    const { data: invoices } = await supabase
        .from('invoices')
        .select('id, payment_status, reminder_count, due_date')
        .in('payment_status', ['unpaid', 'impaye', 'en_attente']);
    const all = invoices || [];
    const sent = all.filter(i => (i.reminder_count || 0) > 0).length;
    const pending = all.filter(i => (i.reminder_count || 0) === 0).length;
    return { data: { total: all.length, sent, pending } };
};
export const getPendingReminders = async () => {
    const { data } = await supabase
        .from('invoices')
        .select('*')
        .in('payment_status', ['unpaid', 'impaye', 'en_attente'])
        .not('due_date', 'is', null)
        .order('due_date', { ascending: true });
    return { data: data || [] };
};
export const sendReminder = async (invoiceId) => {
    const headers = await getAuthHeaders();
    const resp = await fetch(`${BACKEND_URL}/api/email/reminder`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ invoice_id: invoiceId }),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Erreur lors de l'envoi du rappel");
    }
    return { data: await resp.json() };
};
export const getReminderHistory = async () => {
    const { data } = await supabase
        .from('invoices')
        .select('id, invoice_number, client_name, reminder_count, last_reminder_at')
        .gt('reminder_count', 0)
        .order('last_reminder_at', { ascending: false });
    return { data: data || [] };
};
export const triggerReminderCheck = async () => {
    const headers = await getAuthHeaders();
    const resp = await fetch(`${BACKEND_URL}/api/email/check-reminders`, {
        method: 'POST',
        headers,
    });
    return { data: await resp.json() };
};

// ============== CSV EXPORT (client-side) ==============
export { exportClientsCSV, exportQuotesCSV, exportInvoicesCSV } from '@/lib/csvExport';
export const exportAccountingCSV = async () => { throw new Error('Export comptable sera disponible prochainement.'); };

// ============== DEFAULT EXPORT (for api.get/post/put/delete pattern) ==============
// This provides backward compatibility for pages that use api.get('/some/path')
const apiProxy = {
    get: async (path, config = {}) => {
        const url = path.replace(/^\//, '');

        // Admin metrics
        if (url.startsWith('admin/metrics')) {
            return wrap(getAdminMetrics());
        }
        // Financial reports
        if (url.startsWith('reports/financial')) {
            const period = config?.params?.period || 'year';
            return wrap(dashboardService.getFinancialReport(period));
        }
        // Auth profile
        if (url === 'auth/profile') {
            const profile = await getUserProfile();
            return { data: profile };
        }
        // Users
        if (url === 'users') {
            return getUsers();
        }
        if (url.match(/^users\/[^/]+$/)) {
            const userId = url.split('/')[1];
            return getUser(userId);
        }
        if (url.match(/^users\/[^/]+\/profile-completion$/)) {
            return { data: { completion: 100 } };
        }
        // Settings
        if (url === 'settings') {
            return getSettings();
        }
        // Clients
        if (url === 'clients') {
            return getClients();
        }
        // Projects
        if (url === 'projects') {
            const { data } = await supabase.from('quotes').select('*').order('created_at', { ascending: false });
            return { data: data || [] };
        }
        // Work items
        if (url === 'work-items') {
            const { data } = await supabase.from('predefined_items').select('*').order('category');
            const items = (data || []).map(item => ({
                ...item,
                name: item.description || '',
                unit_price: item.default_price || 0,
                vat_rate: item.default_vat_rate || 20,
            }));
            return { data: items };
        }
        if (url === 'work-items/categories') {
            const cats = await predefinedItemsService.getCategories();
            return { data: { categories: cats } };
        }
        if (url === 'work-items/units') {
            return { data: ['m²', 'm', 'ml', 'u', 'forfait', 'kg', 'L', 'h', 'lot'] };
        }
        // Services catalog
        if (url === 'services/catalog') {
            return wrap(proServicesService.getCatalog());
        }
        if (url === 'services/requests/me') {
            return wrap(proServicesService.getMyRequests());
        }
        // Trial
        if (url === 'trial/status') {
            return getTrialStatus();
        }
        if (url === 'trial/limits') {
            return getUsageLimits();
        }

        // Auth impersonation status
        if (url === 'auth/impersonation-status') {
            return { data: { is_impersonating: false } };
        }
        // Profile completion
        if (url === 'profile/completion') {
            return { data: { completion: 100 } };
        }

        console.warn(`[API Proxy] Unhandled GET: ${url}`);
        return { data: null };
    },

    post: async (path, data = {}, config = {}) => {
        const url = path.replace(/^\//, '');

        // Auth
        if (url.match(/^users\/[^/]+\/request-otp/)) {
            return { data: { message: 'OTP envoyé' } };
        }
        if (url === 'admin/impersonate') {
            return { data: { message: 'Non disponible en mode Supabase' } };
        }
        if (url.match(/^users\/[^/]+\/reset-password/)) {
            return { data: { message: 'OK' } };
        }
        // Projects
        if (url === 'projects') {
            const userId = await getUserId();
            const { data: result } = await supabase.from('quotes').insert({ ...data, user_id: userId }).select().single();
            return { data: result };
        }
        // Work items
        if (url === 'work-items') {
            // Map UI field names to DB column names
            const dbData = {
                description: data.name || data.description || '',
                category: data.category || 'autres',
                unit: data.unit || 'u',
                default_price: data.unit_price ?? data.default_price ?? 0,
                default_vat_rate: data.vat_rate ?? data.default_vat_rate ?? 20,
            };
            return createPredefinedItem(dbData);
        }
        if (url.match(/^work-items\/[^/]+\/duplicate$/)) {
            const itemId = url.split('/')[1];
            const { data: item } = await supabase.from('predefined_items').select('*').eq('id', itemId).single();
            if (item) {
                const { id, created_at, updated_at, ...rest } = item;
                return createPredefinedItem({ ...rest, user_id: undefined });
            }
            return { data: null };
        }
        // Services
        if (url === 'services/request') {
            return { data: { message: 'OK' } };
        }
        // Trial
        if (url.startsWith('trial/check-limit/')) {
            const type = url.split('/').pop();
            return checkCanCreate(type);
        }
        // AI endpoints (stubs)
        if (url.startsWith('ai/')) {
            throw new Error("L'assistant IA sera disponible prochainement.");
        }

        console.warn(`[API Proxy] Unhandled POST: ${url}`);
        return { data: null };
    },

    put: async (path, data = {}) => {
        const url = path.replace(/^\//, '');

        // Auth profile
        if (url === 'auth/profile') {
            const userId = await getUserId();
            const { data: result } = await supabase.from('users').update(data).eq('id', userId).select().single();
            return { data: result };
        }
        // Projects
        if (url.match(/^projects\/[^/]+$/)) {
            const id = url.split('/')[1];
            const { data: result } = await supabase.from('quotes').update(data).eq('id', id).select().single();
            return { data: result };
        }
        // Work items
        if (url.match(/^work-items\/[^/]+$/)) {
            const id = url.split('/')[1];
            // Map UI field names to DB column names
            const dbData = {
                description: data.name || data.description || '',
                category: data.category || 'autres',
                unit: data.unit || 'u',
                default_price: data.unit_price ?? data.default_price ?? 0,
                default_vat_rate: data.vat_rate ?? data.default_vat_rate ?? 20,
            };
            return updatePredefinedItem(id, dbData);
        }
        // Settings
        if (url === 'settings') {
            return updateSettings(data);
        }

        console.warn(`[API Proxy] Unhandled PUT: ${url}`);
        return { data: null };
    },

    patch: async (path, data = {}) => {
        const url = path.replace(/^\//, '');

        if (url.match(/^users\/[^/]+\/role$/)) {
            const userId = url.split('/')[1];
            return updateUserRole(userId, data.role);
        }
        if (url.match(/^users\/[^/]+\/activate$/)) {
            const userId = url.split('/')[1];
            return activateUser(userId);
        }
        if (url.match(/^users\/[^/]+\/deactivate$/)) {
            const userId = url.split('/')[1];
            return deactivateUser(userId);
        }

        console.warn(`[API Proxy] Unhandled PATCH: ${url}`);
        return { data: null };
    },

    delete: async (path, config = {}) => {
        const url = path.replace(/^\//, '');

        if (url.match(/^users\/[^/]+$/)) {
            const userId = url.split('/')[1];
            return deleteUser(userId);
        }
        if (url.match(/^projects\/[^/]+$/)) {
            const id = url.split('/')[1];
            await supabase.from('quotes').delete().eq('id', id);
            return { data: { message: 'OK' } };
        }
        if (url.match(/^work-items\/[^/]+$/)) {
            const id = url.split('/')[1];
            return deletePredefinedItem(id);
        }

        console.warn(`[API Proxy] Unhandled DELETE: ${url}`);
        return { data: null };
    },
};

// Admin metrics aggregation (reads from Supabase directly)
async function getAdminMetrics() {
    const [usersRes, quotesRes, invoicesRes] = await Promise.all([
        supabase.from('users').select('*'),
        supabase.from('quotes').select('id, total_ttc, status, created_at'),
        supabase.from('invoices').select('id, total_ttc, payment_status, paid_amount, created_at'),
    ]);

    const users = usersRes.data || [];
    const quotes = quotesRes.data || [];
    const invoices = invoicesRes.data || [];

    const activeUsers = users.filter(u => u.is_active !== false);
    const trialUsers = users.filter(u => u.subscription_plan === 'trial' || !u.subscription_plan);
    const paidUsers = users.filter(u => u.subscription_plan && u.subscription_plan !== 'trial');

    const totalRevenue = invoices
        .filter(i => i.payment_status === 'paid' || i.payment_status === 'paye')
        .reduce((s, i) => s + (i.paid_amount || i.total_ttc || 0), 0);

    return {
        total_users: users.length,
        active_users: activeUsers.length,
        trial_users: trialUsers.length,
        paid_users: paidUsers.length,
        total_quotes: quotes.length,
        total_invoices: invoices.length,
        total_revenue: totalRevenue,
        mrr: 0,
        conversion_rate: users.length > 0 ? (paidUsers.length / users.length * 100).toFixed(1) : 0,
        users_by_plan: {
            trial: trialUsers.length,
            essentiel: paidUsers.filter(u => u.subscription_plan === 'essentiel').length,
            pro: paidUsers.filter(u => u.subscription_plan === 'pro').length,
            business: paidUsers.filter(u => u.subscription_plan === 'business').length,
        },
        recent_users: users.slice(0, 10),
    };
}

export default apiProxy;
