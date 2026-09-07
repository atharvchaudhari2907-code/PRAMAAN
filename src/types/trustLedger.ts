export type AuthorityStatus = 'ACTIVE' | 'EXPIRED' | 'SUSPENDED' | 'REVOKED' | 'UNKNOWN' | 'NOT_FOUND';
export type BlockchainIntegrity = 'VERIFIED' | 'MISMATCH' | 'NOT_ANCHORED' | 'UNAVAILABLE';
export type BlockchainStatus = 'PENDING' | 'ANCHORING' | 'ANCHOR_FAILED' | 'ANCHORED';

export interface CertificationEvent {
  event_type: string;
  previous_status?: AuthorityStatus;
  new_status?: AuthorityStatus;
  reason?: string;
  record_hash: string;
  transaction_hash?: string;
  issuer: string;
  created_at: string;
}

export interface TrustLedgerRecord {
  id: string;
  public_product_id: string;
  product_name: string;
  manufacturer: string;
  model: string;
  standard_id: string;
  standard_title: string;
  standard_version: string;
  certificate_id: string;
  certification_status: AuthorityStatus;
  valid_until?: string;
  issued_at: string;
  record_hash: string;
  hash_algorithm: string;
  blockchain_network: string;
  contract_address: string;
  transaction_hash?: string;
  block_number?: number;
  blockchain_status: BlockchainStatus;
  anchored_at?: string;
  verification_url: string;
  issuer: string;
  qr_code_data_url?: string;
  ipfs_cid?: string;
  event_history: CertificationEvent[];
  created_at: string;
  updated_at: string;
}

export interface TrustLedgerDashboardStats {
  total_products: number;
  blockchain_anchored: number;
  currently_active: number;
  expired: number;
  suspended: number;
  revoked: number;
  verification_attempts: number;
}

export interface TrustLedgerVerificationResult {
  record: TrustLedgerRecord | null;
  certification_status: AuthorityStatus;
  blockchain_integrity: BlockchainIntegrity;
  overall_status:
    | 'VERIFIED_AND_CURRENT'
    | 'AUTHENTIC_BUT_EXPIRED'
    | 'AUTHENTIC_BUT_SUSPENDED'
    | 'AUTHENTIC_BUT_REVOKED'
    | 'AUTHENTIC_RECORD_CERTIFICATION_EXPIRED'
    | 'INTEGRITY_WARNING'
    | 'NOT_FOUND'
    | 'BLOCKCHAIN_UNAVAILABLE';
  verified_at: string;
  messages: string[];
}
