import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { SavedReport } from '@/lib/reports-store';
import type { Locale } from '@/lib/i18n/dictionary';

const PDF_STRINGS: Record<
  Locale,
  {
    title: string;
    createdAt: string;
    cancerType: string;
    region: string;
    inputConditions: string;
    ctdnaClass: string;
    patientAge: string;
    ageUnit: string;
    biomarker: string;
    confidence: string;
    sensitivity: string;
    tableHeaders: string[];
  }
> = {
  ko: {
    title: 'BioSense-GovAI 추천 리포트',
    createdAt: '생성일',
    cancerType: '암종',
    region: '지역',
    inputConditions: '입력 조건',
    ctdnaClass: 'ctDNA 분류',
    patientAge: '환자 연령',
    ageUnit: '세',
    biomarker: '바이오마커',
    confidence: '신뢰도',
    sensitivity: '민감도',
    tableHeaders: ['순위', '센서', '인식 전략', '신뢰도', 'LOD']
  },
  en: {
    title: 'BioSense-GovAI Recommendation Report',
    createdAt: 'Created',
    cancerType: 'Cancer Type',
    region: 'Region',
    inputConditions: 'Input Conditions',
    ctdnaClass: 'ctDNA Class',
    patientAge: 'Patient Age',
    ageUnit: 'yo',
    biomarker: 'Biomarker',
    confidence: 'Confidence',
    sensitivity: 'Sensitivity',
    tableHeaders: ['Rank', 'Sensor', 'Recognition Strategy', 'Confidence', 'LOD']
  }
};

export function exportReportToPdf(report: SavedReport, locale: Locale = 'ko') {
  const s = PDF_STRINGS[locale];
  const dateLocale = locale === 'ko' ? 'ko-KR' : 'en-US';
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const margin = 14;
  let y = margin;

  doc.setFontSize(18);
  doc.text(s.title, margin, y);
  y += 10;

  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`${s.createdAt}: ${new Date(report.createdAt).toLocaleString(dateLocale)}`, margin, y);
  y += 6;
  doc.text(`${s.cancerType}: ${report.input.cancer_type} · ${s.region}: ${report.input.region_code}`, margin, y);
  y += 10;

  doc.setTextColor(0);
  doc.setFontSize(12);
  doc.text(s.inputConditions, margin, y);
  y += 6;
  doc.setFontSize(10);
  const inputLines = [
    `${s.ctdnaClass}: ${report.input.ctdna_class}`,
    `${s.patientAge}: ${report.input.patient_age}${s.ageUnit}`,
    report.input.biomarker_name ? `${s.biomarker}: ${report.input.biomarker_name}` : null
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
    doc.text(
      `${s.confidence}: ${(rec.confidence_score * 100).toFixed(1)}% · ${s.sensitivity}: ${(rec.expected_metrics.sensitivity * 100).toFixed(1)}%`,
      margin,
      y
    );
    y += 5;
    const rationale = doc.splitTextToSize(rec.rationale, 180);
    doc.text(rationale, margin, y);
    y += rationale.length * 4 + 6;
  });

  autoTable(doc, {
    startY: y,
    head: [s.tableHeaders],
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
