import React from 'react';
import { ComplianceGap } from '../types/assessment';
import { AlertCircle, CheckCircle2, ChevronRight, Clock, HelpCircle, FileSearch } from 'lucide-react';

interface GapCardProps {
  gap: ComplianceGap;
  onAction: (gap: ComplianceGap) => void;
  onViewEvidence?: (gap: ComplianceGap) => void;
}

export const GapCard: React.FC<GapCardProps> = ({ gap, onAction, onViewEvidence }) => {
  const isResolved = gap.status === 'Resolved' || gap.isResolved;

  const getStatusBadge = () => {
    switch (gap.status) {
      case 'Resolved':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Resolved
          </span>
        );
      case 'Needs attention':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            Needs attention
          </span>
        );
      case 'Missing':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            Missing
          </span>
        );
      case 'Review required':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
            <HelpCircle className="w-3 h-3 text-indigo-600" />
            Review required
          </span>
        );
    }
  };

  const getPriorityBadge = () => {
    switch (gap.priority) {
      case 'HIGH PRIORITY':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-rose-50 text-rose-700 border border-rose-200">
            High Priority
          </span>
        );
      case 'MEDIUM PRIORITY':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-amber-50 text-amber-700 border border-amber-200">
            Medium Priority
          </span>
        );
      case 'REVIEW':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-slate-100 text-slate-700 border border-slate-200">
            Review Item
          </span>
        );
    }
  };

  return (
    <div
      className={`rounded-xl border transition-all p-5 ${
        isResolved
          ? 'bg-emerald-50/40 border-emerald-200'
          : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm hover:shadow'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
              isResolved
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-white'
            }`}
          >
            {gap.id.replace('GAP-', '')}
          </div>
          <h4 className="font-semibold text-slate-900 text-base">
            {gap.title}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          {getPriorityBadge()}
          {getStatusBadge()}
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3.5 bg-slate-50/70 p-3.5 rounded-lg border border-slate-100 text-xs">
        <div>
          <span className="font-medium text-slate-500 block mb-0.5">
            Current Product Specification:
          </span>
          <span
            className={`font-semibold ${
              isResolved ? 'text-emerald-700' : 'text-slate-800'
            }`}
          >
            {gap.currentValue}
          </span>
        </div>
        <div>
          <span className="font-medium text-slate-500 block mb-0.5">
            Reference Requirement:
          </span>
          <span className="font-semibold text-slate-800">
            {gap.referenceRequirement}
          </span>
        </div>
      </div>

      {/* Recommendation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <div className="text-xs text-slate-600">
          <span className="font-semibold text-slate-700">Recommendation: </span>
          <span>{gap.recommendation}</span>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {onViewEvidence && (
            <button
              type="button"
              onClick={() => onViewEvidence(gap)}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 transition-colors"
            >
              <FileSearch className="w-3.5 h-3.5" />
              <span>View Evidence</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => onAction(gap)}
            className={`inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors shadow-xs ${
              isResolved
                ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border border-emerald-300'
                : 'bg-brand-50 text-brand-700 hover:bg-brand-100 border border-brand-200 hover:border-brand-300'
            }`}
          >
            <span>{gap.actionButtonText}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
