import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { SavedReport } from '@/lib/reports-store';

export function exportReportToPdf(report: SavedReport) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const margin = 14;
  let y = margin;

  doc.setFontSize(18);
  doc.text('BioSense-GovAI 추천 리포트', margin, y);
  y += 10;

  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`생성일: ${new Date(report.createdAt).toLocaleString('ko-KR')}`, margin, y);
  y += 6;
  doc.text(`암종: ${report.input.cancer_type} · 지역: ${report.input.region_code}`, margin, y);
  y += 10;

  doc.setTextColor(0);
  doc.setFontSize(12);
  doc.text('입력 조건', margin, y);
  y += 6;
  doc.setFontSize(10);
  const inputLines = [
    `ctDNA 분류: ${report.input.ctdna_class}`,
    `환자 연령: ${report.input.patient_age}세`,
    report.input.biomarker_name ? `바이오마커: ${report.input.biomarker_name}` : null
  ].filter(Boolean) as string[];
  inputLines.forEach((line) => {
    doc.text(line, margin, y);
    y += 5;
  });
  y += 4;

  report.recommendations.forEach((rec, idx) => {
    if (y > 250) {
      doc.addPage();
      y = margin;
    }
    doc.setFontSize(12);
    doc.text(`${idx + 1}. ${rec.sensor_name}`, margin, y);
    y += 6;
    doc.setFontSize(9);
    doc.text(`신뢰도: ${(rec.confidence_score * 100).toFixed(1)}% · 민감도: ${(rec.expected_metrics.sensitivity * 100).toFixed(1)}%`, margin, y);
    y += 5;
    const rationale = doc.splitTextToSize(rec.rationale, 180);
    doc.text(rationale, margin, y);
    y += rationale.length * 4 + 6;
  });

  autoTable(doc, {
    startY: y,
    head: [['순위', '센서', '인식 전략', '신뢰도', 'LOD']],
    body: report.recommendations.map((r) => [
      String(r.rank),
      r.sensor_name,
      r.recognition_name,
      `${(r.confidence_score * 100).toFixed(1)}%`,
      `${r.expected_metrics.lod_value} ${r.expected_metrics.lod_unit}`
    ]),
    styles: { fontSize: 8 },
    headStyles: { fillColor: [8, 145, 178] }
  });

  doc.save(`biosense-report-${report.id.slice(0, 8)}.pdf`);
}

export function exportTableToPdf(
  title: string,
  headers: string[],
  rows: string[][]
) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
  doc.setFontSize(14);
  doc.text(title, 14, 16);
  autoTable(doc, {
    startY: 22,
    head: [headers],
    body: rows,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [8, 145, 178] }
  });
  doc.save(`${title.replace(/\s+/g, '-').toLowerCase()}.pdf`);
}
