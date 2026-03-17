/**
 * Formatters - Fonctions utilitaires de formatage sécurisées
 * Toutes les fonctions gèrent les valeurs null/undefined
 */

/**
 * Formate un nombre en devise EUR
 * @param {number|null|undefined} value - Valeur à formater
 * @param {object} options - Options de formatage
 * @returns {string} Valeur formatée ou "0,00 €" par défaut
 */
export const formatCurrency = (value, options = {}) => {
    const { 
        decimals = 2, 
        suffix = ' €',
        fallback = '0,00 €'
    } = options;
    
    if (value === null || value === undefined || isNaN(value)) {
        return fallback;
    }
    
    try {
        return Number(value).toLocaleString('fr-FR', { 
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals 
        }) + suffix;
    } catch {
        return fallback;
    }
};

/**
 * Formate un nombre avec décimales fixes
 * @param {number|null|undefined} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Valeur formatée ou "0.00" par défaut
 */
export const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined || isNaN(value)) {
        return (0).toFixed(decimals);
    }
    
    try {
        return Number(value).toFixed(decimals);
    } catch {
        return (0).toFixed(decimals);
    }
};

/**
 * Formate une date en français
 * @param {string|Date|null|undefined} dateStr - Date à formater
 * @param {object} options - Options de formatage
 * @returns {string} Date formatée ou "-" par défaut
 */
export const formatDate = (dateStr, options = {}) => {
    const {
        includeTime = false,
        fallback = '-'
    } = options;
    
    if (!dateStr) {
        return fallback;
    }
    
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) {
            return fallback;
        }
        
        const formatOptions = {
            day: '2-digit',
            month: '2-digit', 
            year: 'numeric',
            ...(includeTime && { hour: '2-digit', minute: '2-digit' })
        };
        
        return date.toLocaleDateString('fr-FR', formatOptions);
    } catch {
        return fallback;
    }
};

/**
 * Formate un pourcentage
 * @param {number|null|undefined} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string} Pourcentage formaté ou "0%" par défaut
 */
export const formatPercent = (value, decimals = 1) => {
    if (value === null || value === undefined || isNaN(value)) {
        return '0%';
    }
    
    try {
        return Number(value).toFixed(decimals) + '%';
    } catch {
        return '0%';
    }
};

/**
 * Obtient une valeur avec fallback
 * @param {any} value - Valeur à vérifier
 * @param {any} fallback - Valeur par défaut
 * @returns {any} Valeur ou fallback
 */
export const safeValue = (value, fallback = 0) => {
    if (value === null || value === undefined) {
        return fallback;
    }
    return value;
};

export default {
    formatCurrency,
    formatNumber,
    formatDate,
    formatPercent,
    safeValue
};
