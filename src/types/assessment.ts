export interface ExtractedParameter {
  id?: string;
  parameter_key: string;
  name: string;
  value: string;
  unit?: string;
  source_page?: number | null;
  source_snippet?: string | null;
  confidence: string; // HIGH, MEDIUM, LOW, USER_ENTERED
  is_user_modified?: boolean;
}

export interface StandardCandidate {
  standard_id: string;
  title: string;
  version: string;
  category: string;
  confidence_score: number;
  match_reason: string;
  is_primary: boolean;
  scope?: string;
}

export interface ProductFormData {
  category: string;
  name: string;
  modelNumber?: string;
  manufacturer?: string;
  manufacturingLocation: string;
  additionalNotes?: string;
  specifications?: Record<string, any>;
  datasheetFile: {
    name: string;
    size: number;
    uploadedAt: string;
    rawFile?: File;
  } | null;
}

export type GapStatus = 'Needs attention' | 'Missing' | 'Review required' | 'Resolved';
export type GapPriority = 'HIGH PRIORITY' | 'MEDIUM PRIORITY' | 'REVIEW';

export interface ComplianceGap {
  id: string;
  title: string;
  parameter: string;
  currentValue: string;
  referenceRequirement: string;
  status: GapStatus;
  priority: GapPriority;
  recommendation: string;
  detailedGuidance?: string;
  actionButtonText: string;
  actionType: 'guidance' | 'upload_test_data' | 'review_packaging' | 'evidence';
  isResolved?: boolean;
}

export interface ComplianceResultItem {
  id: string;
  standard_id: string;
  clause: string;
  parameter_name: string;
  requirement_text: string;
  product_evidence: string;
  product_source?: string;
  bis_source?: string;
  status: 'PASS' | 'FAIL' | 'INSUFFICIENT_INFORMATION' | 'NOT_APPLICABLE';
  reasoning: string;
  recommendation?: string;
  is_deterministic?: boolean;
}

export interface CostBreakdown {
  testingFees: number;
  bisRelatedFees: number;
  documentationFees: number;
  totalFees: number;
  isOfficial?: boolean;
  disclaimer: string;
}

export interface TimelineEstimate {
  range: string;
  disclaimer: string;
  phases: {
    phase: string;
    duration: string;
    description: string;
  }[];
}

export interface PreparedField {
  label: string;
  value: string;
  is_complete: boolean;
  section: string;
}

export interface RequiredDocument {
  document_name: string;
  is_attached: boolean;
  status: 'ATTACHED' | 'PENDING' | 'REQUIRED';
  description: string;
}

export interface ApplicationPreparationData {
  application_id: string;
  product_name: string;
  category: string;
  model_number: string;
  manufacturer: string;
  manufacturing_location: string;
  applicable_standard: string;
  standard_title: string;
  readiness_score: number;
  validation_status: 'READY_FOR_MANAKONLINE' | 'DEFICIENCIES_DETECTED';
  fields: PreparedField[];
  required_documents: RequiredDocument[];
  missing_information: string[];
  official_portal_url: string;
  disclaimer: string;
}

export interface TrackingEvent {
  id: string;
  stage: string;
  title: string;
  description?: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING';
  timestamp: string;
  is_simulated: boolean;
}

export interface ChatCitation {
  standard_id: string;
  clause: string;
  title: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: ChatCitation[];
  created_at: string;
}

export interface VerificationResult {
  sha256_hash: string;
  is_verified: boolean;
  matched_application_id?: string | null;
  matched_document_name?: string | null;
  timestamp?: string;
  integrity_status: 'VALID_RECORD' | 'TAMPER_EVIDENT_MISMATCH' | 'UNKNOWN_RECORD';
  blockchain_network: string;
  message: string;
}

export interface IdentifiedStandard {
  standard_id: string;
  title: string;
  version?: string;
  source?: string;
  applicability?: string;
  confidence?: number;
  reasoning?: string;
}

export interface ReadinessDetail {
  score: number | null;
  score_display: string;
  label: string;
  status_text: string;
  status_type: 'success' | 'warning' | 'danger' | 'neutral';
  assessment_state: string;
  passed_count: number;
  failed_count: number;
  insufficient_count: number;
  conflict_count: number;
  total_count: number;
}

export interface AssessmentResult {
  id: string;
  productId: string;
  productName: string;
  category: string;
  manufacturingLocation: string;
  modelNumber?: string;
  manufacturer?: string;
  specifications: Record<string, any>;
  parameters?: ExtractedParameter[];
  referenceStandard: string;
  standardTitle: string;
  standard?: IdentifiedStandard;
  readinessScore: number;
  readiness?: ReadinessDetail;
  assessment_state?: string;
  statusText: string;
  statusType: 'warning' | 'success' | 'danger' | 'neutral';
  gaps: ComplianceGap[];
  complianceResults?: ComplianceResultItem[];
  costEstimate: CostBreakdown;
  timelineEstimate: TimelineEstimate;
  assessedAt: string;
  isPostRecheck?: boolean;
}
