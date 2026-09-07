from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractedParameterItem(BaseModel):
    id: Optional[str] = None
    parameter_key: str
    name: str
    value: str
    unit: Optional[str] = ""
    source_page: Optional[int] = None
    source_snippet: Optional[str] = None
    confidence: str = "HIGH"
    is_user_verified: Optional[bool] = False
    is_user_modified: Optional[bool] = False
    original_value: Optional[str] = None
    modified_value: Optional[str] = None
    modified_by: Optional[str] = None
    modified_at: Optional[str] = None


class ParameterPatchRequest(BaseModel):
    value: Optional[str] = None
    unit: Optional[str] = None
    name: Optional[str] = None
    is_user_verified: Optional[bool] = None


class ParameterExtractResponse(BaseModel):
    parameters: List[ExtractedParameterItem]
    missing_information: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ParametersUpdateRequest(BaseModel):
    parameters: List[ExtractedParameterItem]


class StandardCandidateResponse(BaseModel):
    standard_id: str
    title: str
    version: str
    category: Optional[str] = "General"
    confidence_score: float
    confidence: Optional[float] = None
    match_reason: str
    is_primary: bool
    scope: Optional[str] = None


class StandardSelectRequest(BaseModel):
    standard_id: str



class ComplianceGapItem(BaseModel):
    id: str
    title: str
    parameter: str
    currentValue: str
    referenceRequirement: str
    status: str = "Needs attention"  # Needs attention, Missing, Review required, Resolved
    priority: str = "HIGH PRIORITY"  # HIGH PRIORITY, MEDIUM PRIORITY, REVIEW
    recommendation: str
    detailedGuidance: Optional[str] = None
    actionButtonText: str = "View Remediation Guide"
    actionType: str = "guidance"
    isResolved: Optional[bool] = False


class ComplianceResultItem(BaseModel):
    id: str
    standard_id: str
    clause: str
    parameter_name: str
    requirement_text: str
    product_evidence: str
    product_source: Optional[str] = "Uploaded Technical File"
    bis_source: Optional[str] = "BIS Standard Repository"
    status: str  # PASS, FAIL, INSUFFICIENT_INFORMATION, NOT_APPLICABLE
    reasoning: str
    recommendation: Optional[str] = None
    is_deterministic: bool = True


class CostBreakdown(BaseModel):
    testingFees: int = 42000
    bisRelatedFees: int = 15500
    documentationFees: int = 8000
    totalFees: int = 65500
    isOfficial: bool = False
    disclaimer: str = (
        "Statutory BIS fees (Application & Annual License) follow Gazette Notifications. "
        "Laboratory testing charges vary across NABL/BIS-recognized laboratories."
    )


class TimelinePhase(BaseModel):
    phase: str
    duration: str
    description: str


class TimelineEstimate(BaseModel):
    range: str = "4 – 6 Weeks"
    disclaimer: str = (
        "Estimates depend on sample queueing at accredited laboratories and promptness of audit scheduling."
    )
    phases: List[TimelinePhase] = Field(
        default_factory=lambda: [
            TimelinePhase(
                phase="Stage 1: Documentation & Technical File",
                duration="3–5 Days",
                description="Form IV dossier, test protocols, calibration records compilation.",
            ),
            TimelinePhase(
                phase="Stage 2: Independent Lab Testing",
                duration="15–20 Days",
                description="Physical sample verification and safety parameter testing at recognized lab.",
            ),
            TimelinePhase(
                phase="Stage 3: Factory Inspection & Audit",
                duration="5–7 Days",
                description="On-site scrutiny by BIS inspecting officers (Scheme I).",
            ),
            TimelinePhase(
                phase="Stage 4: License Grant & Anchoring",
                duration="3–5 Days",
                description="Scrutiny clearance, Standard Mark license issuance.",
            ),
        ]
    )


class ReadinessDetail(BaseModel):
    score: Optional[float] = None
    score_display: str
    label: str
    status_text: str
    status_type: str
    assessment_state: str
    passed_count: int
    failed_count: int
    insufficient_count: int
    conflict_count: int
    total_count: int


class IdentifiedStandardInfo(BaseModel):
    standard_id: str
    title: str
    version: Optional[str] = None
    source: Optional[str] = "Bureau of Indian Standards"
    applicability: Optional[str] = None
    confidence: Optional[float] = 0.95
    reasoning: Optional[str] = None


class AssessmentResultResponse(BaseModel):
    id: str
    productId: str
    productName: str
    category: str
    manufacturingLocation: str
    modelNumber: Optional[str] = None
    manufacturer: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    parameters: List[ExtractedParameterItem] = Field(default_factory=list)
    referenceStandard: str
    standardTitle: str
    standard: Optional[IdentifiedStandardInfo] = None
    readinessScore: float
    readiness: Optional[ReadinessDetail] = None
    assessment_state: Optional[str] = None
    statusText: str
    statusType: str
    gaps: List[ComplianceGapItem] = Field(default_factory=list)
    complianceResults: List[ComplianceResultItem] = Field(default_factory=list)
    costEstimate: CostBreakdown = Field(default_factory=CostBreakdown)
    timelineEstimate: TimelineEstimate = Field(default_factory=TimelineEstimate)
    assessedAt: str
    isPostRecheck: Optional[bool] = False


class PreparedField(BaseModel):
    label: str
    value: str
    is_complete: bool
    section: str


class RequiredDocument(BaseModel):
    document_name: str
    is_attached: bool
    status: str  # ATTACHED, PENDING, REQUIRED
    description: str


class ApplicationPrepResponse(BaseModel):
    application_id: str
    product_name: str
    category: str
    model_number: str
    manufacturer: str
    manufacturing_location: str
    applicable_standard: str
    standard_title: str
    readiness_score: float
    validation_status: str  # READY_FOR_MANAKONLINE, DEFICIENCIES_DETECTED
    fields: List[PreparedField]
    required_documents: List[RequiredDocument]
    missing_information: List[str] = Field(default_factory=list)
    official_portal_url: str = "https://www.manakonline.in"
    disclaimer: str = (
        "Official submission must be executed directly through the BIS Manakonline portal. "
        "This dossier compiles verified parameters to ensure zero-rejection pre-compliance."
    )


class ChatCitation(BaseModel):
    standard_id: str
    clause: str
    title: str


class ChatQueryRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    citations: List[ChatCitation] = Field(default_factory=list)
    created_at: str
