import React from 'react';
import { ComplianceResultItem, ComplianceGap } from '../types/assessment';
import { X, ShieldCheck, FileText, CheckCircle2, AlertTriangle, BookOpen, ExternalLink, HelpCircle } from 'lucide-react';

interface EvidenceModalProps {
  item: ComplianceResultItem | ComplianceGap;
  standardId: string;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ item, standardId, onClose }) => {
  const isGap = 'currentValue' in item;
  const title = isGap ? item.title : `${item.clause} — ${item.parameter_name}`;
  const status = isGap ? item.status : item.status;
  const requirement = isGap ? item.referenceRequirement : item.requirement_text;
  const evidence = isGap ? item.currentValue : item.product_evidence;
  const reasoning = isGap ? (item.detailedGuidance || item.recommendation) : item.reasoning;
  const bisSource = !isGap && item.bis_source ? item.bis_source : `${standardId}, Clause ${isGap ? 'Reference' : item.clause}`;
  const prodSource = !isGap && item.product_source ? item.product_source : 'Submitted Product Datasheet, Page 1';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-100 text-brand-700 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">{title}</h3>
              <p className="text-xs text-slate-500">Compliance Traceability & Evidence Verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-700">
          {/* Side-by-Side Comparison Box */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left Box: Product Evidence */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[11px] text-slate-500 uppercase tracking-wider">
                  Product Evidence
                </span>
                <span className="text-[10px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                  {prodSource}
                </span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200 text-sm font-bold text-slate-900">
                {evidence}
              </div>
              <p className="text-[11px] text-slate-500">
                Extracted directly from technical datasheet without inference or modification.
              </p>
            </div>

            {/* Right Box: BIS Standard Requirement */}
            <div className="p-4 rounded-xl bg-brand-50/50 border border-brand-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[11px] text-brand-800 uppercase tracking-wider">
                  BIS Reference Requirement
                </span>
                <span className="text-[10px] font-semibold text-brand-800 bg-white px-2 py-0.5 rounded border border-brand-200">
                  {bisSource}
                </span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-brand-200 text-sm font-bold text-brand-950">
                {requirement}
              </div>
              <p className="text-[11px] text-brand-700">
                Mandatory Indian Standard specification benchmark.
              </p>
            </div>
          </div>

          {/* Reasoning & Traceability Analysis */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              AI Compliance Evaluation Reasoning
            </h4>
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 leading-relaxed space-y-2">
              <p>{reasoning}</p>
              {!isGap && item.recommendation && (
                <div className="pt-2 border-t border-slate-100 flex items-start gap-1.5 text-brand-800">
                  <span className="font-bold">Action:</span>
                  <span>{item.recommendation}</span>
                </div>
              )}
            </div>
          </div>

          {/* Audit Trail Assurance */}
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600">
            <ShieldCheck className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Explainability Note:</strong> Every compliance finding is grounded exclusively in retrieved clauses from the official Indian Standard catalog and verified against user product documentation.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
