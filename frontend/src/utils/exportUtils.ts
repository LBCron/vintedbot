import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';

interface AnalyticsData {
  revenue: number;
  sales: number;
  views: number;
  conversion: number;
  categories: Array<{ name: string; value: number; revenue: number }>;
}

export async function exportAnalyticsToPDF(data: AnalyticsData) {
  const pdf = new jsPDF('p', 'mm', 'a4');

  // Header
  pdf.setFontSize(24);
  pdf.setTextColor(79, 70, 229); // brand-600
  pdf.text('VintedBot Analytics Report', 20, 20);

  pdf.setFontSize(12);
  pdf.setTextColor(100);
  pdf.text(`Généré le ${new Date().toLocaleDateString('fr-FR')}`, 20, 30);

  // Stats
  pdf.setFontSize(16);
  pdf.setTextColor(0);
  pdf.text('Statistiques Clés', 20, 45);

  const stats = [
    ['Revenus', `${data.revenue}€`],
    ['Articles vendus', data.sales.toString()],
    ['Vues totales', data.views.toLocaleString()],
    ['Taux de conversion', `${data.conversion}%`]
  ];

  autoTable(pdf, {
    startY: 50,
    head: [['Métrique', 'Valeur']],
    body: stats,
    theme: 'grid',
    headStyles: { fillColor: [79, 70, 229] }
  });

  // Categories
  const finalY = (pdf as any).lastAutoTable.finalY || 100;
  pdf.setFontSize(16);
  pdf.text('Ventes par Catégorie', 20, finalY + 15);

  const categories = data.categories.map(cat => [
    cat.name,
    `${cat.value}%`,
    `${cat.revenue}€`
  ]);

  autoTable(pdf, {
    startY: finalY + 20,
    head: [['Catégorie', 'Part (%)', 'Revenus']],
    body: categories,
    theme: 'striped',
    headStyles: { fillColor: [79, 70, 229] }
  });

  // Footer
  pdf.setFontSize(10);
  pdf.setTextColor(150);
  pdf.text('VintedBot - Automatisez vos ventes Vinted', 20, 280);

  // Save
  pdf.save(`vintedbot-analytics-${new Date().toISOString().split('T')[0]}.pdf`);
}

interface Draft {
  id: string;
  title: string;
  price: number;
  category: string;
  status: string;
  created_at: string;
  quality_score?: number;
}

export function exportDraftsToCSV(drafts: Draft[]) {
  const headers = ['ID', 'Titre', 'Prix', 'Catégorie', 'Statut', 'Date création', 'Score qualité'];

  const rows = drafts.map(draft => [
    draft.id,
    `"${draft.title.replace(/"/g, '""')}"`, // Escape quotes
    draft.price,
    draft.category,
    draft.status,
    new Date(draft.created_at).toLocaleDateString('fr-FR'),
    draft.quality_score || '-'
  ]);

  const csv = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');

  // Download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `vintedbot-drafts-${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
}

export async function exportChartToImage(chartElementId: string) {
  const element = document.getElementById(chartElementId);
  if (!element) return;

  const canvas = await html2canvas(element);
  const link = document.createElement('a');
  link.download = `chart-${Date.now()}.png`;
  link.href = canvas.toDataURL();
  link.click();
}
