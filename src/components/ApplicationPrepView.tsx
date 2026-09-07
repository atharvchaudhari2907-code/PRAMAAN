import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  FileCheck2,
  Download,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Building,
  Copy,
  Check,
  ShieldCheck,
  FileText,
  FileCode,
  Layers,
  Send,
  RefreshCw,
  Hash,
  AlertCircle
} from 'lucide-react';

interface ApplicationPrepViewProps {
  applicationId: string;
}

export const ApplicationPrepView: React.FC<ApplicationPrepViewProps> = ({ applicationId }) => {
  const [readiness, setReadiness] = useState<any>(null);
  const [checklist, setChecklist] = useState<any[]>([]);
  const [forms, setForms] = useState<Record<string, any>>({});
  const [generatedDocs, setGeneratedDocs] = useState<any[]>([]);
  const [activeFormTab, setActiveFormTab] = useState<'FORM_I' | 'FORM_II' | 'FORM_IV' | 'TECHNICAL_DOSSIER'>('FORM_I');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Submission modal state
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [refNumber, setRefNumber] = useState('');
  const [submitter, setSubmitter] = useState('');
  const [submitNotes, setSubmitNotes] = useState('');
  const [submittingApp, setSubmittingApp] = useState(false);

  // Form download state
  const [downloadingForm, setDownloadingForm] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [rGate, chk, fms, docs] = await Promise.all([
        api.getReadinessGate(applicationId),
        api.getChecklist(applicationId),
        api.getForms(applicationId),
        api.listGeneratedDocuments(applicationId),
      ]);
      setReadiness(rGate);
      setChecklist(chk || []);
      setForms(fms || {});
      setGeneratedDocs(docs || []);
    } catch (err) {
      console.warn('Error loading dossier prep data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [applicationId]);

  const handleVerifyItem = async (itemId: string, verified: boolean) => {
    try {
      await api.verifyChecklistItem(applicationId, itemId, verified, 'Verified via Application Dossier Gate');
      await loadData();
    } catch (err) {
      console.error('Failed to verify checklist item:', err);
    }
  };

  const handleGenerateDossier = async () => {
    setGenerating(true);
    try {
      const docs = await api.generateDocuments(applicationId);
      setGeneratedDocs(docs);
      await loadData();
    } catch (err) {
      console.error('Failed to generate dossier:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleDownloadForm = async (formType: string, format: 'pdf' | 'json') => {
    const key = `${formType}_${format}`;
    setDownloadingForm(key);
    setDownloadError(null);
    try {
      await api.downloadForm(applicationId, formType, format);
      const updatedDocs = await api.listGeneratedDocuments(applicationId);
      if (updatedDocs) setGeneratedDocs(updatedDocs);
    } catch (err: any) {
      setDownloadError(err?.message || `Failed to download ${formType} (${format.toUpperCase()})`);
    } finally {
      setDownloadingForm(null);
    }
  };

  const handleOfficialSubmission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refNumber.trim() || !submitter.trim()) return;

    setSubmittingApp(true);
    try {
      await api.submitApplication(applicationId, {
        reference_number: refNumber.trim(),
        submitted_by: submitter.trim(),
        notes: submitNotes.trim() || undefined,
        portal_url: 'https://www.manakonline.in',
      });
      setShowSubmitModal(false);
      setRefNumber('');
      setSubmitNotes('');
      await loadData();
    } catch (err) {
      console.error('Failed to submit application:', err);
    } finally {
      setSubmittingApp(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 text-xs">
        <Clock className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
        <span>Evaluating BIS readiness gate and compiling technical dossier...</span>
      </div>
    );
  }

  const isReady = readiness?.is_ready ?? false;
  const activeForm = forms[activeFormTab];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-500/30 text-brand-200 border border-brand-400/40 uppercase">
              Phase 3 Technical Dossier
            </span>
            <span className="text-xs text-slate-300">
              Readiness: <strong>{readiness?.readiness_score ?? 0}%</strong>
            </span>
          </div>
          <h2 className="text-lg font-bold text-white mt-1.5">
            BIS Application Dossier & Document Generation
          </h2>
          <p className="text-xs text-slate-300 mt-0.5 max-w-xl">
            Pre-filled statutory Form I, II, IV and 14-section Technical Dossier with monotonic versioning & SHA-256 integrity.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
          <button
            onClick={handleGenerateDossier}
            disabled={generating}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-brand-500 hover:bg-brand-600 text-white rounded-xl transition-colors shadow-sm shadow-brand-500/20 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Generating v...' : 'Generate Official Dossier'}</span>
          </button>

          <button
            onClick={() => setShowSubmitModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-white text-slate-900 hover:bg-slate-100 rounded-xl transition-colors shadow-sm"
          >
            <Send className="w-3.5 h-3.5 text-brand-600" />
            <span>Record Manakonline Filing</span>
          </button>
        </div>
      </div>

      {/* Readiness Gate Banner */}
      <div
        className={`p-4 rounded-xl border flex items-start gap-3 ${
          isReady
            ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
            : readiness?.validation_status === 'GAPS_DETECTED'
            ? 'bg-rose-50/70 border-rose-200 text-rose-900'
            : 'bg-amber-50/70 border-amber-200 text-amber-900'
        }`}
      >
        {isReady ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        )}
        <div className="text-xs space-y-1 flex-1">
          <div className="flex items-center justify-between">
            <p className="font-bold text-sm">
              Readiness Gate: {readiness?.validation_status || 'EVALUATING'} ({readiness?.readiness_score || 0}/100)
            </p>
            <span className="font-semibold text-[11px] px-2 py-0.5 rounded bg-white/80 border border-current">
              {isReady ? 'Gate Passed' : 'Gating Conditions Unmet'}
            </span>
          </div>

          {readiness?.failed_critical_clauses?.length > 0 && (
            <div className="mt-1 text-rose-800">
              <span className="font-bold">Failed Critical Safety Clauses:</span>
              <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                {readiness.failed_critical_clauses.map((c: string, idx: number) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {readiness?.missing_documents?.length > 0 && (
            <div className="mt-1 text-amber-800">
              <span className="font-bold">Missing Mandatory Documents:</span>
              <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                {readiness.missing_documents.map((d: string, idx: number) => (
                  <li key={idx}>{d}</li>
                ))}
              </ul>
            </div>
          )}

          {readiness?.required_actions?.length > 0 && (
            <div className="mt-1 text-slate-700 font-medium">
              <span className="font-bold text-slate-900">Required Next Steps:</span>
              <ul className="list-disc pl-4 mt-0.5 space-y-0.5">
                {readiness.required_actions.map((a: string, idx: number) => (
                  <li key={idx}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Generated Documents Manager (Versioned PDFs & JSON) */}
      {generatedDocs.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-brand-600" />
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Generated Official Documents ({generatedDocs.length} Files)
              </h3>
            </div>
            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              Latest: v{Math.max(...generatedDocs.map((d) => d.version), 1)}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {generatedDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 flex flex-col justify-between gap-3"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {doc.mime_type === 'application/pdf' ? (
                        <FileText className="w-4 h-4 text-rose-600 flex-shrink-0" />
                      ) : (
                        <FileCode className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      )}
                      <span className="text-xs font-bold text-slate-900 truncate">
                        {doc.document_name || doc.document_type}
                      </span>
                    </div>

                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand-100 text-brand-800">
                      v{doc.version}
                    </span>
                  </div>

                  <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Hash className="w-3 h-3 text-slate-400" />
                    <span className="font-mono truncate">{doc.sha256_hash.substring(0, 24)}...</span>
                    <button
                      onClick={() => handleCopy(doc.sha256_hash, doc.id)}
                      className="p-1 hover:text-slate-700"
                      title="Copy full SHA-256 hash"
                    >
                      {copiedHash === doc.id ? (
                        <Check className="w-3 h-3 text-emerald-600" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200/60">
                  <span className="text-[10px] text-slate-400">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>

                  <a
                    href={api.getGeneratedDocumentDownloadUrl(applicationId, doc.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-bold text-brand-600 hover:text-brand-700"
                  >
                    <Download className="w-3 h-3" />
                    <span>Download {doc.mime_type === 'application/pdf' ? 'PDF' : 'JSON'}</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dynamic Document Checklist Section */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Dynamic Document Checklist ({checklist.filter((i) => i.verified).length}/{checklist.length} Verified)
            </h3>
          </div>
          <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            BIS Scheme I Requisites
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {checklist.map((item) => (
            <div
              key={item.id}
              className={`p-3 rounded-xl border flex flex-col justify-between gap-2 ${
                item.verified
                  ? 'bg-emerald-50/40 border-emerald-200'
                  : item.status === 'UPLOADED'
                  ? 'bg-blue-50/40 border-blue-200'
                  : 'bg-slate-50/60 border-slate-200'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-bold text-slate-900">{item.name}</span>
                  <div className="flex items-center gap-1.5">
                    {item.required && (
                      <span className="text-[9px] font-bold text-rose-600 bg-rose-50 px-1 py-0.5 rounded border border-rose-200 uppercase">
                        Mandatory
                      </span>
                    )}
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                        item.status === 'VERIFIED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.status === 'UPLOADED'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">{item.description}</p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-200/50">
                <span className="text-[10px] text-slate-400">
                  {item.verified ? 'Verified by Quality Assurance' : 'Verification Pending'}
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleVerifyItem(item.id, !item.verified)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-colors ${
                      item.verified
                        ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                        : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    }`}
                  >
                    {item.verified ? 'Unverify' : 'Mark Verified'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Statutory BIS Forms Direct Download Hub */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-600" />
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Download Statutory BIS Forms & Dossiers
              </h3>
              <p className="text-[11px] text-slate-500">
                Directly download individual Scheme I schedules, compliance declarations, and technical dossiers as PDF or JSON.
              </p>
            </div>
          </div>
          {downloadError && (
            <span className="text-[11px] font-semibold text-rose-600 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">
              {downloadError}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              type: 'FORM_I',
              title: 'FORM I',
              subtitle: 'Application for Grant of Licence',
              desc: 'Manufacturer particulars, factory location, manufacturing premises, and product specification scope under Scheme I.',
            },
            {
              type: 'FORM_II',
              title: 'FORM II',
              subtitle: 'Self-Declaration & Test Protocol',
              desc: 'Declarations on testing capabilities, quality control personnel, and standard conformance protocols.',
            },
            {
              type: 'FORM_IV',
              title: 'FORM IV',
              subtitle: 'Pre-Certification Compliance Dossier',
              desc: 'Clause-by-clause evaluation report, verified electrical/physical parameters, and calculated readiness index.',
            },
            {
              type: 'TECHNICAL_DOSSIER',
              title: 'TECHNICAL DOSSIER',
              subtitle: '14-Section Technical File',
              desc: 'Comprehensive engineering file: product BOM, circuit schematics, markings, rating plates, and quality plans.',
            },
          ].map((item) => {
            const hasGenerated = generatedDocs.some((d) => d.document_type === item.type);
            const isPdfLoading = downloadingForm === `${item.type}_pdf`;
            const isJsonLoading = downloadingForm === `${item.type}_json`;

            return (
              <div
                key={item.type}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300 transition-all flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-extrabold text-slate-900 tracking-wider">{item.title}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        hasGenerated
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {hasGenerated ? 'Ready' : 'On-Demand'}
                    </span>
                  </div>
                  <h5 className="text-[11px] font-bold text-brand-700">{item.subtitle}</h5>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{item.desc}</p>
                </div>

                <div className="pt-2 border-t border-slate-200/80 flex items-center gap-2">
                  <button
                    onClick={() => handleDownloadForm(item.type, 'pdf')}
                    disabled={isPdfLoading || isJsonLoading}
                    className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-rose-50 text-rose-700 border border-slate-200 hover:border-rose-300 rounded-lg text-xs font-bold transition-colors disabled:opacity-50 shadow-xs"
                    title={`Download ${item.title} as official PDF`}
                  >
                    {isPdfLoading ? (
                      <RefreshCw className="w-3 h-3 animate-spin text-rose-600" />
                    ) : (
                      <FileText className="w-3 h-3 text-rose-600" />
                    )}
                    <span>PDF</span>
                  </button>

                  <button
                    onClick={() => handleDownloadForm(item.type, 'json')}
                    disabled={isPdfLoading || isJsonLoading}
                    className="flex-1 inline-flex items-center justify-center gap-1 px-2.5 py-1.5 bg-white hover:bg-blue-50 text-blue-700 border border-slate-200 hover:border-blue-300 rounded-lg text-xs font-bold transition-colors disabled:opacity-50 shadow-xs"
                    title={`Download ${item.title} as structured JSON schema`}
                  >
                    {isJsonLoading ? (
                      <RefreshCw className="w-3 h-3 animate-spin text-blue-600" />
                    ) : (
                      <FileCode className="w-3 h-3 text-blue-600" />
                    )}
                    <span>JSON</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* BIS Form Definitions Tabs with Field-Level Provenance */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-brand-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Statutory Form Schedules & Provenance Tracking
            </h3>
          </div>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
            {(['FORM_I', 'FORM_II', 'FORM_IV', 'TECHNICAL_DOSSIER'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveFormTab(tab)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                  activeFormTab === tab
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {activeForm ? (
          <div className="space-y-6">
            <div className="flex items-start justify-between gap-4 flex-wrap pb-4 border-b border-slate-100">
              <div>
                <h4 className="text-sm font-bold text-slate-900">{activeForm.title}</h4>
                <p className="text-xs text-slate-500 mt-0.5">{activeForm.description}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadForm(activeFormTab, 'pdf')}
                  disabled={downloadingForm === `${activeFormTab}_pdf`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-bold transition-all disabled:opacity-50 shadow-xs"
                  title={`Download ${activeFormTab} as official PDF`}
                >
                  {downloadingForm === `${activeFormTab}_pdf` ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-rose-600" />
                  ) : (
                    <FileText className="w-3.5 h-3.5 text-rose-600" />
                  )}
                  <span>Download PDF</span>
                </button>

                <button
                  onClick={() => handleDownloadForm(activeFormTab, 'json')}
                  disabled={downloadingForm === `${activeFormTab}_json`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl text-xs font-bold transition-all disabled:opacity-50 shadow-xs"
                  title={`Download ${activeFormTab} as structured JSON schema`}
                >
                  {downloadingForm === `${activeFormTab}_json` ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                  ) : (
                    <FileCode className="w-3.5 h-3.5 text-blue-600" />
                  )}
                  <span>Download JSON</span>
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {activeForm.sections?.map((sec: any) => (
                <div key={sec.section_id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    {sec.section_title}
                  </h5>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {sec.fields?.map((fld: any) => (
                      <div key={fld.field_key} className="p-2.5 rounded-lg bg-white border border-slate-100 space-y-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            {fld.label}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase ${
                              fld.source === 'AI_EXTRACTED'
                                ? 'bg-purple-50 text-purple-700 border border-purple-200'
                                : fld.source === 'MANUFACTURER_INPUT'
                                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                : fld.source === 'BIS_STANDARD_CATALOG'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {fld.source.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <p className="text-xs font-semibold text-slate-800 break-words">
                          {String(fld.value || '—')}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 text-center py-6">Form preview not loaded.</p>
        )}
      </div>

      {/* Record Submission Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Record BIS Manakonline Submission</h3>
            <p className="text-xs text-slate-500">
              Enter the official reference/acknowledgement number provided after lodging your application on{' '}
              <a
                href="https://www.manakonline.in"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-600 underline font-semibold"
              >
                manakonline.in
              </a>
              .
            </p>

            <form onSubmit={handleOfficialSubmission} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  BIS Acknowledgement / Reference Number *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BIS-MANAK-2026-894120"
                  value={refNumber}
                  onChange={(e) => setRefNumber(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Submitter Name / Designation *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rajesh Kumar (Quality Assurance Director)"
                  value={submitter}
                  onChange={(e) => setSubmitter(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Filing Notes / Fee Receipt ID (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Challan reference number, fee deposit date, or branch notes..."
                  value={submitNotes}
                  onChange={(e) => setSubmitNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:outline-hidden"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSubmitModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingApp}
                  className="px-4 py-2 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50"
                >
                  {submittingApp ? 'Recording...' : 'Confirm Submission'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
