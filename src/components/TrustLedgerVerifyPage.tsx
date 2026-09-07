import React, { useEffect, useState } from 'react';
import { trustLedgerService } from '../services/trustLedgerService';
import { TrustLedgerVerificationResult } from '../types/trustLedger';
import {
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Hash,
  ShieldAlert,
  Database,
  ExternalLink,
  Layers,
  Clock
} from 'lucide-react';

interface TrustLedgerVerifyPageProps {
  publicProductId?: string;
}

export const TrustLedgerVerifyPage: React.FC<TrustLedgerVerifyPageProps> = ({ publicProductId }) => {
  const [result, setResult] = useState<TrustLedgerVerificationResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!publicProductId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      const data = await trustLedgerService.verifyProduct(publicProductId);
      setResult(data);
      setLoading(false);
    };
    load();
  }, [publicProductId]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-xs text-slate-500">
        <Clock className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
        <span>Verifying cryptographic anchor on Polygon / EVM ledger...</span>
      </div>
    );
  }

  if (!result || !result.record || result.overall_status === 'NOT_FOUND') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="rounded-3xl border border-rose-200 bg-white shadow-xl overflow-hidden">
          <div className="px-6 py-5 border-b border-rose-200 bg-gradient-to-r from-rose-50 to-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-rose-100 text-rose-700">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Public Product Verification</p>
                <h1 className="text-2xl font-extrabold text-slate-900">Certificate Not Found</h1>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-4">
            <p className="text-sm font-semibold text-slate-900">This product is not registered in the official BIS Trust Ledger.</p>
            <p className="text-xs text-slate-600">
              The identifier <code className="font-mono bg-slate-100 px-1.5 py-0.5 rounded">{publicProductId}</code> does not correspond to an active or historical Bureau of Indian Standards certification record.
            </p>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-bold text-slate-900">Status: NOT_FOUND</p>
              <p className="text-xs text-slate-600 mt-1">Please verify the QR code URL or contact the manufacturer to confirm BIS grant status.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isTampered = result.overall_status === 'INTEGRITY_WARNING' || result.blockchain_integrity === 'MISMATCH';
  const isVerifiedAndCurrent = result.overall_status === 'VERIFIED_AND_CURRENT';
  const isSuspendedOrRevoked = result.overall_status === 'AUTHENTIC_BUT_SUSPENDED' || result.overall_status === 'AUTHENTIC_BUT_REVOKED';
  const isExpired = result.overall_status === 'AUTHENTIC_BUT_EXPIRED';

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white shadow-xl overflow-hidden">
        {/* Verification Status Header Banner */}
        <div
          className={`px-6 py-5 border-b ${
            isTampered
              ? 'bg-rose-500 text-white border-rose-600'
              : isVerifiedAndCurrent
              ? 'bg-emerald-600 text-white border-emerald-700'
              : isSuspendedOrRevoked
              ? 'bg-amber-600 text-white border-amber-700'
              : 'bg-slate-800 text-white border-slate-900'
          }`}
        >
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl flex items-center justify-center bg-white/20 backdrop-blur-sm text-white shadow-sm">
                {isTampered ? (
                  <ShieldAlert className="w-6 h-6 animate-pulse text-white" />
                ) : isVerifiedAndCurrent ? (
                  <CheckCircle2 className="w-6 h-6 text-white" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-white" />
                )}
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-white/80 font-semibold">
                  BIS Public Verification
                </p>
                <h1 className="text-xl md:text-2xl font-black">
                  {isTampered
                    ? 'INTEGRITY WARNING — TAMPERING DETECTED'
                    : isVerifiedAndCurrent
                    ? 'AUTHENTIC & CURRENT BIS CERTIFICATE'
                    : isSuspendedOrRevoked
                    ? 'AUTHENTIC BUT SUSPENDED / REVOKED'
                    : isExpired
                    ? 'AUTHENTIC RECORD BUT EXPIRED'
                    : result.overall_status}
                </h1>
              </div>
            </div>

            <span className="px-3 py-1 rounded-full text-xs font-black uppercase bg-white text-slate-900 shadow-sm">
              {result.overall_status}
            </span>
          </div>
        </div>

        {/* Warning Alert if Tampering Detected */}
        {isTampered && (
          <div className="p-4 bg-rose-50 border-b border-rose-200 text-rose-900 text-xs flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-bold text-sm text-rose-950">CRITICAL TAMPERING ALERT</p>
              <p className="leading-relaxed">
                The current product attributes in the database produce a SHA-256 canonical hash that does NOT match the immutable hash permanently anchored on the blockchain. Data has been altered post-issuance.
              </p>
            </div>
          </div>
        )}

        <div className="p-6 sm:p-8 space-y-6">
          {/* Top Product & QR Card */}
          <div className="grid md:grid-cols-2 gap-6 bg-slate-50/70 p-6 rounded-2xl border border-slate-200">
            <div className="space-y-3">
              <span className="text-[11px] uppercase tracking-[0.2em] text-slate-400 font-bold block">
                Certified Article Details
              </span>
              <div className="flex items-start gap-4">
                {result.record.qr_code_data_url && (
                  <img
                    src={result.record.qr_code_data_url}
                    alt={`${result.record.public_product_id} QR`}
                    className="w-24 h-24 rounded-xl border border-slate-200 bg-white p-2 flex-shrink-0 shadow-xs"
                  />
                )}
                <div>
                  <h2 className="text-lg font-extrabold text-slate-900">{result.record.product_name}</h2>
                  <p className="text-xs text-slate-600 mt-0.5">Model: <strong>{result.record.model || 'Standard Model'}</strong></p>
                  <p className="text-xs text-slate-600">Manufacturer: <strong>{result.record.manufacturer}</strong></p>
                  <p className="text-xs text-brand-700 font-bold mt-1">Standard: {result.record.standard_id}</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <span className="text-[11px] uppercase tracking-[0.2em] text-slate-400 font-bold block">
                Licence & Validity
              </span>
              <div className="space-y-1.5 text-xs text-slate-700">
                <p>Certificate ID: <strong className="font-mono text-slate-900">{result.record.certificate_id}</strong></p>
                <p>Status: <span className={`px-2 py-0.5 rounded font-bold uppercase ${isVerifiedAndCurrent ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{result.certification_status}</span></p>
                <p>Issued At: <strong>{result.record.issued_at ? new Date(result.record.issued_at).toLocaleDateString() : 'N/A'}</strong></p>
                <p>Valid Until: <strong>{result.record.valid_until ? new Date(result.record.valid_until).toLocaleDateString() : 'N/A'}</strong></p>
                <p>Issuing Authority: <strong>{result.record.issuer || 'Bureau of Indian Standards'}</strong></p>
              </div>
            </div>
          </div>

          {/* Cryptographic Proof & Blockchain Ledger Card */}
          <div className="grid md:grid-cols-2 gap-5">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3 shadow-2xs">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                  On-Chain Cryptographic Anchor
                </h3>
              </div>

              <div className="text-xs space-y-2 text-slate-600">
                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Canonical SHA-256 Hash</span>
                  <span className="font-mono text-[11px] bg-slate-50 p-1.5 rounded border border-slate-100 block break-all font-semibold text-slate-800">
                    {result.record.record_hash}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Blockchain Network</span>
                  <span className="font-semibold text-slate-800">{result.record.blockchain_network}</span>
                </div>

                {result.record.transaction_hash && (
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Transaction Hash</span>
                    <span className="font-mono text-[11px] text-brand-700 break-all">{result.record.transaction_hash}</span>
                  </div>
                )}

                {result.record.block_number && (
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Block Number</span>
                    <span className="font-mono font-bold text-slate-800">#{result.record.block_number}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3 shadow-2xs">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-brand-600" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                  IPFS Decentralized Storage
                </h3>
              </div>

              <div className="text-xs space-y-2 text-slate-600">
                {result.record.ipfs_cid ? (
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">IPFS Content Identifier (CIDv1)</span>
                    <span className="font-mono text-[11px] bg-slate-50 p-1.5 rounded border border-slate-100 block break-all font-semibold text-brand-800">
                      {result.record.ipfs_cid}
                    </span>
                    <p className="text-[11px] text-slate-500 mt-1.5">
                      Technical file and laboratory evidence permanently addressed via decentralized content-addressed storage.
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">No external IPFS CID associated with this certificate record.</p>
                )}

                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Verification Timestamp</span>
                  <span className="text-xs text-slate-700 font-medium">
                    {new Date(result.verified_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Verification Explanatory Notes */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5 text-slate-600">
            <div className="flex items-center gap-2 font-bold text-slate-800">
              <Layers className="w-4 h-4 text-brand-600" />
              <span>Cryptographic Verification Audit Notes:</span>
            </div>
            <ul className="list-disc pl-5 space-y-1">
              {result.messages.map((msg, i) => (
                <li key={i}>{msg}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
