import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

interface AnalysisProgressViewProps {
  onComplete: () => void;
  isRecheck?: boolean;
}

interface Step {
  id: number;
  label: string;
  sublabel: string;
}

export const AnalysisProgressView: React.FC<AnalysisProgressViewProps> = ({
  onComplete,
  isRecheck = false,
}) => {
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const initialSteps: Step[] = [
    { id: 1, label: 'Reading product specifications', sublabel: 'Extracting technical parameters and ratings...' },
    { id: 2, label: 'Identifying applicable requirements', sublabel: 'Mapping against canonical Indian Standards...' },
    { id: 3, label: 'Checking compliance parameters', sublabel: 'Benchmarking electrical, mechanical, and safety limits...' },
    { id: 4, label: 'Detecting potential gaps', sublabel: 'Evaluating safety margins and documentation completeness...' },
    { id: 5, label: 'Preparing assessment', sublabel: 'Generating transparent readiness estimate and recommendations...' },
  ];

  const recheckSteps: Step[] = [
    { id: 1, label: 'Verifying updated specifications', sublabel: 'Evaluating updated ratings and component tolerances...' },
    { id: 2, label: 'Validating attached test documentation', sublabel: 'Confirming parameters satisfy threshold limits...' },
    { id: 3, label: 'Auditing packaging artwork compliance', sublabel: 'Mandatory bilingual markings and ISI mark clearance verified...' },
    { id: 4, label: 'Synthesizing updated readiness score', sublabel: 'Calculating elevated compliance readiness index...' },
  ];

  const steps = isRecheck ? recheckSteps : initialSteps;

  useEffect(() => {
    // Step interval timing
    const stepDuration = isRecheck ? 450 : 550;
    const timer = setInterval(() => {
      setActiveStepIndex((prev) => {
        if (prev < steps.length) {
          return prev + 1;
        } else {
          clearInterval(timer);
          return prev;
        }
      });
    }, stepDuration);

    // Completion timeout
    const completeTimeout = setTimeout(() => {
      onComplete();
    }, steps.length * stepDuration + 400);

    return () => {
      clearInterval(timer);
      clearTimeout(completeTimeout);
    };
  }, [steps.length, isRecheck, onComplete]);

  const progressPercent = Math.min(Math.round((activeStepIndex / steps.length) * 100), 100);

  return (
    <div className="max-w-xl mx-auto px-4 py-12">
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-card p-8 text-center relative overflow-hidden">
        {/* Background ambient glow */}
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Animated Spinner */}
        <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 border border-brand-100 flex items-center justify-center mx-auto mb-5 relative">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600" />
          <Sparkles className="w-3.5 h-3.5 text-brand-500 absolute top-2 right-2" />
        </div>

        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          {isRecheck ? 'Re-evaluating Compliance Parameters...' : 'Analyzing your product...'}
        </h2>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          AI Pre-Certification engine is evaluating technical attributes against identified BIS standards.
        </p>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 rounded-full h-2 my-6 overflow-hidden">
          <div
            className="bg-brand-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Sequential Stepper */}
        <div className="space-y-3.5 text-left mt-6">
          {steps.map((step, index) => {
            const isCompleted = index < activeStepIndex;
            const isCurrent = index === activeStepIndex;

            return (
              <div
                key={step.id}
                className={`flex items-start gap-3 p-3 rounded-xl border transition-all duration-200 ${
                  isCompleted
                    ? 'bg-emerald-50/50 border-emerald-200/80 text-emerald-900'
                    : isCurrent
                    ? 'bg-brand-50/70 border-brand-200 text-brand-900 ring-1 ring-brand-400/30'
                    : 'bg-slate-50/50 border-slate-100 text-slate-400 opacity-60'
                }`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300" />
                  )}
                </div>

                <div>
                  <p className="text-xs font-semibold">{step.label}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">{step.sublabel}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
