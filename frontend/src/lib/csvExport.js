/**
 * CSV Export utility for BTP Facture
 * Client-side CSV generation and download
 */

const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleDateString('fr-FR');
};

const formatAmount = (val) => {
    const num = parseFloat(val) || 0;
    return num.toFixed(2).replace('.', ',');
};

const escapeCsvField = (field) => {
    const str = String(field ?? '');
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes(';')) {
        return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
};

const toCsv = (headers, rows) => {
    const BOM = '\uFEFF'; // UTF-8 BOM for Excel compatibility
    const sep = ';'; // Semicolon separator for French Excel
    const headerLine = headers.map(escapeCsvField).join(sep);
    const dataLines = rows.map(row => row.map(escapeCsvField).join(sep));
    return BOM + [headerLine, ...dataLines].join('\n');
};

const downloadCsv = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
};

/**
 * Export clients to CSV
 */
export function exportClientsCSV(clients) {
    const headers = ['Nom', 'Email', 'Téléphone', 'Adresse', 'Ville', 'Code Postal', 'SIRET', 'Date création'];
    const rows = (clients || []).map(c => [
        c.name,
        c.email,
        c.phone,
        c.address,
        c.city,
        c.postal_code,
        c.siret,
        formatDate(c.created_at),
    ]);
    downloadCsv(toCsv(headers, rows), `clients_${new Date().toISOString().slice(0, 10)}.csv`);
}

/**
 * Export quotes to CSV
 */
export function exportQuotesCSV(quotes) {
    const headers = ['N° Devis', 'Client', 'Date', 'Validité', 'Total HT', 'TVA', 'Total TTC', 'Statut'];
    const rows = (quotes || []).map(q => [
        q.quote_number,
        q.client_name,
        formatDate(q.quote_date || q.issue_date),
        formatDate(q.validity_date),
        formatAmount(q.total_ht),
        formatAmount(q.total_vat || q.total_tva),
        formatAmount(q.total_ttc),
        q.status,
    ]);
    downloadCsv(toCsv(headers, rows), `devis_${new Date().toISOString().slice(0, 10)}.csv`);
}

/**
 * Export invoices to CSV
 */
export function exportInvoicesCSV(invoices) {
    const headers = ['N° Facture', 'Client', 'Date', 'Échéance', 'Total HT', 'TVA', 'Total TTC', 'Statut paiement', 'Montant payé'];
    const rows = (invoices || []).map(inv => [
        inv.invoice_number,
        inv.client_name,
        formatDate(inv.invoice_date || inv.issue_date),
        formatDate(inv.due_date),
        formatAmount(inv.total_ht),
        formatAmount(inv.total_vat || inv.total_tva),
        formatAmount(inv.total_ttc),
        inv.payment_status === 'paye' || inv.payment_status === 'paid' ? 'Payé' : 'Impayé',
        formatAmount(inv.paid_amount),
    ]);
    downloadCsv(toCsv(headers, rows), `factures_${new Date().toISOString().slice(0, 10)}.csv`);
}
