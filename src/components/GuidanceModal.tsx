import React, { useState } from 'react';
import { ComplianceGap } from '../types/assessment';
import { X, CheckCircle2, AlertTriangle, FileUp, Lightbulb, PackageCheck, Sparkles } from 'lucide-react';

interface GuidanceModalProps {
  gap: ComplianceGap | null;
  onClose: () => void;
  onApplyFix?: (gapId: string) => void;
}

export const GuidanceModal: React.FC<GuidanceModalProps> = ({ gap, onClose, onApplyFix }) => {
  const [thermalUploaded, setThermalUploaded] = useState(false);
  const [packagingChecked, setPackagingChecked] = useState({
    ratedLumens: true,
    cct: true,
    cri: true,
    standardMarkSpace: true,
  });

  if (!gap) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs">
              {gap.id.replace('GAP-', '')}
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">{gap.title}</h3>
              <p className="text-xs text-slate-500">BIS Standard Action Guidance</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content based on Action Type */}
        <div className="p-6 space-y-4 text-sm text-slate-700">
          <div className="p-3.5 bg-brand-50 border border-brand-200 rounded-xl flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-brand-700 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-brand-900 space-y-1">
              <p className="font-semibold">{gap.parameter}: {gap.referenceRequirement}</p>
              <p>Current measured value: {gap.currentValue}.</p>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">
              Recommended Remediation Guidance
            </h4>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-2 leading-relaxed">
              <p>{gap.recommendation}</p>
              {gap.detailedGuidance && gap.detailedGuidance !== gap.recommendation && (
                <p className="text-slate-600 pt-1 border-t border-slate-200">{gap.detailedGuidance}</p>
              )}
            </div>
          </div>

          {gap.actionType === 'upload_test_data' && (
            <div className="space-y-4">
              <p className="text-xs text-slate-600">
                To satisfy thermal compliance verification, attach preliminary thermocouple test data or temperature rise curve logs for rated ambient conditions (25°C & 45°C).
              </p>

              <div
                onClick={() => setThermalUploaded(true)}
                className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
                  thermalUploaded
                    ? 'border-emerald-400 bg-emerald-50/50'
                    : 'border-slate-300 hover:border-brand-400 bg-slate-50'
                }`}
              >
                {thermalUploaded ? (
                  <div className="flex flex-col items-center gap-1.5 text-emerald-700">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                    <span className="font-semibold text-xs">Thermal_Test_Report_Tj78C.pdf</span>
                    <span className="text-[11px] text-emerald-600">Verified • Junction temp 78°C (&lt;85°C limit)</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1.5 text-slate-500">
                    <FileUp className="w-7 h-7 text-brand-600" />
                    <span className="font-semibold text-xs text-slate-800">Click to attach Thermal Measurement Report</span>
                    <span className="text-[11px] text-slate-400">PDF or CSV thermocouple logs</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {gap.actionType === 'review_packaging' && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs text-slate-600">
                <PackageCheck className="w-4 h-4 text-brand-600 flex-shrink-0" />
                <span>Verify that your retail artwork includes all mandatory Clause 6 technical legends:</span>
              </div>

              <div className="space-y-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={packagingChecked.ratedLumens}
                    onChange={(e) => setPackagingChecked({ ...packagingChecked, ratedLumens: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Rated Luminous Flux (e.g. 720 lm) & Rated Wattage (9W)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={packagingChecked.cct}
                    onChange={(e) => setPackagingChecked({ ...packagingChecked, cct: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Correlated Colour Temperature (e.g. 6500K Cool Daylight)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={packagingChecked.cri}
                    onChange={(e) => setPackagingChecked({ ...packagingChecked, cri: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Colour Rendering Index (CRI Ra ≥ 80)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={packagingChecked.standardMarkSpace}
                    onChange={(e) => setPackagingChecked({ ...packagingChecked, standardMarkSpace: e.target.checked })}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Standard ISI mark & license number clearance area</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200/50 rounded-lg transition-colors"
          >
            Close
          </button>
          {onApplyFix && (
            <button
              onClick={() => {
                onApplyFix(gap.id);
                onClose();
              }}
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Mark as Ready for Re-check</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
