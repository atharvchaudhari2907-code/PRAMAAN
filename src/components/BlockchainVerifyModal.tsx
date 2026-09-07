import React, { useState } from 'react';
import { VerificationResult } from '../types/assessment';
import { assessmentService } from '../services/assessmentService';
import { X, ShieldCheck, CheckCircle2, AlertCircle, FileCheck, Hash, UploadCloud, ArrowRight, Clock } from 'lucide-react';

interface BlockchainVerifyModalProps {
  onClose: () => void;
}

export const BlockchainVerifyModal: React.FC<BlockchainVerifyModalProps> = ({ onClose }) => {
  const [hashInput, setHashInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);

  const calculateFileSha256 = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setCalculating(true);
      try {
        const computedHash = await calculateFileSha256(file);
        setHashInput(computedHash);
        const res = await assessmentService.verifyIntegrity(computedHash, file.name);
        setResult(res);
      } catch (err) {
        console.error('Error calculating hash:', err);
      } finally {
        setCalculating(false);
      }
    }
  };

  const handleManualVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hashInput.trim()) return;
    setCalculating(true);
    try {
      const res = await assessmentService.verifyIntegrity(hashInput.trim());
      setResult(res);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">Certificate Integrity Verification</h3>
              <p className="text-xs text-slate-500">Tamper-Evident SHA-256 Ledger Prototype</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-700">
          <p className="text-xs text-slate-600 leading-relaxed">
            Verify the cryptographic tamper-evident integrity of an issued BIS pre-certification report or product technical datasheet.
          </p>

          {/* Drag and drop document hasher */}
          <label className="border-2 border-dashed rounded-xl p-5 text-center cursor-pointer hover:border-brand-400 bg-slate-50 hover:bg-slate-100/60 transition-all block">
            <input type="file" onChange={handleFileChange} className="hidden" accept=".pdf" />
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-2">
              <UploadCloud className="w-5 h-5" />
            </div>
            <span className="font-semibold text-xs text-slate-800 block">
              {selectedFile ? selectedFile.name : 'Click to select Certificate or Datasheet PDF'}
            </span>
            <span className="text-[11px] text-slate-400 mt-0.5 block">
              Calculates SHA-256 client-side hash instantly
            </span>
          </label>

          {/* Or Manual Hash Input */}
          <form onSubmit={handleManualVerify} className="space-y-2">
            <label className="font-bold text-slate-700 uppercase tracking-wider text-[10px] block">
              Or Paste SHA-256 Hash Digest
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={hashInput}
                onChange={(e) => setHashInput(e.target.value)}
                placeholder="e.g. e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                className="flex-1 px-3 py-2 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <button
                type="submit"
                disabled={calculating || !hashInput.trim()}
                className="px-4 py-2 text-xs font-bold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors disabled:opacity-50"
              >
                {calculating ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          </form>

          {/* Verification Result Card */}
          {result && (
            <div
              className={`p-4 rounded-xl border space-y-2.5 animate-in fade-in duration-200 ${
                result.is_verified
                  ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
                  : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            >
              <div className="flex items-center gap-2">
                {result.is_verified ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-slate-500 flex-shrink-0" />
                )}
                <span className="font-bold text-xs">
                  {result.is_verified ? 'Authentic Document Record Confirmed' : 'Hash Computed — Unregistered in Local Ledger'}
                </span>
              </div>

              <div className="space-y-1 font-mono text-[10px] bg-white/80 p-2.5 rounded-lg border border-slate-200/80">
                <p className="truncate">
                  <span className="font-sans font-bold text-slate-500">SHA-256: </span>
                  {result.sha256_hash}
                </p>
                {result.matched_application_id && (
                  <p>
                    <span className="font-sans font-bold text-slate-500">Record ID: </span>
                    {result.matched_application_id}
                  </p>
                )}
                <p>
                  <span className="font-sans font-bold text-slate-500">Ledger: </span>
                  {result.blockchain_network}
                </p>
              </div>

              <p className="text-[11px] leading-relaxed text-slate-600">{result.message}</p>
            </div>
          )}

          {/* Transparency Disclaimer */}
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-500 leading-tight">
            <strong>Honesty Notice:</strong> Blockchain / cryptographic hashing provides tamper-evident proof that a document has not been altered since generation. It does not replace official statutory BIS certification.
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex justify-end flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
