import React, { useState } from 'react';
import { X, BookOpen, CheckCircle2, Layers, ShieldCheck } from 'lucide-react';

interface AboutStandardModalProps {
  onClose: () => void;
  activeStandardId?: string;
}

const STANDARDS_CATALOG = [
  {
    id: 'IS 302 (Part 1) : 2024',
    title: 'Safety of Household and Similar Electrical Appliances — Part 1: General Requirements',
    category: 'Household Electrical Appliances',
    scope: 'Deals with the safety of electrical appliances for household and similar purposes, their rated voltage being not more than 250V for single-phase.',
    clauses: [
      { name: 'Clause 7 Marking and Instructions', desc: 'Mandatory bilingual marking of rated input, voltage, model, and manufacturer.' },
      { name: 'Clause 8 Protection Against Electric Shock', desc: 'No accessible live parts during normal operation or cleaning.' },
      { name: 'Clause 10 Power Input and Current', desc: 'Power input shall not exceed rated wattage by more than +15% / -10%.' },
      { name: 'Clause 13 Leakage Current & Electric Strength', desc: 'Leakage current shall not exceed 0.75 mA for Class I earthed appliances.' },
    ],
  },
  {
    id: 'IS 13252 (Part 1) : 2010',
    title: 'Information Technology Equipment — Safety — Part 1: General Requirements',
    category: 'Electronics & IT Goods',
    scope: 'Safety requirements for mains-powered or battery-powered information technology equipment and audio/video apparatus.',
    clauses: [
      { name: 'Clause 1.7 Markings and Instructions', desc: 'Legible identification of manufacturer, model designation, and electrical ratings.' },
      { name: 'Clause 2.1 Protection from Electric Shock', desc: 'Accessible parts must be SELV or protective earth bonded.' },
      { name: 'Clause 4.3 Design and Construction', desc: 'Mechanical enclosure strength, stability, and flammability classification.' },
      { name: 'Clause 5.1 Touch Current & Protective Conductor Current', desc: 'Touch current limits for stationary and portable equipment.' },
    ],
  },
  {
    id: 'IS 14286 (Part 2) : 2023',
    title: 'Terrestrial Photovoltaic (PV) Modules — Design Qualification and Type Approval',
    category: 'Solar & Renewable Energy',
    scope: 'Specifies requirements for the design qualification and type approval of terrestrial PV modules.',
    clauses: [
      { name: 'Clause 4.1 Visual Inspection', desc: 'Verification of module encapsulation, cell alignment, and junction box seal.' },
      { name: 'Clause 4.2 Maximum Power Determination', desc: 'Output power measurement at Standard Test Conditions (STC).' },
      { name: 'Clause 4.3 Insulation Test', desc: 'Dielectric withstand voltage between current-carrying parts and frame.' },
    ],
  },
  {
    id: 'IS 14543 : 2024',
    title: 'Packaged Drinking Water (Other Than Packaged Natural Mineral Water) — Specification',
    category: 'Water & Food Safety',
    scope: 'Mandatory quality, microbiological, physical, and chemical parameters for packaged drinking water.',
    clauses: [
      { name: 'Clause 4 Hygienic Conditions', desc: 'Hygienic processing in accordance with IS 2491 code of hygienic conditions.' },
      { name: 'Clause 5 Microbiological Requirements', desc: 'Zero detection of coliform, E. coli, and fecal streptococci.' },
      { name: 'Clause 6 Packaging and Labeling', desc: 'Tamper-evident food-grade containers and mandatory BIS Standard Mark.' },
    ],
  },
  {
    id: 'IS 694 : 2010',
    title: 'Polyvinyl Chloride Insulated Unsheathed and Sheathed Cables/Cords with Rigid and Flexible Conductor',
    category: 'Electrical Wiring & Cables',
    scope: 'Requirements for single core and multicore PVC insulated cables for working voltages up to and including 1100 V.',
    clauses: [
      { name: 'Clause 5 Conductor Specification', desc: 'High conductivity annealed plain or tinned copper conductor complying with IS 8130.' },
      { name: 'Clause 6 Insulation Thickness', desc: 'Standard radial thickness of PVC insulation for designated voltage grades.' },
      { name: 'Clause 14 High Voltage Test (Spark Test)', desc: 'Withstand test voltage without breakdown or spark failure.' },
    ],
  },
];

export const AboutStandardModal: React.FC<AboutStandardModalProps> = ({ onClose, activeStandardId }) => {
  const defaultIndex = activeStandardId
    ? Math.max(0, STANDARDS_CATALOG.findIndex((s) => s.id.includes(activeStandardId.split(':')[0].trim())))
    : 0;

  const [selectedIdx, setSelectedIdx] = useState(defaultIndex >= 0 ? defaultIndex : 0);
  const activeStd = STANDARDS_CATALOG[selectedIdx];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[88vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">BIS Standards Knowledge Base</h3>
              <p className="text-xs text-slate-500">Official Indian Standards & Evaluated Clauses</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Standard Selector Tabs */}
        <div className="px-6 pt-3 pb-2 border-b border-slate-100 flex gap-2 overflow-x-auto bg-slate-50/50">
          {STANDARDS_CATALOG.map((std, idx) => (
            <button
              key={std.id}
              onClick={() => setSelectedIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                selectedIdx === idx
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <span>{std.id.split(':')[0].trim()}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs text-slate-600">
          <div className="p-4 bg-brand-50/70 border border-brand-100 rounded-xl">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-brand-700 bg-brand-100 px-2 py-0.5 rounded">
                {activeStd.category}
              </span>
              <span className="text-xs font-bold text-slate-800">{activeStd.id}</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm mt-2">{activeStd.title}</h4>
            <p className="mt-1 text-slate-700 leading-relaxed">{activeStd.scope}</p>
          </div>

          <div className="space-y-2.5">
            <h5 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-brand-600" />
              Key Mandatory Clauses Evaluated by Assistant:
            </h5>
            <div className="grid grid-cols-1 gap-2">
              {activeStd.clauses.map((c, i) => (
                <div key={i} className="p-3 rounded-lg border border-slate-200 bg-slate-50/70">
                  <span className="font-bold text-slate-800">{c.name}:</span>
                  <p className="mt-0.5 text-slate-600 leading-relaxed">{c.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-amber-900 text-[11px] leading-relaxed">
            <strong>Pre-Certification Methodology:</strong> This AI assistant compares dynamic parameters extracted from engineering datasheets against standardized Indian Standards clauses to empower manufacturers to resolve technical non-conformities prior to formal BIS Manakonline filing.
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
