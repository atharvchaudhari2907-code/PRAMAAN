import React from 'react';
import { ShieldCheck, Info, ExternalLink } from 'lucide-react';

interface FooterProps {
  onOpenAbout: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onOpenAbout }) => {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-brand-700 text-white flex items-center justify-center font-bold text-[10px]">
              BIS
            </div>
            <div>
              <p className="font-semibold text-slate-800">BIS AI Assistant — Hackathon Prototype</p>
              <p className="text-[11px] text-slate-500">Designed for Indian hardware & electronics manufacturers</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6">
            <button
              onClick={onOpenAbout}
              className="hover:text-brand-700 transition-colors flex items-center gap-1 text-xs"
            >
              <Info className="w-3.5 h-3.5" />
              <span>BIS Standards Catalog</span>
            </button>
            <span className="text-slate-300">•</span>
            <span>All Manufactured Product Categories</span>
            <span className="text-slate-300">•</span>
            <span>Non-official Pre-Certification Tool</span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-400">
          <p>© 2026 BIS AI Assistant Prototype. Universal Standards Compliance Engine.</p>
          <p className="text-center sm:text-right">
            Values, timelines, and costs are simulated estimates configured for pre-submission guidance.
          </p>
        </div>
      </div>
    </footer>
  );
};
