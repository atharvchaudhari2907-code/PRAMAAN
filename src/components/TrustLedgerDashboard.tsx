import React, { useEffect, useState } from 'react';
import { trustLedgerService } from '../services/trustLedgerService';
import { TrustLedgerDashboardStats, TrustLedgerRecord } from '../types/trustLedger';
import { ArrowRight, CheckCircle2, Hash, ShieldCheck, TriangleAlert, FileText } from 'lucide-react';

interface TrustLedgerDashboardProps {
  onViewProduct: (publicId: string) => void;
}

export const TrustLedgerDashboard: React.FC<TrustLedgerDashboardProps> = ({ onViewProduct }) => {
  const [stats, setStats] = useState<TrustLedgerDashboardStats | null>(null);
  const [records, setRecords] = useState<TrustLedgerRecord[]>([]);

  const handlePrintQr = (record: TrustLedgerRecord) => {
    const printWindow = window.open('', '_blank', 'width=520,height=720');
    if (!printWindow) {
      return;
    }

    const qrHtml = record.qr_code_data_url
      ? `<img src="${record.qr_code_data_url}" alt="QR code" style="width: 180px; height: 180px; display:block; margin: 0 auto 16px; background: white; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0;" />`
      : '<div style="padding: 24px; text-align: center; color: #64748b;">QR unavailable</div>';

    const body = `
      <html>
        <head>
          <title>${record.public_product_id} QR Label</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }
            .card { max-width: 420px; margin: 24px auto; background: white; border: 1px solid #e2e8f0; border-radius: 18px; padding: 24px; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08); }
            .title { font-size: 18px; font-weight: 700; text-align: center; margin-bottom: 8px; }
            .sub { text-align: center; font-size: 12px; color: #64748b; margin-bottom: 18px; }
            .meta { font-size: 11px; color: #334155; line-height: 1.8; text-align: center; }
            .status { display: inline-block; font-size: 11px; font-weight: 700; padding: 6px 10px; border-radius: 999px; background: ${record.certification_status === 'ACTIVE' ? '#dcfce7' : '#fef3c7'}; color: ${record.certification_status === 'ACTIVE' ? '#166534' : '#92400e'}; margin-top: 12px; }
            @media print { body { background: white; } .card { box-shadow: none; border: none; margin: 0 auto; } }
          </style>
        </head>
        <body>
          <div class="card">
            <div class="title">${record.product_name}</div>
            <div class="sub">BIS Trust Ledger / Product Verification</div>
            ${qrHtml}
            <div class="meta">
              <div><strong>Public ID:</strong> ${record.public_product_id}</div>
              <div><strong>Manufacturer:</strong> ${record.manufacturer}</div>
              <div><strong>Certificate:</strong> ${record.certificate_id}</div>
              <div><strong>Standard:</strong> ${record.standard_id}</div>
              <div class="status">${record.certification_status}</div>
            </div>
          </div>
        </body>
      </html>
    `;

    printWindow.document.write(body);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 250);
  };

  useEffect(() => {
    const load = async () => {
      const [dashboardStats, products] = await Promise.all([
        trustLedgerService.getDashboardStats(),
        trustLedgerService.listProducts(),
      ]);
      setStats(dashboardStats);
      setRecords(products);
    };
    load();
  }, []);

  if (!stats) {
    return <div className="p-8 text-xs text-slate-500">Loading Trust Ledger…</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">BIS Trust Ledger</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">Tamper-evident certification provenance and public verification</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-4">
        {[{label:'Total Products',value:stats.total_products,icon:FileText,color:'bg-slate-100 text-slate-700'},{label:'Blockchain Anchored',value:stats.blockchain_anchored,icon:Hash,color:'bg-indigo-100 text-indigo-700'},{label:'Currently Active',value:stats.currently_active,icon:CheckCircle2,color:'bg-emerald-100 text-emerald-700'},{label:'Expired',value:stats.expired,icon:TriangleAlert,color:'bg-amber-100 text-amber-700'},{label:'Suspended',value:stats.suspended,icon:TriangleAlert,color:'bg-orange-100 text-orange-700'},{label:'Revoked',value:stats.revoked,icon:TriangleAlert,color:'bg-rose-100 text-rose-700'}].map((item) => (
          <div key={item.label} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${item.color}`}>
              <item.icon className="w-4 h-4" />
            </div>
            <p className="text-2xl font-extrabold text-slate-900 mt-4">{item.value}</p>
            <p className="text-[11px] text-slate-500 mt-1">{item.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">Registered Product Records</h2>
          <p className="text-[11px] text-slate-500">{records.length} records</p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-3 font-semibold">Product</th>
                <th className="px-5 py-3 font-semibold">Manufacturer</th>
                <th className="px-5 py-3 font-semibold">Standard</th>
                <th className="px-5 py-3 font-semibold">Certificate</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Blockchain</th>
                <th className="px-5 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id} className="border-t border-slate-100 hover:bg-slate-50/60">
                  <td className="px-5 py-3 font-semibold text-slate-900">
                    <div className="flex items-center gap-3">
                      {record.qr_code_data_url ? (
                        <img src={record.qr_code_data_url} alt={`${record.public_product_id} QR`} className="w-10 h-10 rounded-md border border-slate-200 bg-white p-1" />
                      ) : (
                        <div className="w-10 h-10 rounded-md border border-slate-200 bg-slate-50 flex items-center justify-center text-[9px] font-bold text-slate-500">QR</div>
                      )}
                      <div>
                        <div>{record.product_name}</div>
                        <div className="text-[10px] text-slate-500">{record.public_product_id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{record.manufacturer}</td>
                  <td className="px-5 py-3 text-slate-600">{record.standard_id}</td>
                  <td className="px-5 py-3 text-slate-600">{record.certificate_id}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-1 rounded-full text-[10px] font-bold ${record.certification_status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                      {record.certification_status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{record.blockchain_status === 'ANCHORED' ? 'Verified' : 'Pending'}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => onViewProduct(record.public_product_id)} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700 transition-colors">
                        Verify <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handlePrintQr(record)} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 font-semibold hover:bg-slate-50 transition-colors">
                        Print QR
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
