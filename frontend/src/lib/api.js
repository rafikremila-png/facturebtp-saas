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
export const getQuotes = (status) => api.get('/quotes', { params: { status } });
export const getQuote = (id) => api.get(`/quotes/${id}`);
export const createQuote = (data) => api.post('/quotes', data);
export const updateQuote = (id, data) => api.put(`/quotes/${id}`, data);
export const deleteQuote = (id) => api.delete(`/quotes/${id}`);
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
export const getInvoices = (paymentStatus) => api.get('/invoices', { params: { payment_status: paymentStatus } });
export const getInvoice = (id) => api.get(`/invoices/${id}`);
export const createInvoice = (data) => api.post('/invoices', data);
export const updateInvoice = (id, data) => api.put(`/invoices/${id}`, data);
export const deleteInvoice = (id) => api.delete(`/invoices/${id}`);
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

// Predefined Items
export const getPredefinedCategories = () => api.get('/predefined-items/categories');
export const getPredefinedItems = (category) => api.get('/predefined-items', { params: { category } });
export const createPredefinedItem = (data) => api.post('/predefined-items', data);
export const updatePredefinedItem = (id, data) => api.put(`/predefined-items/${id}`, data);
export const deletePredefinedItem = (id) => api.delete(`/predefined-items/${id}`);
export const resetPredefinedItems = () => api.post('/predefined-items/reset');

// Renovation Kits
export const getKits = () => api.get('/kits');
export const getKit = (id) => api.get(`/kits/${id}`);
export const createKit = (data) => api.post('/kits', data);
export const updateKit = (id, data) => api.put(`/kits/${id}`, data);
export const deleteKit = (id) => api.delete(`/kits/${id}`);
export const createKitFromQuote = (quoteId, name, description = "") => 
    api.post(`/kits/from-quote/${quoteId}`, null, { params: { kit_name: name, kit_description: description } });
export const resetKits = () => api.post('/kits/reset');

export default api;
