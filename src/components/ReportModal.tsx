import React from 'react';
import { AssessmentResult } from '../types/assessment';
import { X, Download, Printer, CheckCircle2, AlertTriangle, ShieldCheck, FileText } from 'lucide-react';
import jsPDF from 'jspdf';

interface ReportModalProps {
  assessment: AssessmentResult;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ assessment, onClose }) => {
  const downloadPdf = () => {
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    // Header styling
    doc.setFillColor(14, 140, 233); // Brand color
    doc.rect(0, 0, 210, 24, 'F');

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text('BIS AI ASSISTANT — PRE-CERTIFICATION REPORT', 14, 15);

    // Metadata
    doc.setTextColor(50, 50, 50);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Report ID: ${assessment.id}`, 14, 34);
    doc.text(`Generated: ${new Date(assessment.assessedAt).toLocaleDateString()} ${new Date(assessment.assessedAt).toLocaleTimeString()}`, 14, 40);
    doc.text(`Target Standard: ${assessment.referenceStandard}`, 14, 46);

    // Product Specs Box
    doc.setDrawColor(220, 220, 220);
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(14, 52, 182, 32, 2, 2, 'FD');

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(15, 23, 42);
    doc.text('PRODUCT SPECIFICATIONS', 18, 60);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(70, 70, 70);
    doc.text(`Product: ${assessment.productName} (${assessment.category})`, 18, 68);
    doc.text(`Location: ${assessment.manufacturingLocation}`, 18, 74);
    doc.text(`Specs: ${assessment.specifications.wattage}W | ${assessment.specifications.voltage}V | ${assessment.specifications.luminousEfficacy} lm/W`, 110, 68);
    doc.text(`Readiness Score: ${assessment.readinessScore}% (${assessment.isPostRecheck ? 'Post-Optimization' : 'Initial Assessment'})`, 110, 74);

    // Gaps Section
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(15, 23, 42);
    doc.text('COMPLIANCE PARAMETERS & GAPS EVALUATION', 14, 94);

    let yPos = 102;
    assessment.gaps.forEach((gap, index) => {
      doc.setDrawColor(230, 230, 230);
      doc.setFillColor(gap.isResolved ? 240 : 255, gap.isResolved ? 253 : 245, gap.isResolved ? 244 : 245);
      doc.roundedRect(14, yPos, 182, 22, 2, 2, 'FD');

      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(20, 20, 20);
      doc.text(`${gap.title} — Status: ${gap.status}`, 18, yPos + 7);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(80, 80, 80);
      doc.text(`Current: ${gap.currentValue} | Requirement: ${gap.referenceRequirement}`, 18, yPos + 13);
      doc.text(`Rec: ${gap.recommendation.substring(0, 95)}...`, 18, yPos + 18);

      yPos += 26;
    });

    // Estimates Box
    yPos += 4;
    doc.setDrawColor(220, 220, 220);
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(14, yPos, 182, 30, 2, 2, 'FD');

    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(15, 23, 42);
    doc.text('ESTIMATED FINANCIAL & TIMELINE PROJECTIONS', 18, yPos + 8);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(70, 70, 70);
    doc.text(`Testing Fees: ₹${assessment.costEstimate.testingFees.toLocaleString('en-IN')}`, 18, yPos + 16);
    doc.text(`Statutory BIS & Doc: ₹${(assessment.costEstimate.bisRelatedFees + assessment.costEstimate.documentationFees).toLocaleString('en-IN')}`, 18, yPos + 22);
    doc.text(`Total Estimate: ₹${assessment.costEstimate.totalFees.toLocaleString('en-IN')}`, 18, yPos + 27);

    doc.text(`Estimated Timeline: ${assessment.timelineEstimate.range}`, 110, yPos + 16);
    doc.text(`Phases: Testing (25-35d), Audit (12-15d)`, 110, yPos + 22);

    // Footer Disclaimer
    doc.setFontSize(7.5);
    doc.setTextColor(120, 120, 120);
    doc.text('NOTICE: This is an AI Assessment Report for pre-certification preparation, NOT an official BIS application or guarantee.', 14, 280);

    doc.save(`BIS_AI_Assessment_Report_${assessment.productId}.pdf`);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center shadow-xs">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">AI Assessment Report</h3>
              <p className="text-xs text-slate-500">Document ID: {assessment.id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Report Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-700">
          {/* Top Banner */}
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <p className="text-xs text-slate-500 font-medium">Evaluated Product</p>
              <h4 className="text-base font-bold text-slate-900">{assessment.productName}</h4>
              <p className="text-xs text-slate-600">Location: {assessment.manufacturingLocation}</p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-extrabold text-brand-700">{assessment.readinessScore}%</span>
              <p className="text-[11px] text-slate-500 font-semibold uppercase">Readiness Score</p>
            </div>
          </div>

          {/* Reference Standard */}
          <div className="border border-slate-200 rounded-xl p-4 bg-white">
            <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
              Reference Standard & Clause Mapping
            </h5>
            <div className="flex items-center justify-between text-xs text-slate-600 bg-brand-50/50 p-2.5 rounded-lg border border-brand-100">
              <div>
                <span className="font-bold text-brand-900">{assessment.referenceStandard}</span>
                <p className="text-slate-500 text-[11px]">{assessment.standardTitle}</p>
              </div>
              <span className="text-[11px] font-semibold bg-white text-brand-700 px-2 py-0.5 rounded border border-brand-200">
                Self-Ballasted LED
              </span>
            </div>
          </div>

          {/* Identified Parameters / Gaps */}
          <div>
            <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
              Assessment Summary ({assessment.gaps.length} Parameters)
            </h5>
            <div className="space-y-2">
              {assessment.gaps.map((gap) => (
                <div
                  key={gap.id}
                  className={`p-3 rounded-lg border text-xs flex items-start justify-between gap-3 ${
                    gap.isResolved
                      ? 'bg-emerald-50/60 border-emerald-200'
                      : 'bg-amber-50/60 border-amber-200'
                  }`}
                >
                  <div className="space-y-1">
                    <p className="font-semibold text-slate-900">
                      {gap.title} — <span className="font-normal text-slate-600">{gap.parameter}</span>
                    </p>
                    <p className="text-slate-600">
                      Current: <strong>{gap.currentValue}</strong> | Req: <strong>{gap.referenceRequirement}</strong>
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase flex-shrink-0 ${
                      gap.isResolved
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {gap.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Cost & Timeline Projections */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <h6 className="text-[11px] font-bold text-slate-500 uppercase">Estimated Testing & Certification Cost</h6>
              <p className="text-lg font-bold text-slate-900 mt-1">₹{assessment.costEstimate.totalFees.toLocaleString('en-IN')}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Testing ₹45k + BIS ₹10k + Doc ₹5k</p>
            </div>
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <h6 className="text-[11px] font-bold text-slate-500 uppercase">Estimated Certification Timeline</h6>
              <p className="text-lg font-bold text-slate-900 mt-1">{assessment.timelineEstimate.range}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Standard laboratory turnaround window</p>
            </div>
          </div>

          {/* Disclaimer Note */}
          <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-3">
            This AI Assessment Report is generated solely for informational pre-certification preparedness and does not constitute an official Bureau of Indian Standards decision, endorsement, or certified test report.
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 rounded-lg transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print View</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/50 rounded-lg transition-colors"
            >
              Close
            </button>
            <button
              onClick={downloadPdf}
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PDF Report</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
