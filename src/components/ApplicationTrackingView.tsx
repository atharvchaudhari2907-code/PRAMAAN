import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  CheckCircle2,
  Clock,
  CircleDot,
  RefreshCw,
  PlusCircle,
  FileCheck2,
  Send,
  Calendar,
  Layers,
  Building2,
  Check
} from 'lucide-react';

interface ApplicationTrackingViewProps {
  applicationId: string;
}

interface StatusEvent {
  id: string;
  application_id: string;
  from_status?: string;
  to_status: string;
  event_type?: string;
  description?: string;
  note?: string;
  source: string;
  created_at: string;
}

const LIFECYCLE_STAGES = [
  { code: 'DRAFT', label: 'Application Drafted', desc: 'Initial registration and draft dossier created.' },
  { code: 'DOCUMENT_UPLOADED', label: 'Documents Uploaded', desc: 'Engineering drawings and datasheets uploaded.' },
  { code: 'PARAMETER_REVIEW', label: 'Parameter Extraction', desc: 'Structured technical parameters parsed and confirmed.' },
  { code: 'STANDARD_MATCHING', label: 'Standard Matched', desc: 'Primary Indian Standard mapped and aligned.' },
  { code: 'COMPLIANCE_ANALYSIS', label: 'Compliance Analysis', desc: 'Clause-by-clause deterministic safety checks completed.' },
  { code: 'READY_FOR_APPLICATION', label: 'Readiness Gate Passed', desc: 'Pre-requisite specifications and checklist verified.' },
  { code: 'APPLICATION_PREPARED', label: 'Dossier Generated', desc: 'Official Form I, II, IV and Technical Dossier compiled.' },
  { code: 'SUBMITTED', label: 'Portal Submission', desc: 'Submitted to BIS Manakonline portal with reference.' },
  { code: 'LAB_TESTING', label: 'Laboratory Testing', desc: 'Specimens dispatched for accredited lab testing.' },
  { code: 'INSPECTION', label: 'Factory Inspection', desc: 'BIS on-site surveillance audit and SIT verification.' },
  { code: 'BIS_SCRUTINY', label: 'BIS Directorate Scrutiny', desc: 'Committee review and technical evaluation.' },
  { code: 'APPROVED', label: 'Certification Approved', desc: 'Grant of licence authorized by BIS Directorate.' },
  { code: 'CERTIFICATE_ISSUED', label: 'Certificate Issued', desc: 'Standard Mark (ISI) Licence issued & anchored.' },
];

export const ApplicationTrackingView: React.FC<ApplicationTrackingViewProps> = ({ applicationId }) => {
  const [appData, setAppData] = useState<any>(null);
  const [events, setEvents] = useState<StatusEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogModal, setShowLogModal] = useState(false);
  const [nextStatus, setNextStatus] = useState('LAB_TESTING');
  const [eventDesc, setEventDesc] = useState('');
  const [eventNote, setEventNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadTrackingData = async () => {
    try {
      const [app, evts] = await Promise.all([
        api.getApplication(applicationId),
        api.getApplicationEvents(applicationId),
      ]);
      setAppData(app);
      setEvents(evts || []);
    } catch (err) {
      console.warn('Failed to load tracking data from backend:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrackingData();
  }, [applicationId]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eventDesc.trim()) return;

    setSubmitting(true);
    try {
      await api.createApplicationEvent(applicationId, {
        to_status: nextStatus,
        event_type: 'MILESTONE_LOGGED',
        description: eventDesc.trim(),
        note: eventNote.trim() || undefined,
        source: 'MANUFACTURER',
      });
      setEventDesc('');
      setEventNote('');
      setShowLogModal(false);
      await loadTrackingData();
    } catch (err) {
      console.error('Failed to log event:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 text-xs">
        <Clock className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
        <span>Loading live application lifecycle tracking...</span>
      </div>
    );
  }

  const currentStatus = appData?.status || 'DRAFT';
  const currentStageIndex = LIFECYCLE_STAGES.findIndex((s) => s.code === currentStatus);
  const activeIndex = currentStageIndex >= 0 ? currentStageIndex : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">Application Lifecycle & Audit Tracking</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-50 text-brand-700 border border-brand-200">
              Live Backend Audit Log
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Application Number: <strong className="text-slate-800">{appData?.application_number || applicationId}</strong> • {appData?.product_name || 'Product'} ({appData?.primary_standard_id || 'IS Standard'})
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-600 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200">
            <span>Current Stage: </span>
            <strong className="text-brand-700 ml-1">
              {LIFECYCLE_STAGES[activeIndex]?.label || currentStatus}
            </strong>
          </div>

          <button
            onClick={() => setShowLogModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-xs transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Log Milestone</span>
          </button>
        </div>
      </div>

      {/* 13-Stage Progression Timeline */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Statutory Certification Stages
            </h3>
          </div>
          <span className="text-[11px] font-medium text-slate-500">
            Stage {activeIndex + 1} of {LIFECYCLE_STAGES.length}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {LIFECYCLE_STAGES.map((stage, idx) => {
            const isCompleted = idx < activeIndex;
            const isCurrent = idx === activeIndex;

            return (
              <div
                key={stage.code}
                className={`p-3.5 rounded-xl border transition-all ${
                  isCurrent
                    ? 'bg-brand-50/60 border-brand-300 ring-2 ring-brand-500/20 shadow-xs'
                    : isCompleted
                    ? 'bg-emerald-50/30 border-emerald-200'
                    : 'bg-slate-50/50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                        isCompleted
                          ? 'bg-emerald-600 text-white'
                          : isCurrent
                          ? 'bg-brand-600 text-white'
                          : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {isCompleted ? <Check className="w-3.5 h-3.5" /> : idx + 1}
                    </div>
                    <span className="text-xs font-bold text-slate-900">{stage.label}</span>
                  </div>

                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      isCompleted
                        ? 'bg-emerald-100 text-emerald-800'
                        : isCurrent
                        ? 'bg-brand-100 text-brand-800 animate-pulse'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {isCompleted ? 'Done' : isCurrent ? 'Active' : 'Queued'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">{stage.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Chronological Real Backend Audit Events */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Chronological Audit Log ({events.length} Events)
            </h3>
          </div>
          <button
            onClick={loadTrackingData}
            className="text-xs text-brand-600 hover:text-brand-700 font-medium inline-flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>

        {events.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6">No tracking events recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {events.map((evt) => (
              <div
                key={evt.id}
                className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-white transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-slate-900">
                      {evt.description || `Transitioned to ${evt.to_status}`}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700 uppercase">
                      {evt.to_status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                      Source: {evt.source}
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap">
                    {new Date(evt.created_at).toLocaleString()}
                  </span>
                </div>

                {evt.note && (
                  <p className="text-xs text-slate-600 mt-2 bg-white p-2 rounded-lg border border-slate-100">
                    {evt.note}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Milestone Log Modal */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Record Certification Milestone</h3>
            <p className="text-xs text-slate-500">
              Log an official lifecycle event or status transition for this application.
            </p>

            <form onSubmit={handleCreateEvent} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Stage / Lifecycle Status
                </label>
                <select
                  value={nextStatus}
                  onChange={(e) => setNextStatus(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden"
                >
                  {LIFECYCLE_STAGES.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.label} ({s.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Milestone Description *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 5 samples dispatched to NTH lab via courier DTDC-9921"
                  value={eventDesc}
                  onChange={(e) => setEventDesc(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Additional Notes / Reference Numbers (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Courier docket number, lab receipt ID, or officer notes..."
                  value={eventNote}
                  onChange={(e) => setEventNote(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Recording...' : 'Save Milestone'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
