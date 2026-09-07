/**
 * API client for interacting with the FastAPI backend.
 * Provides live backend connectivity with automatic error handling.
 */

const BASE_URL = (import.meta as any).env?.VITE_API_URL || '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = localStorage.getItem('bis_access_token');
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: any;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }
    const message = (errorData && (errorData.detail || errorData.message || errorData.error)) || `HTTP error ${response.status}`;
    throw new ApiError(response.status, message, errorData);
  }
  return response.json();
}

export const api = {
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${BASE_URL}/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
      return res.ok;
    } catch {
      return false;
    }
  },

  async createApplication(payload: {
    product_name: string;
    category: string;
    model_number?: string;
    manufacturer?: string;
    manufacturing_location: string;
    wattage?: number;
    voltage?: number;
    luminous_efficacy?: number;
  }) {
    const res = await fetch(`${BASE_URL}/applications`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async listApplications() {
    const res = await fetch(`${BASE_URL}/applications`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  async deleteApplication(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async getApplication(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async uploadDocument(id: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/applications/${id}/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: formData,
    });
    return handleResponse<any>(res);
  },

  async extractParameters(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/extract`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async getParameters(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/parameters`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  async patchParameter(id: string, parameterId: string, payload: { value?: string; unit?: string; name?: string; is_user_verified?: boolean }) {
    const res = await fetch(`${BASE_URL}/applications/${id}/parameters/${parameterId}`, {
      method: 'PATCH',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async updateParameters(id: string, parameters: any[]) {
    const res = await fetch(`${BASE_URL}/applications/${id}/parameters`, {
      method: 'PUT',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ parameters }),
    });
    return handleResponse<any>(res);
  },

  async identifyStandards(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/identify-standards`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },


  async selectStandard(id: string, standardId: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/select-standard`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ standard_id: standardId }),
    });
    return handleResponse<any>(res);
  },

  async retrieveRequirements(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/retrieve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async analyzeApplication(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async recheckApplication(id: string, customEfficacy: number = 84) {
    const res = await fetch(`${BASE_URL}/applications/${id}/recheck?custom_efficacy=${customEfficacy}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async prepareApplication(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/prepare-application`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async getTrackingEvents(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/tracking`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async sendChatMessage(id: string, message: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/chat`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ message }),
    });
    return handleResponse<any>(res);
  },

  async listStandards() {
    const res = await fetch(`${BASE_URL}/standards`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async getStandardDetails(standardId: string) {
    const res = await fetch(`${BASE_URL}/standards/${encodeURIComponent(standardId)}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async verifyHash(sha256Hash: string, documentName?: string) {
    const res = await fetch(`${BASE_URL}/verification/verify-hash`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ sha256_hash: sha256Hash, document_name: documentName }),
    });
    return handleResponse<any>(res);
  },

  async listTrustLedgerRecords() {
    const res = await fetch(`${BASE_URL}/trust-ledger/records`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  async createTrustLedgerRecord(payload: {
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
  }) {
    const res = await fetch(`${BASE_URL}/trust-ledger/records`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getTrustLedgerRecord(publicProductId: string) {
    const res = await fetch(`${BASE_URL}/trust-ledger/records/${encodeURIComponent(publicProductId)}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  // Phase 3 Dossier & Certification Workflow Methods
  async getReadinessGate(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/readiness`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<{
      application_id: string;
      readiness_score: number;
      validation_status: string;
      missing_information: string[];
      missing_documents: string[];
      failed_critical_clauses: string[];
      required_actions: string[];
      is_ready: boolean;
    }>(res);
  },

  async getChecklist(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/checklist`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  async verifyChecklistItem(id: string, itemId: string, verified: boolean, notes?: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/checklist/${itemId}/verify`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ verified, verification_notes: notes }),
    });
    return handleResponse<any>(res);
  },

  async getForms(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/forms`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<Record<string, any>>(res);
  },

  async generateDocuments(id: string, documentTypes?: string[]) {
    const res = await fetch(`${BASE_URL}/applications/${id}/documents/generate`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify({ document_types: documentTypes }),
    });
    return handleResponse<any[]>(res);
  },

  async listGeneratedDocuments(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/generated-documents`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  getGeneratedDocumentDownloadUrl(id: string, docId: string): string {
    return `${BASE_URL}/applications/${id}/generated-documents/${docId}/download`;
  },

  getFormDownloadUrl(id: string, formType: string, format: 'pdf' | 'json' = 'pdf'): string {
    return `${BASE_URL}/applications/${id}/forms/${formType}/download?format=${format}`;
  },

  async downloadForm(id: string, formType: string, format: 'pdf' | 'json' = 'pdf'): Promise<void> {
    const res = await fetch(`${BASE_URL}/applications/${id}/forms/${formType}/download?format=${format}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to download form' }));
      throw new Error(err.detail || 'Download failed');
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${formType.toLowerCase()}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  },

  async getSubmissionManifest(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/submission-manifest`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async submitApplication(
    id: string,
    payload: { reference_number: string; portal_url?: string; submitted_by: string; notes?: string }
  ) {
    const res = await fetch(`${BASE_URL}/applications/${id}/submit`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getApplicationEvents(id: string) {
    const res = await fetch(`${BASE_URL}/applications/${id}/events`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any[]>(res);
  },

  async createApplicationEvent(
    id: string,
    payload: { to_status: string; event_type?: string; description?: string; note?: string; source?: string }
  ) {
    const res = await fetch(`${BASE_URL}/applications/${id}/events`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  // Phase 4 Trust Ledger, Blockchain, Voice & Vision Methods
  async publicVerifyCertificate(publicProductId: string) {
    const res = await fetch(`${BASE_URL}/public/verify/${encodeURIComponent(publicProductId)}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async issueCertificate(payload: { application_id: string; document_id?: string; valid_years?: number }) {
    const res = await fetch(`${BASE_URL}/certificates`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getCertificate(id: string) {
    const res = await fetch(`${BASE_URL}/certificates/${encodeURIComponent(id)}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<any>(res);
  },

  async updateCertificateStatus(id: string, payload: { status: string; reason?: string }) {
    const res = await fetch(`${BASE_URL}/certificates/${encodeURIComponent(id)}/status`, {
      method: 'PATCH',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async queryVoiceAssistant(id: string, payload: { language_code: string; query_text?: string; audio_base64?: string }) {
    const res = await fetch(`${BASE_URL}/applications/${encodeURIComponent(id)}/voice/query`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getSupportedLanguages() {
    const res = await fetch(`${BASE_URL}/applications/voice/languages`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });
    return handleResponse<Record<string, string>>(res);
  },

  async analyzeProductImage(id: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/applications/${encodeURIComponent(id)}/vision/analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: formData,
    });
    return handleResponse<any>(res);
  },

  async ingestIoTResult(payload: {
    device_id: string;
    lab_id?: string;
    test_type: string;
    parameter: string;
    value: number;
    unit: string;
    application_id: string;
  }) {
    const res = await fetch(`${BASE_URL}/iot/test-results`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },
};


