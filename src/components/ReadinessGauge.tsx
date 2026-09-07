import React, { useEffect, useState } from 'react';
import { CheckCircle2, AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';

interface ReadinessGaugeProps {
  score?: number | null;
  scoreDisplay?: string;
  isPostRecheck?: boolean;
  referenceStandard?: string;
  gapCount?: number;
  assessmentState?: string;
}

export const ReadinessGauge: React.FC<ReadinessGaugeProps> = ({
  score,
  scoreDisplay,
  isPostRecheck,
  referenceStandard,
  gapCount = 0,
  assessmentState,
}) => {
  const numericScore = typeof score === 'number' ? score : null;
  const [animatedScore, setAnimatedScore] = useState(numericScore || 0);

  useEffect(() => {
    if (numericScore === null) return;
    let start = 0;
    const duration = 1200;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const currentVal = Math.round(start + (numericScore - start) * ease);
      setAnimatedScore(currentVal);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [numericScore]);

  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = numericScore !== null
    ? circumference - (numericScore / 100) * circumference
    : circumference;

  const isConflict = assessmentState === 'EXTRACTION_CONFLICT';
  const isInsufficient = numericScore === null || assessmentState === 'INSUFFICIENT_EVIDENCE';
  const hasGaps = gapCount > 0 || assessmentState === 'GAPS_FOUND';
  const isHighReadiness = !isConflict && !isInsufficient && !hasGaps && (numericScore !== null ? numericScore >= 90 : false);

  let strokeColor = '#10b981'; // Emerald
  let badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  let badgeText = 'No Gaps Identified';

  if (isConflict) {
    strokeColor = '#ef4444'; // Red
    badgeBg = 'bg-rose-50 text-rose-800 border-rose-200';
    badgeText = 'Extraction Conflict';
  } else if (isInsufficient) {
    strokeColor = '#94a3b8'; // Slate
    badgeBg = 'bg-slate-100 text-slate-700 border-slate-200';
    badgeText = 'Evidence Pending';
  } else if (hasGaps) {
    strokeColor = '#f59e0b'; // Amber
    badgeBg = 'bg-amber-50 text-amber-800 border-amber-200';
    badgeText = gapCount > 0 ? `Gaps Detected (${gapCount})` : 'Gaps Detected';
  } else if (isHighReadiness) {
    strokeColor = '#10b981';
    badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
    badgeText = 'High Readiness';
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-2xl border border-slate-200/90 shadow-sm relative overflow-hidden">
      {/* Background radial glow */}
      <div
        className={`absolute -top-12 -right-12 w-48 h-48 rounded-full blur-3xl pointer-events-none opacity-20 ${
          isConflict ? 'bg-rose-400' : isHighReadiness ? 'bg-emerald-400' : 'bg-amber-400'
        }`}
      />

      <div className="relative flex items-center justify-center">
        <svg className="w-44 h-44 -rotate-90 transform" viewBox="0 0 160 160">
          {/* Background circle track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            className="text-slate-100"
            strokeWidth="12"
            stroke="currentColor"
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke={strokeColor}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="animate-gauge"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-3">
          {numericScore !== null ? (
            <>
              <span className="text-4xl font-extrabold tracking-tight text-slate-900">
                {animatedScore}%
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mt-0.5">
                Estimated Readiness
              </span>
            </>
          ) : (
            <>
              <span className="text-2xl font-bold tracking-tight text-slate-700">
                —
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 mt-0.5 text-center leading-tight">
                {scoreDisplay || 'Estimated Readiness'}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Label and status below gauge */}
      <div className="mt-4 text-center space-y-1.5">
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${badgeBg}`}>
          {isConflict ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>{badgeText}</span>
            </>
          ) : isHighReadiness || (!hasGaps && !isInsufficient) ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>{badgeText}</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>{badgeText}</span>
            </>
          )}
        </div>

        <p className="text-xs text-slate-500">
          {isConflict
            ? 'Compliance check blocked due to parameter conflict'
            : isInsufficient
            ? 'Readiness unavailable — insufficient validated evidence'
            : hasGaps
            ? 'Estimated readiness before remediation'
            : 'Estimated ready for pre-submission testing'}
        </p>

        {referenceStandard && (
          <p className="text-[11px] font-medium text-brand-700 bg-brand-50/80 px-2 py-0.5 rounded inline-block max-w-full truncate">
            Reference standard: {referenceStandard}
          </p>
        )}
      </div>
    </div>
  );
};
