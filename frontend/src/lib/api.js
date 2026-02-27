import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

const api = axios.create({
    baseURL: API,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Dashboard
export const getDashboard = () => api.get('/dashboard');

// Clients
export const getClients = () => api.get('/clients');
export const getClient = (id) => api.get(`/clients/${id}`);
export const createClient = (data) => api.post('/clients', data);
export const updateClient = (id, data) => api.put(`/clients/${id}`, data);
export const deleteClient = (id) => api.delete(`/clients/${id}`);

// Quotes
export const getQuotes = (status, clientId) => api.get('/quotes', { params: { status, client_id: clientId } });
export const getQuote = (id) => api.get(`/quotes/${id}`);
export const createQuote = (data) => api.post('/quotes', data);
export const updateQuote = (id, data) => api.put(`/quotes/${id}`, data);
export const deleteQuote = (id) => api.delete(`/quotes/${id}`);
export const bulkDeleteQuotes = (ids) => api.post('/quotes/bulk-delete', { ids });
export const convertQuoteToInvoice = (id) => api.post(`/quotes/${id}/convert`);
export const downloadQuotePdf = async (id, quoteNumber) => {
    const response = await api.get(`/quotes/${id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `devis_${quoteNumber}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

// Invoices
export const getInvoices = (paymentStatus, clientId) => api.get('/invoices', { params: { payment_status: paymentStatus, client_id: clientId } });
export const getInvoice = (id) => api.get(`/invoices/${id}`);
export const createInvoice = (data) => api.post('/invoices', data);
export const updateInvoice = (id, data) => api.put(`/invoices/${id}`, data);
export const deleteInvoice = (id) => api.delete(`/invoices/${id}`);
export const bulkDeleteInvoices = (ids) => api.post('/invoices/bulk-delete', { ids });

// Retenue de garantie (Retention Guarantee)
export const applyRetenueGarantie = (invoiceId, data) => api.post(`/invoices/${invoiceId}/retenue-garantie`, data);
export const removeRetenueGarantie = (invoiceId) => api.delete(`/invoices/${invoiceId}/retenue-garantie`);
export const releaseRetenueGarantie = (invoiceId) => api.post(`/invoices/${invoiceId}/retenue-garantie/release`);
export const getQuoteRetenuesSummary = (quoteId) => api.get(`/quotes/${quoteId}/retenues-garantie/summary`);

// Project Financial Summary
export const getProjectFinancialSummary = (quoteId) => api.get(`/quotes/${quoteId}/financial-summary`);
export const getPublicFinancialSummary = (shareToken) => api.get(`/public/quote/${shareToken}/financial-summary`);
export const downloadFinancialSummaryPdf = async (quoteId, quoteNumber) => {
    const response = await api.get(`/quotes/${quoteId}/financial-summary/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Recapitulatif_financier_${quoteNumber}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

export const downloadInvoicePdf = async (id, invoiceNumber) => {
    const response = await api.get(`/invoices/${id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `facture_${invoiceNumber}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

// Settings
export const getSettings = () => api.get('/settings');
export const updateSettings = (data) => api.put('/settings', data);
export const uploadLogo = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};

// Predefined Items (Legacy - for backward compatibility)
export const getPredefinedCategories = () => api.get('/predefined-items/categories');
export const getPredefinedItems = (category) => api.get('/predefined-items', { params: { category } });
export const createPredefinedItem = (data) => api.post('/predefined-items', data);
export const updatePredefinedItem = (id, data) => api.put(`/predefined-items/${id}`, data);
export const deletePredefinedItem = (id) => api.delete(`/predefined-items/${id}`);
export const resetPredefinedItems = () => api.post('/predefined-items/reset');

// Dynamic Service Categories (New system - filtered by business_type)
export const getDynamicCategories = () => api.get('/categories');
export const getDynamicCategoriesWithItems = () => api.get('/categories/with-items');
export const getDynamicCategoryItems = (categoryId) => api.get(`/categories/${categoryId}/items`);
export const searchCategoryItems = (query) => api.get('/categories/search/items', { params: { q: query } });
export const getBusinessTypes = () => api.get('/business-types');

// Service Categories V3 (Simplified - No Subcategories, Enriched Library)
export const getCategoriesV3 = () => api.get('/v3/categories');
export const getCategoriesWithItemsV3 = () => api.get('/v3/categories/with-items');
export const getCategoryV3 = (categoryId) => api.get(`/v3/categories/${categoryId}`);
export const getCategoryItemsV3 = (categoryId) => api.get(`/v3/categories/${categoryId}/items`);
export const getItemV3 = (itemId) => api.get(`/v3/items/${itemId}`);
export const searchItemsV3 = (query) => api.get('/v3/items/search', { params: { q: query } });
export const getKitsV3 = () => api.get('/v3/kits');
export const getKitV3 = (kitId) => api.get(`/v3/kits/${kitId}`);
export const seedCategoriesV3 = (force = false) => api.post(`/v3/categories/seed?force=${force}`);

// Renovation Kits
export const getKits = () => api.get('/kits');
export const getKit = (id) => api.get(`/kits/${id}`);
export const createKit = (data) => api.post('/kits', data);
export const updateKit = (id, data) => api.put(`/kits/${id}`, data);
export const deleteKit = (id) => api.delete(`/kits/${id}`);
export const createKitFromQuote = (quoteId, name, description = "") => 
    api.post(`/kits/from-quote/${quoteId}`, null, { params: { kit_name: name, kit_description: description } });
export const resetKits = () => api.post('/kits/reset');

// Share Links
export const createQuoteShareLink = (quoteId) => api.post(`/quotes/${quoteId}/share`);
export const revokeQuoteShareLink = (quoteId) => api.delete(`/quotes/${quoteId}/share`);
export const createInvoiceShareLink = (invoiceId) => api.post(`/invoices/${invoiceId}/share`);
export const revokeInvoiceShareLink = (invoiceId) => api.delete(`/invoices/${invoiceId}/share`);

// Acomptes (Advance Payments)
export const createAcompte = (quoteId, data) => api.post(`/quotes/${quoteId}/acompte`, data);
export const getQuoteAcomptes = (quoteId) => api.get(`/quotes/${quoteId}/acomptes`);
export const getAcomptesSummary = (quoteId) => api.get(`/quotes/${quoteId}/acomptes/summary`);
export const createFinalInvoice = (quoteId) => api.post(`/quotes/${quoteId}/final-invoice`);

// Situations (Progressive Billing)
export const createSituation = (quoteId, data) => api.post(`/quotes/${quoteId}/situation`, data);
export const getQuoteSituations = (quoteId) => api.get(`/quotes/${quoteId}/situations`);
export const getSituationsSummary = (quoteId) => api.get(`/quotes/${quoteId}/situations/summary`);
export const createSituationFinalInvoice = (quoteId) => api.post(`/quotes/${quoteId}/situation/final-invoice`);

// Public endpoints (no auth)
export const getPublicQuote = (token) => axios.get(`${API}/public/quote/${token}`);
export const getPublicInvoice = (token) => axios.get(`${API}/public/invoice/${token}`);
export const downloadPublicQuotePdf = async (token) => {
    const response = await axios.get(`${API}/public/quote/${token}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `devis.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};
export const downloadPublicInvoicePdf = async (token) => {
    const response = await axios.get(`${API}/public/invoice/${token}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `facture.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

// Email
export const sendQuoteEmail = (quoteId, data) => api.post(`/quotes/${quoteId}/send-email`, data);
export const sendInvoiceEmail = (invoiceId, data) => api.post(`/invoices/${invoiceId}/send-email`, data);
export const getEmailStatus = () => api.get('/email/status');

// ============== USER MANAGEMENT (ADMIN ONLY) ==============

// List all users
export const getUsers = () => api.get('/users');

// Get single user
export const getUser = (userId) => api.get(`/users/${userId}`);

// Update user role
export const updateUserRole = (userId, role) => api.patch(`/users/${userId}/role`, { role });

// Activate user
export const activateUser = (userId) => api.patch(`/users/${userId}/activate`);

// Deactivate user
export const deactivateUser = (userId) => api.patch(`/users/${userId}/deactivate`);

// Delete user (super admin only)
export const deleteUser = (userId) => api.delete(`/users/${userId}`);

// ============== SUBSCRIPTION & BILLING ==============

// Get available subscription plans
export const getSubscriptionPlans = () => api.get('/subscription/plans');

// Get current subscription status
export const getSubscriptionStatus = () => api.get('/subscription/status');

// Create checkout session for a plan
export const createCheckoutSession = (planId, originUrl) => api.post('/subscription/checkout', { plan_id: planId, origin_url: originUrl });

// Check checkout session status
export const checkCheckoutStatus = (sessionId) => api.get(`/subscription/checkout/status/${sessionId}`);

// Cancel subscription
export const cancelSubscription = () => api.post('/subscription/cancel');

// Check feature access
export const checkFeatureAccess = (feature) => api.get(`/subscription/features/${feature}`);

// ============== SAAS / NEW SUBSCRIPTION SYSTEM ==============

// Get SaaS plans with full details
export const getSaaSPlans = () => api.get('/saas/plans');

// Get user's subscription info with usage
export const getSaaSSubscription = () => api.get('/saas/subscription');

// Get usage stats (quotes/invoices this month)
export const getUsageStats = () => api.get('/saas/usage');

// Create checkout session for SaaS plan
export const createSaaSCheckout = (planId, billingPeriod, originUrl) => 
    api.post('/saas/checkout', { plan_id: planId, billing_period: billingPeriod, origin_url: originUrl });

// Cancel SaaS subscription
export const cancelSaaSSubscription = () => api.post('/saas/cancel');

// Check SaaS feature access
export const checkSaaSFeature = (feature) => api.get(`/saas/feature/${feature}`);

// ============== REMINDERS (Pro Feature) ==============

// Get reminder stats
export const getReminderStats = () => api.get('/reminders/stats');

// Get pending reminders
export const getPendingReminders = () => api.get('/reminders/pending');

// Send reminder for invoice
export const sendReminder = (invoiceId) => api.post(`/reminders/send/${invoiceId}`);

// Get reminder history for invoice
export const getReminderHistory = (invoiceId) => api.get(`/reminders/history/${invoiceId}`);

// ============== CSV EXPORT (Pro Feature) ==============

// Export invoices to CSV
export const exportInvoicesCSV = (params) => 
    api.get('/export/invoices/csv', { params, responseType: 'blob' });

// Export quotes to CSV
export const exportQuotesCSV = (params) => 
    api.get('/export/quotes/csv', { params, responseType: 'blob' });

// Export clients to CSV
export const exportClientsCSV = () => 
    api.get('/export/clients/csv', { responseType: 'blob' });

// Export accounting summary
export const exportAccountingCSV = (year, month) => 
    api.get('/export/accounting/csv', { params: { year, month }, responseType: 'blob' });

export default api;
