/**
 * PDF Generation utility for BTP Facture
 * Generates professional PDF documents for quotes and invoices using jsPDF
 */
import jsPDF from 'jspdf';
import 'jspdf-autotable';

// Colors
const COLORS = {
    primary: [232, 121, 47],    // #E8792F - orange
    dark: [30, 35, 40],         // dark header
    text: [55, 65, 81],         // gray-700
    textLight: [107, 114, 128], // gray-500
    white: [255, 255, 255],
    tableBorder: [229, 231, 235],
    tableStripe: [249, 250, 251],
};

const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '-';
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

const formatCurrency = (amount) => {
    const num = parseFloat(amount) || 0;
    return num.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
};

const parseItems = (items) => {
    if (!items) return [];
    if (typeof items === 'string') {
        try { return JSON.parse(items); } catch { return []; }
    }
    return Array.isArray(items) ? items : [];
};

/**
 * Generate a PDF for a quote or invoice
 * @param {Object} params
 * @param {'quote'|'invoice'} params.type
 * @param {Object} params.document - The quote or invoice data
 * @param {Object} params.settings - Company settings
 * @param {Object} params.client - Client info (optional, for extra details)
 */
export function generateDocumentPdf({ type, document: doc, settings = {}, client = {} }) {
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const margin = 15;
    const contentWidth = pageWidth - margin * 2;
    let y = margin;

    const isQuote = type === 'quote';
    const docLabel = isQuote ? 'DEVIS' : 'FACTURE';
    const docNumber = isQuote ? doc.quote_number : doc.invoice_number;
    const docDate = isQuote ? (doc.quote_date || doc.issue_date) : (doc.invoice_date || doc.issue_date);

    // ===== HEADER BAR =====
    pdf.setFillColor(...COLORS.dark);
    pdf.rect(0, 0, pageWidth, 32, 'F');

    // Company name in header
    pdf.setTextColor(...COLORS.white);
    pdf.setFontSize(18);
    pdf.setFont('helvetica', 'bold');
    pdf.text(settings.company_name || 'BTP Facture', margin, 14);

    // Document type badge
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.text(settings.company_email || '', margin, 24);

    // Document number on the right
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.text(`${docLabel} ${docNumber || ''}`, pageWidth - margin, 14, { align: 'right' });

    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Date: ${formatDate(docDate)}`, pageWidth - margin, 24, { align: 'right' });

    y = 42;

    // ===== COMPANY & CLIENT INFO (two columns) =====
    const colWidth = contentWidth / 2 - 5;

    // Company info box
    pdf.setFillColor(249, 250, 251);
    pdf.roundedRect(margin, y, colWidth, 38, 2, 2, 'F');

    pdf.setTextColor(...COLORS.primary);
    pdf.setFontSize(8);
    pdf.setFont('helvetica', 'bold');
    pdf.text('ÉMETTEUR', margin + 4, y + 6);

    pdf.setTextColor(...COLORS.text);
    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'bold');
    pdf.text(settings.company_name || '', margin + 4, y + 13);

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    let companyY = y + 18;
    if (settings.company_address) {
        pdf.text(settings.company_address, margin + 4, companyY);
        companyY += 4;
    }
    if (settings.company_phone) {
        pdf.text(`Tél: ${settings.company_phone}`, margin + 4, companyY);
        companyY += 4;
    }
    if (settings.company_siret) {
        pdf.text(`SIRET: ${settings.company_siret}`, margin + 4, companyY);
        companyY += 4;
    }
    if (settings.company_tva) {
        pdf.text(`TVA: ${settings.company_tva}`, margin + 4, companyY);
    }

    // Client info box
    const clientX = margin + colWidth + 10;
    pdf.setFillColor(255, 247, 237);
    pdf.roundedRect(clientX, y, colWidth, 38, 2, 2, 'F');

    pdf.setTextColor(...COLORS.primary);
    pdf.setFontSize(8);
    pdf.setFont('helvetica', 'bold');
    pdf.text('DESTINATAIRE', clientX + 4, y + 6);

    pdf.setTextColor(...COLORS.text);
    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'bold');
    pdf.text(doc.client_name || client.name || '', clientX + 4, y + 13);

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    let clientY = y + 18;
    const clientAddress = doc.client_address || client.address || '';
    if (clientAddress) {
        pdf.text(clientAddress, clientX + 4, clientY);
        clientY += 4;
    }
    const clientEmail = doc.client_email || client.email || '';
    if (clientEmail) {
        pdf.text(clientEmail, clientX + 4, clientY);
        clientY += 4;
    }
    const clientPhone = client.phone || '';
    if (clientPhone) {
        pdf.text(`Tél: ${clientPhone}`, clientX + 4, clientY);
    }

    y += 45;

    // ===== DOCUMENT META =====
    pdf.setFillColor(...COLORS.primary);
    pdf.roundedRect(margin, y, contentWidth, 12, 1, 1, 'F');

    pdf.setTextColor(...COLORS.white);
    pdf.setFontSize(8);
    pdf.setFont('helvetica', 'bold');

    if (isQuote) {
        pdf.text(`Date d'émission: ${formatDate(docDate)}`, margin + 4, y + 8);
        pdf.text(`Validité: ${formatDate(doc.validity_date)}`, margin + contentWidth / 3, y + 8);
        pdf.text(`Statut: ${(doc.status || 'brouillon').toUpperCase()}`, margin + contentWidth * 2 / 3, y + 8);
    } else {
        pdf.text(`Date d'émission: ${formatDate(docDate)}`, margin + 4, y + 8);
        pdf.text(`Échéance: ${formatDate(doc.due_date)}`, margin + contentWidth / 3, y + 8);
        const statusLabel = doc.payment_status === 'paye' || doc.payment_status === 'paid' ? 'PAYÉ' : 'IMPAYÉ';
        pdf.text(`Statut: ${statusLabel}`, margin + contentWidth * 2 / 3, y + 8);
    }

    y += 18;

    // ===== ITEMS TABLE =====
    const items = parseItems(doc.items);

    const tableBody = items.map(item => {
        const qty = parseFloat(item.quantity) || 0;
        const price = parseFloat(item.unit_price) || 0;
        const vatRate = parseFloat(item.vat_rate) || 0;
        const totalHT = qty * price;
        return [
            item.description || '',
            item.unit || 'u',
            qty.toLocaleString('fr-FR'),
            formatCurrency(price),
            `${vatRate}%`,
            formatCurrency(totalHT),
        ];
    });

    pdf.autoTable({
        startY: y,
        head: [['Description', 'Unité', 'Qté', 'Prix unit. HT', 'TVA', 'Total HT']],
        body: tableBody,
        margin: { left: margin, right: margin },
        styles: {
            fontSize: 8,
            cellPadding: 3,
            textColor: COLORS.text,
            lineColor: COLORS.tableBorder,
            lineWidth: 0.1,
        },
        headStyles: {
            fillColor: COLORS.dark,
            textColor: COLORS.white,
            fontStyle: 'bold',
            fontSize: 8,
        },
        alternateRowStyles: {
            fillColor: COLORS.tableStripe,
        },
        columnStyles: {
            0: { cellWidth: 'auto' },
            1: { cellWidth: 18, halign: 'center' },
            2: { cellWidth: 16, halign: 'center' },
            3: { cellWidth: 28, halign: 'right' },
            4: { cellWidth: 16, halign: 'center' },
            5: { cellWidth: 28, halign: 'right' },
        },
    });

    y = pdf.lastAutoTable.finalY + 8;

    // ===== TOTALS SECTION =====
    const totalHT = parseFloat(doc.total_ht) || 0;
    const totalVAT = parseFloat(doc.total_vat) || parseFloat(doc.total_tva) || 0;
    const totalTTC = parseFloat(doc.total_ttc) || (totalHT + totalVAT);

    const totalsX = pageWidth - margin - 75;
    const totalsWidth = 75;

    // Total HT
    pdf.setFillColor(249, 250, 251);
    pdf.roundedRect(totalsX, y, totalsWidth, 8, 1, 1, 'F');
    pdf.setTextColor(...COLORS.text);
    pdf.setFontSize(9);
    pdf.setFont('helvetica', 'normal');
    pdf.text('Total HT', totalsX + 3, y + 5.5);
    pdf.text(formatCurrency(totalHT), totalsX + totalsWidth - 3, y + 5.5, { align: 'right' });
    y += 9;

    // TVA
    pdf.setFillColor(249, 250, 251);
    pdf.roundedRect(totalsX, y, totalsWidth, 8, 1, 1, 'F');
    pdf.text('TVA', totalsX + 3, y + 5.5);
    pdf.text(formatCurrency(totalVAT), totalsX + totalsWidth - 3, y + 5.5, { align: 'right' });
    y += 9;

    // Retention de garantie (if applicable)
    if (doc.retention_rate && doc.retention_amount) {
        pdf.setFillColor(255, 247, 237);
        pdf.roundedRect(totalsX, y, totalsWidth, 8, 1, 1, 'F');
        pdf.text(`Retenue (${doc.retention_rate}%)`, totalsX + 3, y + 5.5);
        pdf.text(`-${formatCurrency(doc.retention_amount)}`, totalsX + totalsWidth - 3, y + 5.5, { align: 'right' });
        y += 9;
    }

    // Total TTC
    pdf.setFillColor(...COLORS.primary);
    pdf.roundedRect(totalsX, y, totalsWidth, 10, 1, 1, 'F');
    pdf.setTextColor(...COLORS.white);
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'bold');
    pdf.text('Total TTC', totalsX + 3, y + 7);
    pdf.text(formatCurrency(totalTTC), totalsX + totalsWidth - 3, y + 7, { align: 'right' });
    y += 14;

    // For invoices: paid amount
    if (!isQuote && (doc.paid_amount > 0)) {
        pdf.setTextColor(...COLORS.text);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`Montant payé: ${formatCurrency(doc.paid_amount)}`, totalsX + 3, y + 3);
        const remaining = totalTTC - (parseFloat(doc.paid_amount) || 0);
        pdf.text(`Reste à payer: ${formatCurrency(remaining)}`, totalsX + 3, y + 8);
        y += 12;
    }

    // ===== NOTES =====
    if (doc.notes) {
        y = Math.max(y, pdf.lastAutoTable.finalY + 8);
        pdf.setTextColor(...COLORS.text);
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Notes:', margin, y + 4);
        pdf.setFont('helvetica', 'normal');
        const noteLines = pdf.splitTextToSize(doc.notes, contentWidth / 2);
        pdf.text(noteLines, margin, y + 9);
        y += 9 + noteLines.length * 4;
    }

    // ===== LEGAL MENTIONS =====
    const legalText = settings.legal_mentions || doc.terms || '';
    if (legalText) {
        // Position near bottom
        const bottomY = Math.max(y + 10, 255);
        pdf.setDrawColor(...COLORS.tableBorder);
        pdf.line(margin, bottomY, pageWidth - margin, bottomY);

        pdf.setTextColor(...COLORS.textLight);
        pdf.setFontSize(7);
        pdf.setFont('helvetica', 'italic');
        const legalLines = pdf.splitTextToSize(legalText, contentWidth);
        pdf.text(legalLines, margin, bottomY + 5);
    }

    // ===== FOOTER =====
    const footerY = 285;
    pdf.setTextColor(...COLORS.textLight);
    pdf.setFontSize(7);
    pdf.text(
        `${settings.company_name || 'BTP Facture'} - ${docLabel} ${docNumber} - Généré le ${formatDate(new Date().toISOString())}`,
        pageWidth / 2,
        footerY,
        { align: 'center' }
    );

    return pdf;
}

/**
 * Download a quote as PDF
 */
export function downloadQuotePdf(quote, settings = {}, client = {}) {
    const pdf = generateDocumentPdf({ type: 'quote', document: quote, settings, client });
    pdf.save(`${quote.quote_number || 'devis'}.pdf`);
}

/**
 * Download an invoice as PDF
 */
export function downloadInvoicePdf(invoice, settings = {}, client = {}) {
    const pdf = generateDocumentPdf({ type: 'invoice', document: invoice, settings, client });
    pdf.save(`${invoice.invoice_number || 'facture'}.pdf`);
}
