import React, { useEffect, useState } from 'react';
import { ArrowRight, Shield, Gauge, Wrench, Sparkles, FileText, CheckCircle2, ChevronRight, Clock, RefreshCw, PlusCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface LandingViewProps {
  onStartAssessment: () => void;
  onOpenAbout: () => void;
}

interface ApplicationItem {
  id: string;
  application_number: string;
  product_name: string;
  category: string;
  model_number?: string;
  manufacturer?: string;
  manufacturing_location?: string;
  status: string;
  readiness_score?: number;
  created_at: string;
}

export const LandingView: React.FC<LandingViewProps> = ({ onStartAssessment, onOpenAbout }) => {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loadingApps, setLoadingApps] = useState<boolean>(true);
  const [appError, setAppError] = useState<string | null>(null);

  const fetchApplications = async () => {
    setLoadingApps(true);
    setAppError(null);
    try {
      const data = await api.listApplications();
      setApplications(data || []);
    } catch (err: any) {
      // If backend is fresh or user has no applications, gracefully set empty
      setAppError(err.message || 'Unable to load applications');
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
      case 'CERTIFICATE_ISSUED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">Approved / Issued</span>;
      case 'READY_FOR_APPLICATION':
      case 'APPLICATION_PREPARED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">Ready for Submission</span>;
      case 'DOCUMENT_UPLOADED':
      case 'PARAMETER_REVIEW':
      case 'COMPLIANCE_ANALYSIS':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">Analysis in Progress</span>;
      case 'DRAFT':
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">Draft</span>;
    }
  };

  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative pt-12 pb-8 text-center max-w-4xl mx-auto px-4">
        {/* Subtle background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-400/10 rounded-full blur-3xl -z-10" />

        {/* Small Tagline Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-50 border border-brand-200/80 text-brand-800 text-xs font-semibold mb-6 shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          <span>AI-Powered Pre-Certification Assessment</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-[1.15]">
          Know your <span className="text-blue-600 dark:text-blue-400">BIS compliance readiness</span> before you apply.
        </h1>

        {/* Supporting Copy */}
        <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Analyze your product requirements, identify potential compliance gaps, and get actionable recommendations before submitting your certification application.
        </p>

        {/* Primary CTA button */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onStartAssessment}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 text-base font-semibold text-white bg-brand-600 hover:bg-brand-700 active:bg-brand-800 rounded-xl shadow-md shadow-brand-600/20 hover:shadow-lg transition-all group"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>

        <p className="mt-3 text-xs text-slate-500 font-medium">
          Multi-Category Indian Standards Evaluation • Scheme I & Scheme II Ready
        </p>
      </section>

      {/* Live Applications Dashboard Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
            <div>
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-brand-600" />
                <h2 className="text-xl font-bold text-slate-900">Your Certification Applications</h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Real-time synchronized records from the FastAPI compliance engine
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchApplications}
                disabled={loadingApps}
                className="p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-50 border border-slate-200 transition-colors"
                title="Refresh applications"
              >
                <RefreshCw className={`w-4 h-4 ${loadingApps ? 'animate-spin text-brand-600' : ''}`} />
              </button>
              <button
                onClick={onStartAssessment}
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors shadow-xs"
              >
                <PlusCircle className="w-4 h-4" />
                <span>New Application</span>
              </button>
            </div>
          </div>

          {loadingApps ? (
            <div className="py-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
              <Clock className="w-6 h-6 animate-spin text-brand-600" />
              <span>Loading registered applications...</span>
            </div>
          ) : applications.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {applications.map((app) => (
                <div
                  key={app.id}
                  className="p-5 rounded-xl border border-slate-200 hover:border-brand-300 hover:shadow-md transition-all bg-slate-50/50 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200/60">
                        {app.application_number}
                      </span>
                      {getStatusBadge(app.status)}
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">{app.product_name}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">{app.category}</p>
                    </div>
                    {app.model_number && (
                      <p className="text-xs text-slate-600">
                        <span className="text-slate-400">Model:</span> {app.model_number}
                      </p>
                    )}
                  </div>
                  <div className="pt-4 border-t border-slate-200/60 mt-4 flex items-center justify-between text-xs">
                    <span className="text-slate-400">
                      {new Date(app.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                    <button
                      onClick={onStartAssessment}
                      className="inline-flex items-center gap-1 font-semibold text-brand-600 hover:text-brand-700"
                    >
                      <span>Resume</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center text-slate-500 text-xs flex flex-col items-center gap-2">
              <FileText className="w-8 h-8 text-slate-300" />
              <p className="font-medium text-slate-700">No applications created yet</p>
              <p className="text-slate-400 max-w-sm">
                Get started by clicking &quot;Start Assessment&quot; to evaluate your product against relevant Indian Standards.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* 3 Core Value Pillars */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-subtle hover:shadow-card transition-all hover:border-brand-200 group">
            <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <Shield className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Compliance Check</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Identify potential gaps before application. Automatically compare your technical specifications against relevant Indian Standards requirements.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-subtle hover:shadow-card transition-all hover:border-brand-200 group">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <Gauge className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Readiness Score</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Get an estimated assessment of certification readiness. Understand your statistical probability of passing accredited lab testing on first attempt.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-white rounded-2xl p-7 border border-slate-200/90 shadow-subtle hover:shadow-card transition-all hover:border-brand-200 group">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
              <Wrench className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Actionable Guidance</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Understand what needs to be fixed before proceeding. Receive explicit engineering recommendations, test data checklists, and artwork guides.
            </p>
          </div>
        </div>
      </section>

      {/* Evaluation Presets Box */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-700/50">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-700">
            <div>
              <span className="text-[11px] font-bold tracking-wider uppercase text-brand-400 bg-brand-950/80 px-2.5 py-1 rounded border border-brand-800/60">
                Universal BIS Evaluator
              </span>
              <h3 className="text-xl font-bold text-white mt-2">
                Evaluate Any Manufactured Product
              </h3>
              <p className="text-xs text-slate-300 mt-1">
                Supports Household Appliances, IT & Electronics, Lighting, Industrial Machinery, and Kitchenware
              </p>
            </div>
            <button
              onClick={onStartAssessment}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-500 hover:bg-brand-600 text-white rounded-lg transition-colors flex-shrink-0"
            >
              <span>Begin Assessment</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 text-xs">
            <div>
              <span className="text-slate-400 block">Rated Wattage</span>
              <span className="font-bold text-slate-100 text-sm">9 W / 1200 W</span>
            </div>
            <div>
              <span className="text-slate-400 block">Supply Voltage</span>
              <span className="font-bold text-slate-100 text-sm">230 V AC</span>
            </div>
            <div>
              <span className="text-slate-400 block">Standards Supported</span>
              <span className="font-bold text-brand-300 text-sm">IS 16102, IS 302, IS 2347, IS 374</span>
            </div>
            <div>
              <span className="text-slate-400 block">Pipeline Status</span>
              <span className="font-bold text-emerald-400 text-sm">Active & Verified</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
