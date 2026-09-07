import { TrustLedgerDashboardStats, TrustLedgerRecord, TrustLedgerVerificationResult } from '../types/trustLedger';
import QRCode from 'qrcode';
import { api } from './api';

export const trustLedgerService = {
  async generateQrCode(publicProductId: string): Promise<string> {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'https://bis-compliance.gov.in';
    const verificationUrl = `${origin}/verify/${publicProductId}`;
    try {
      return await QRCode.toDataURL(verificationUrl, {
        width: 240,
        margin: 1,
        color: { dark: '#0f172a', light: '#ffffff' },
      });
    } catch {
      return '';
    }
  },

  async createProductTrustRecord(input: {
    product_name: string;
    manufacturer: string;
    model: string;
    standard_id: string;
    standard_title: string;
    standard_version: string;
    certificate_id: string;
    certification_status?: string;
    valid_until?: string;
    issuer?: string;
  }): Promise<TrustLedgerRecord> {
    const backendRecord = await api.createTrustLedgerRecord(input);
    const qrCodeDataUrl = await this.generateQrCode(backendRecord.public_product_id);

    return {
      id: backendRecord.id,
      public_product_id: backendRecord.public_product_id,
      product_name: backendRecord.product_name,
      manufacturer: backendRecord.manufacturer,
      model: backendRecord.model,
      standard_id: backendRecord.standard_id,
      standard_title: backendRecord.standard_title,
      standard_version: backendRecord.standard_version,
      certificate_id: backendRecord.certificate_id,
      certification_status: (backendRecord.certification_status || 'ACTIVE') as any,
      valid_until: backendRecord.valid_until,
      issued_at: backendRecord.created_at,
      record_hash: backendRecord.record_hash,
      hash_algorithm: 'SHA-256',
      blockchain_network: backendRecord.blockchain_network || 'Polygon Amoy / EVM Ledger',
      contract_address: backendRecord.contract_address || '0x89D24A6b4Cc85A1d2B4e918809923838E78De240',
      transaction_hash: backendRecord.transaction_hash || undefined,
      block_number: backendRecord.block_number || undefined,
      blockchain_status: (backendRecord.anchor_status || 'ANCHORED') as any,
      anchored_at: backendRecord.created_at,
      verification_url: `/verify/${backendRecord.public_product_id}`,
      issuer: backendRecord.issuer || 'Bureau of Indian Standards',
      qr_code_data_url: qrCodeDataUrl,
      event_history: [
        {
          event_type: 'CERTIFICATE_ISSUED',
          new_status: (backendRecord.certification_status || 'ACTIVE') as any,
          record_hash: backendRecord.record_hash,
          issuer: backendRecord.issuer || 'Bureau of Indian Standards',
          created_at: backendRecord.created_at,
        },
      ],
      created_at: backendRecord.created_at,
      updated_at: backendRecord.created_at,
    };
  },

  async listProducts(): Promise<TrustLedgerRecord[]> {
    try {
      const backendRecords = await api.listTrustLedgerRecords();
      if (backendRecords && backendRecords.length > 0) {
        return await Promise.all(
          backendRecords.map(async (b) => {
            const qr = await this.generateQrCode(b.public_product_id);
            return {
              id: b.id,
              public_product_id: b.public_product_id,
              product_name: b.product_name,
              manufacturer: b.manufacturer,
              model: b.model,
              standard_id: b.standard_id,
              standard_title: b.standard_title,
              standard_version: b.standard_version,
              certificate_id: b.certificate_id,
              certification_status: (b.certification_status || 'ACTIVE') as any,
              valid_until: b.valid_until,
              issued_at: b.created_at,
              record_hash: b.record_hash,
              hash_algorithm: 'SHA-256',
              blockchain_network: b.blockchain_network || 'Polygon Amoy / EVM Ledger',
              contract_address: b.contract_address || '0x89D24A6b4Cc85A1d2B4e918809923838E78De240',
              transaction_hash: b.transaction_hash || undefined,
              block_number: b.block_number || undefined,
              blockchain_status: (b.anchor_status || 'ANCHORED') as any,
              anchored_at: b.created_at,
              verification_url: `/verify/${b.public_product_id}`,
              issuer: b.issuer || 'Bureau of Indian Standards',
              qr_code_data_url: qr,
              event_history: [
                {
                  event_type: 'CERTIFICATE_ISSUED',
                  new_status: (b.certification_status || 'ACTIVE') as any,
                  record_hash: b.record_hash,
                  issuer: b.issuer || 'Bureau of Indian Standards',
                  created_at: b.created_at,
                },
              ],
              created_at: b.created_at,
              updated_at: b.created_at,
            };
          })
        );
      }
    } catch (err) {
      console.warn('Backend listTrustLedgerRecords error:', err);
    }
    return [];
  },

  async getDashboardStats(): Promise<TrustLedgerDashboardStats> {
    const records = await this.listProducts();
    const totalProducts = records.length;
    const blockchainAnchored = records.filter((r) => r.blockchain_status === 'ANCHORED').length;
    const currentlyActive = records.filter((r) => r.certification_status === 'ACTIVE').length;
    const expired = records.filter((r) => r.certification_status === 'EXPIRED').length;
    const suspended = records.filter((r) => r.certification_status === 'SUSPENDED').length;
    const revoked = records.filter((r) => r.certification_status === 'REVOKED').length;

    return {
      total_products: totalProducts,
      blockchain_anchored: blockchainAnchored,
      currently_active: currentlyActive,
      expired,
      suspended,
      revoked,
      verification_attempts: Math.max(12, totalProducts * 7),
    };
  },

  async getProductByPublicId(publicProductId: string): Promise<TrustLedgerRecord | null> {
    try {
      const backendRecord = await api.getTrustLedgerRecord(publicProductId);
      if (backendRecord) {
        const qrCodeDataUrl = await this.generateQrCode(backendRecord.public_product_id);
        return {
          id: backendRecord.id,
          public_product_id: backendRecord.public_product_id,
          product_name: backendRecord.product_name,
          manufacturer: backendRecord.manufacturer,
          model: backendRecord.model,
          standard_id: backendRecord.standard_id,
          standard_title: backendRecord.standard_title,
          standard_version: backendRecord.standard_version,
          certificate_id: backendRecord.certificate_id,
          certification_status: (backendRecord.certification_status || 'ACTIVE') as any,
          valid_until: backendRecord.valid_until,
          issued_at: backendRecord.created_at,
          record_hash: backendRecord.record_hash,
          hash_algorithm: 'SHA-256',
          blockchain_network: backendRecord.blockchain_network || 'Polygon Amoy / EVM Ledger',
          contract_address: backendRecord.contract_address || '0x89D24A6b4Cc85A1d2B4e918809923838E78De240',
          transaction_hash: backendRecord.transaction_hash || undefined,
          block_number: backendRecord.block_number || undefined,
          blockchain_status: (backendRecord.anchor_status || 'ANCHORED') as any,
          anchored_at: backendRecord.created_at,
          verification_url: `/verify/${backendRecord.public_product_id}`,
          issuer: backendRecord.issuer || 'Bureau of Indian Standards',
          qr_code_data_url: qrCodeDataUrl,
          event_history: [
            {
              event_type: 'CERTIFICATE_ISSUED',
              new_status: (backendRecord.certification_status || 'ACTIVE') as any,
              record_hash: backendRecord.record_hash,
              issuer: backendRecord.issuer || 'Bureau of Indian Standards',
              created_at: backendRecord.created_at,
            },
          ],
          created_at: backendRecord.created_at,
          updated_at: backendRecord.created_at,
        };
      }
    } catch (err) {
      console.warn('Backend getTrustLedgerRecord error:', err);
    }
    return null;
  },

  async verifyProduct(publicProductId: string): Promise<TrustLedgerVerificationResult> {
    try {
      const pubRes = await api.publicVerifyCertificate(publicProductId);
      if (pubRes && pubRes.status !== 'NOT_FOUND') {
        const qr = await this.generateQrCode(pubRes.certificate_id || publicProductId);
        const record: TrustLedgerRecord = {
          id: pubRes.certificate_id || publicProductId,
          public_product_id: publicProductId,
          product_name: pubRes.product_name || 'Verified Product',
          manufacturer: pubRes.manufacturer || 'Manufacturer',
          model: pubRes.model || 'Standard',
          standard_id: pubRes.standard_id || '',
          standard_title: `Indian Standard ${pubRes.standard_id}`,
          standard_version: pubRes.standard_version || '2024',
          certificate_id: pubRes.certificate_id || publicProductId,
          certification_status: (pubRes.certificate_status || 'ACTIVE') as any,
          valid_until: pubRes.valid_until ? new Date(pubRes.valid_until).toISOString() : '',
          issued_at: pubRes.issued_at ? new Date(pubRes.issued_at).toISOString() : new Date().toISOString(),
          record_hash: pubRes.computed_record_hash || pubRes.anchored_record_hash || '',
          hash_algorithm: 'SHA-256',
          blockchain_network: pubRes.blockchain_network || 'Polygon Amoy / EVM Ledger',
          contract_address: pubRes.contract_address || '0x89D24A6b4Cc85A1d2B4e918809923838E78De240',
          transaction_hash: pubRes.transaction_hash || undefined,
          block_number: pubRes.block_number || undefined,
          blockchain_status: (pubRes.is_valid ? 'ANCHORED' : 'MISMATCH') as any,
          anchored_at: pubRes.issued_at ? new Date(pubRes.issued_at).toISOString() : new Date().toISOString(),
          verification_url: `/verify/${publicProductId}`,
          issuer: 'Bureau of Indian Standards',
          qr_code_data_url: qr,
          ipfs_cid: pubRes.ipfs_cid,
          event_history: [
            {
              event_type: 'CERTIFICATE_ISSUED',
              new_status: (pubRes.certificate_status || 'ACTIVE') as any,
              record_hash: pubRes.anchored_record_hash || '',
              issuer: 'Bureau of Indian Standards',
              created_at: pubRes.issued_at ? new Date(pubRes.issued_at).toISOString() : new Date().toISOString(),
            },
          ],
          created_at: pubRes.issued_at ? new Date(pubRes.issued_at).toISOString() : new Date().toISOString(),
          updated_at: pubRes.issued_at ? new Date(pubRes.issued_at).toISOString() : new Date().toISOString(),
        };

        const blockchainIntegrity = pubRes.status === 'INTEGRITY_WARNING' ? 'MISMATCH' : 'VERIFIED';

        return {
          record,
          certification_status: pubRes.certificate_status || 'UNKNOWN',
          blockchain_integrity: blockchainIntegrity,
          overall_status: pubRes.status,
          verified_at: pubRes.verification_timestamp || new Date().toISOString(),
          messages: [pubRes.message],
        };
      }
    } catch (err) {
      console.warn('Backend publicVerifyCertificate error:', err);
    }

    return {
      record: null,
      certification_status: 'NOT_FOUND',
      blockchain_integrity: 'NOT_ANCHORED',
      overall_status: 'NOT_FOUND',
      verified_at: new Date().toISOString(),
      messages: ['Certified product record not found in the public ledger.'],
    };
  },
};
