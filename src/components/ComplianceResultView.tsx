import React, { useState } from 'react';
import { AssessmentResult, ComplianceGap, ComplianceResultItem } from '../types/assessment';
import { ReadinessGauge } from './ReadinessGauge';
import { GapCard } from './GapCard';
import { GuidanceModal } from './GuidanceModal';
import { ReportModal } from './ReportModal';
import { EvidenceModal } from './EvidenceModal';
import { ApplicationPrepView } from './ApplicationPrepView';
import { ApplicationTrackingView } from './ApplicationTrackingView';
import { BlockchainVerifyModal } from './BlockchainVerifyModal';
import { ContextualChatDrawer } from './ContextualChatDrawer';
import {
  AlertTriangle,
  CheckCircle2,
  FileSpreadsheet,
  IndianRupee,
  Clock,
  RotateCw,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Download,
  ShieldCheck,
  ChevronDown,
  Info,
  MessageSquareText,
  FileText,
  Activity,
  Layers,
  FileSearch,
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface ComplianceResultViewProps {
  assessment: AssessmentResult;
  onRecheck: () => void;
  onEditSpecs: () => void;
  onRegisterTrustLedger?: () => Promise<any>;
}

export const ComplianceResultView: React.FC<ComplianceResultViewProps> = ({
  assessment,
  onRecheck,
  onEditSpecs,
  onRegisterTrustLedger,
}) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'dossier' | 'tracking'>('dashboard');
  const [selectedGap, setSelectedGap] = useState<ComplianceGap | null>(null);
  const [evidenceItem, setEvidenceItem] = useState<ComplianceGap | ComplianceResultItem | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [showChatDrawer, setShowChatDrawer] = useState(false);

  const isPostRecheck = assessment.isPostRecheck || assessment.readinessScore >= 90;

  React.useEffect(() => {
    if (isPostRecheck) {
      triggerConfetti();
    }
  }, [isPostRecheck]);

  const triggerConfetti = () => {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#10b981', '#0ea5e9', '#6366f1'],
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              AI Compliance Assessment
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200">
              {assessment.referenceStandard}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Evaluated product: <strong>{assessment.productName}</strong> ({assessment.category}) • Location: {assessment.manufacturingLocation}
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => setShowChatDrawer(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-xl transition-colors shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            <span>Ask BIS AI</span>
          </button>

          <button
            onClick={() => setShowReportModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-xl shadow-xs transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Report</span>
          </button>

          <button
            onClick={onRegisterTrustLedger || (() => Promise.resolve())}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-xl transition-colors"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
            <span>Register Trust Ledger</span>
          </button>

          <button
            onClick={onEditSpecs}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
          >
            <span>Edit Specs</span>
          </button>
        </div>
      </div>

      {/* Main Workflow Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 overflow-x-auto">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'dashboard'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Compliance Dashboard</span>
        </button>

        <button
          onClick={() => setActiveTab('dossier')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'dossier'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Application Dossier Preview</span>
        </button>

        <button
          onClick={() => setActiveTab('tracking')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'tracking'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Tracking Pipeline</span>
        </button>
      </div>

      {/* Tab 1: Dashboard View */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Hero Status Callout Banner */}
          {assessment.assessment_state === 'EXTRACTION_CONFLICT' ? (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-300/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in duration-300">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-rose-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-rose-950">
                    Extraction Conflict Detected
                  </h3>
                  <p className="text-xs text-rose-800 mt-0.5">
                    Extracted parameter specifications contradict source document text. Compliance analysis is blocked until corrected.
                  </p>
                </div>
              </div>
              <button
                onClick={onEditSpecs}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-sm transition-all self-start sm:self-auto"
              >
                <span>Correct Specifications</span>
              </button>
            </div>
          ) : assessment.gaps.length === 0 || isPostRecheck ? (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-300/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in duration-300">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-emerald-950">
                    No compliance gaps identified from the currently available product data.
                  </h3>
                  <p className="text-xs text-emerald-800 mt-0.5">
                    Your product specifications satisfy evaluated requirements under {assessment.referenceStandard}.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-white/80 px-3 py-1.5 rounded-lg border border-emerald-200 self-start sm:self-auto">
                <TrendingUp className="w-4 h-4 text-emerald-600" />
                <span>Estimated Readiness: {assessment.readiness?.score_display || `${assessment.readinessScore}%`}</span>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-300/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-amber-950">
                    Potential compliance gaps detected ({assessment.gaps.length} items)
                  </h3>
                  <p className="text-xs text-amber-800 mt-0.5">
                    Remediate identified parameter gaps prior to submitting formal test samples.
                  </p>
                </div>
              </div>
              <button
                onClick={onRecheck}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-xl shadow-sm transition-all self-start sm:self-auto group"
              >
                <RotateCw className="w-3.5 h-3.5 group-hover:rotate-180 transition-transform duration-500" />
                <span>Simulate Fixes & Re-check</span>
              </button>
            </div>
          )}

          {/* Grid: Left column (Gauge + Cost + Timeline), Right column (Gaps & Recommendations) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column (4 Cols) */}
            <div className="lg:col-span-4 space-y-5">
              {/* Readiness Score Card */}
              <ReadinessGauge
                score={assessment.readiness?.score ?? assessment.readinessScore}
                scoreDisplay={assessment.readiness?.score_display}
                isPostRecheck={isPostRecheck}
                referenceStandard={assessment.referenceStandard}
                gapCount={assessment.gaps.length}
                assessmentState={assessment.assessment_state || assessment.readiness?.assessment_state}
              />

              {/* Cost Estimate Card */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center">
                      <IndianRupee className="w-4 h-4" />
                    </div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Estimated Certification Cost
                    </h4>
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                    Prototype Estimate
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-500">Projected Total:</span>
                    <span className="text-2xl font-extrabold text-slate-900">
                      ₹{assessment.costEstimate.totalFees.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5 text-xs text-slate-600 pt-1">
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span>Accredited Lab Testing</span>
                    <span className="font-semibold text-slate-800">
                      ₹{assessment.costEstimate.testingFees.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-50">
                    <span>BIS Statutory Fees</span>
                    <span className="font-semibold text-slate-800">
                      ₹{assessment.costEstimate.bisRelatedFees.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span>Documentation Preparation</span>
                    <span className="font-semibold text-slate-800">
                      ₹{assessment.costEstimate.documentationFees.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 pt-1 leading-tight">
                  *{assessment.costEstimate.disclaimer}
                </p>
              </div>

              {/* Timeline Estimate Card */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
                      <Clock className="w-4 h-4" />
                    </div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Estimated Timeline
                    </h4>
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                    Benchmark
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-500">Total Turnaround:</span>
                    <span className="text-2xl font-extrabold text-slate-900">
                      {assessment.timelineEstimate.range}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-xs pt-1">
                  {assessment.timelineEstimate.phases.map((p, idx) => (
                    <div key={idx} className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                      <div className="flex justify-between font-semibold text-slate-800">
                        <span>{p.phase}</span>
                        <span className="text-brand-700">{p.duration}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">{p.description}</p>
                    </div>
                  ))}
                </div>

                <p className="text-[10px] text-slate-400 pt-1 leading-tight">
                  *{assessment.timelineEstimate.disclaimer}
                </p>
              </div>
            </div>

            {/* Right Column (8 Cols): Gaps & Recommended Actions */}
            <div className="lg:col-span-8 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    {assessment.gaps.length === 0
                      ? 'Verified Technical Parameters & Requirements'
                      : 'Potential Compliance Gaps & Actions'}
                  </h2>
                  <p className="text-xs text-slate-500">
                    Evaluated against {assessment.referenceStandard} requirements with deterministic verification.
                  </p>
                </div>
                <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                  {assessment.gaps.length === 0
                    ? '0 Gaps'
                    : `${assessment.gaps.filter((g) => g.isResolved).length} / ${assessment.gaps.length} Resolved`}
                </span>
              </div>

              {/* Gaps List or Clean State */}
              {assessment.gaps.length === 0 ? (
                <div className="p-6 rounded-2xl border border-emerald-200 bg-emerald-50/50 text-emerald-950 flex items-start gap-4">
                  <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-emerald-950">
                      No compliance gaps identified from available product data
                    </h3>
                    <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                      All evaluated parameters for <strong>{assessment.productName}</strong> satisfy reference requirements under standard <strong>{assessment.referenceStandard}</strong>. Your product is ready for dossier compilation and laboratory sample scheduling.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {assessment.gaps.map((gap) => (
                    <GapCard
                      key={gap.id}
                      gap={gap}
                      onAction={(g) => setSelectedGap(g)}
                      onViewEvidence={(g) => setEvidenceItem(g)}
                    />
                  ))}
                </div>
              )}

              {/* Action Banner */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-brand-950 text-white shadow-xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-brand-300 bg-brand-900/80 px-2.5 py-0.5 rounded border border-brand-700/60">
                      Pre-Certification Pipeline
                    </span>
                    <h3 className="text-base font-bold text-white mt-1.5">
                      {assessment.gaps.length === 0
                        ? 'Assessment Verified — Ready for Application Dossier'
                        : 'Address non-conformities before testing application'}
                    </h3>
                    <p className="text-xs text-slate-300 mt-1 max-w-lg leading-relaxed">
                      {assessment.gaps.length === 0
                        ? `All verified specifications satisfy ${assessment.referenceStandard}. Proceed to review pre-filled Form IV schedules in the Application Dossier.`
                        : `Simulate engineering corrections and test documentation attachments under ${assessment.referenceStandard} to re-evaluate certification readiness.`}
                    </p>
                  </div>

                  <button
                    onClick={assessment.gaps.length === 0 ? () => setActiveTab('dossier') : onRecheck}
                    className={`inline-flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-xs shadow-lg transition-all flex-shrink-0 ${
                      assessment.gaps.length === 0
                        ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                        : 'bg-brand-500 hover:bg-brand-400 text-white shadow-brand-500/30 hover:scale-105'
                    }`}
                  >
                    {assessment.gaps.length === 0 ? (
                      <>
                        <FileSpreadsheet className="w-4 h-4" />
                        <span>View Application Dossier</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    ) : (
                      <>
                        <RotateCw className="w-4 h-4" />
                        <span>Re-check Product</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Dossier Preparation View */}
      {activeTab === 'dossier' && (
        <ApplicationPrepView applicationId={assessment.id} />
      )}

      {/* Tab 3: Tracking View */}
      {activeTab === 'tracking' && (
        <ApplicationTrackingView applicationId={assessment.id} />
      )}

      {/* Floating Ask BIS AI Button */}
      <div className="fixed bottom-6 right-6 z-30">
        <button
          onClick={() => setShowChatDrawer(true)}
          className="inline-flex items-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-full font-bold text-xs shadow-xl shadow-brand-600/30 hover:scale-105 transition-all group"
        >
          <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
          <span>Ask BIS AI</span>
        </button>
      </div>

      {/* Interactive Guidance Modal */}
      {selectedGap && (
        <GuidanceModal
          gap={selectedGap}
          onClose={() => setSelectedGap(null)}
          onApplyFix={() => {
            setSelectedGap(null);
            onRecheck();
          }}
        />
      )}

      {/* Evidence Deep-Dive Modal */}
      {evidenceItem && (
        <EvidenceModal
          item={evidenceItem}
          standardId={assessment.referenceStandard}
          onClose={() => setEvidenceItem(null)}
        />
      )}

      {/* AI Assessment Report Modal */}
      {showReportModal && (
        <ReportModal
          assessment={assessment}
          onClose={() => setShowReportModal(false)}
        />
      )}

      {/* Blockchain Integrity Modal */}
      {showVerifyModal && (
        <BlockchainVerifyModal onClose={() => setShowVerifyModal(false)} />
      )}

      {/* Contextual Chat Drawer */}
      {showChatDrawer && (
        <ContextualChatDrawer
          applicationId={assessment.id}
          productName={assessment.productName}
          standardId={assessment.referenceStandard}
          onClose={() => setShowChatDrawer(false)}
        />
      )}
    </div>
  );
};
