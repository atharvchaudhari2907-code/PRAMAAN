import React, { useState } from 'react';
import { ExtractedParameter, StandardCandidate } from '../types/assessment';
import { X, Sparkles, CheckCircle2, AlertCircle, FileText, ArrowRight, BookOpen, ShieldCheck, Edit3 } from 'lucide-react';

interface ExtractedReviewModalProps {
  applicationId: string;
  parameters: ExtractedParameter[];
  candidates: StandardCandidate[];
  missingInfo: string[];
  warnings: string[];
  onConfirm: (reviewedParameters: ExtractedParameter[], selectedStandardId: string) => void;
  onClose: () => void;
}

export const ExtractedReviewModal: React.FC<ExtractedReviewModalProps> = ({
  applicationId,
  parameters: initialParams,
  candidates,
  missingInfo,
  warnings,
  onConfirm,
  onClose,
}) => {
  const [params, setParams] = useState<ExtractedParameter[]>(initialParams);
  const [selectedStandard, setSelectedStandard] = useState<string>(
    candidates.find((c) => c.is_primary)?.standard_id || candidates[0]?.standard_id || ''
  );
  const [activeTab, setActiveTab] = useState<'params' | 'standards'>('params');

  const handleParamChange = (index: number, field: keyof ExtractedParameter, value: any) => {
    setParams((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value, is_user_modified: true };
      return updated;
    });
  };

  const handleProceed = () => {
    onConfirm(params, selectedStandard);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-3xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 border border-brand-200 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-base">Review AI-Extracted Product Specs</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Step 2 of 3
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Verify and correct extracted technical parameters before compliance analysis.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 border-b border-slate-100 flex items-center gap-4 bg-slate-50/50">
          <button
            onClick={() => setActiveTab('params')}
            className={`pb-2.5 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'params'
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Extracted Parameters ({params.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('standards')}
            className={`pb-2.5 text-xs font-bold border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'standards'
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Applicable Standards ({candidates.length})</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-700">
          {/* Missing info & warnings banner */}
          {(missingInfo.length > 0 || warnings.length > 0) && (
            <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 space-y-1 text-amber-900">
              <div className="flex items-center gap-1.5 font-bold text-xs">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>Notice on Submitted Information:</span>
              </div>
              <ul className="list-disc pl-5 text-[11px] space-y-0.5 text-amber-800">
                {missingInfo.map((m, i) => (
                  <li key={`m-${i}`}>Missing in document: <strong>{m}</strong> (will be flagged as gap/insufficient).</li>
                ))}
                {warnings.map((w, i) => (
                  <li key={`w-${i}`}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {activeTab === 'params' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Extracted Specifications & Source Traceability
                </span>
                <span className="text-slate-400 text-[11px]">
                  Editable fields • Values reflect product datasheet
                </span>
              </div>

              <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
                {params.map((p, idx) => (
                  <div key={p.parameter_key || idx} className="p-3.5 bg-white hover:bg-slate-50/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1 max-w-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{p.name}</span>
                        {p.confidence === 'HIGH' && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            High Confidence
                          </span>
                        )}
                        {p.is_user_modified && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                            User Edited
                          </span>
                        )}
                      </div>
                      {p.source_snippet && (
                        <p className="text-[11px] text-slate-500 italic truncate">
                          "{p.source_snippet}" {p.source_page ? `• Page ${p.source_page}` : ''}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <div className="relative">
                        <input
                          type="text"
                          value={p.value}
                          onChange={(e) => handleParamChange(idx, 'value', e.target.value)}
                          className="px-3 py-1.5 text-xs font-semibold text-slate-900 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 w-32"
                        />
                      </div>
                      {p.unit && (
                        <span className="text-xs font-semibold text-slate-500 w-12">
                          {p.unit}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px] block">
                Select Applicable Target Standard
              </span>

              <div className="space-y-2.5">
                {candidates.map((c) => (
                  <div
                    key={c.standard_id}
                    onClick={() => setSelectedStandard(c.standard_id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedStandard === c.standard_id
                        ? 'border-brand-500 bg-brand-50/40 shadow-xs ring-1 ring-brand-500'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-sm text-slate-900">{c.standard_id}</span>
                          <span className="text-slate-400 font-normal">({c.version})</span>
                          {c.is_primary && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-100 text-brand-800">
                              Recommended Candidate
                            </span>
                          )}
                        </div>
                        <p className="font-medium text-slate-700 text-xs mt-0.5">{c.title}</p>
                        <p className="text-[11px] text-slate-500 mt-1">{c.match_reason}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded">
                          {Math.round(c.confidence_score * 100)}% Match
                        </span>
                        <div
                          className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                            selectedStandard === c.standard_id
                              ? 'border-brand-600 bg-brand-600 text-white'
                              : 'border-slate-300'
                          }`}
                        >
                          {selectedStandard === c.standard_id && <CheckCircle2 className="w-3.5 h-3.5" />}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trust Disclaimer */}
          <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500">
            <ShieldCheck className="w-4 h-4 text-brand-600 flex-shrink-0" />
            <span>
              Target standard candidate: <strong>{selectedStandard}</strong>. Compliance analysis will execute deterministic parameter checks against this specification.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 rounded-lg transition-colors"
          >
            Back to Upload
          </button>

          <button
            onClick={handleProceed}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs text-white bg-brand-600 hover:bg-brand-700 shadow-md shadow-brand-600/20 hover:shadow-lg transition-all"
          >
            <span>Proceed to Compliance Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
