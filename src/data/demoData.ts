import { AssessmentResult, ProductFormData, ExtractedParameter, ComplianceGap } from '../types/assessment';

export const EMPTY_PRODUCT_FORM: ProductFormData = {
  category: '',
  name: '',
  modelNumber: '',
  manufacturer: '',
  manufacturingLocation: '',
  additionalNotes: '',
  datasheetFile: null,
};

export const PRODUCT_PRESETS = [
  {
    id: 'electric-iron',
    label: 'Household Appliance — Electric Steam Iron (IS 302-2-3)',
    category: 'Household Electrical Appliances',
    data: {
      category: 'Household Electrical Appliances',
      name: 'Electric Steam Iron 1200W',
      modelNumber: 'ESI-1200X',
      manufacturer: 'Bajaj Electricals Ltd.',
      manufacturingLocation: 'Ahmedabad, Gujarat',
      additionalNotes: 'Non-stick soleplate, 1200W rated input, Class I earthed appliance',
      datasheetFile: null,
    },
  },
  {
    id: 'pressure-cooker',
    label: 'Kitchenware — Domestic Pressure Cooker 5L (IS 2347)',
    category: 'Kitchen & Pressure Cookers',
    data: {
      category: 'Kitchen & Pressure Cookers',
      name: 'Stainless Steel Pressure Cooker 5 Litre',
      modelNumber: 'PC-SS-5L',
      manufacturer: 'Prestige Consumer Products',
      manufacturingLocation: 'Hosur, Tamil Nadu',
      additionalNotes: 'Grade 304 stainless steel body, gasket release system, nominal pressure 1.0 kgf/cm²',
      datasheetFile: null,
    },
  },
  {
    id: 'ceiling-fan',
    label: 'Electrical Appliance — 1200mm Ceiling Fan (IS 374)',
    category: 'Household Electrical Appliances',
    data: {
      category: 'Household Electrical Appliances',
      name: 'High-Speed 1200mm Ceiling Fan',
      modelNumber: 'CF-1200-HS',
      manufacturer: 'Havells India Ltd.',
      manufacturingLocation: 'Haridwar, Uttarakhand',
      additionalNotes: '50W rated input, 215 m³/min air delivery, service value 4.3 m³/min/W',
      datasheetFile: null,
    },
  },
  {
    id: 'led-bulb',
    label: 'Lighting — 9W Self-Ballasted LED Lamp (IS 16102)',
    category: 'Lighting & Luminaires',
    data: {
      category: 'Lighting & Luminaires',
      name: '9W Self-Ballasted LED Bulb',
      modelNumber: 'LED-9W-B22',
      manufacturer: 'Nova Lighting Systems',
      manufacturingLocation: 'Pune, Maharashtra',
      additionalNotes: 'B22 cap, 230V AC, 78 lm/W efficacy, 6500K CCT',
      datasheetFile: null,
    },
  },
];

export const DEFAULT_DEMO_PRODUCT: ProductFormData = { ...EMPTY_PRODUCT_FORM };

export function generateDynamicAssessmentResult(
  productData: ProductFormData,
  selectedStandardId?: string,
  parameters: ExtractedParameter[] = []
): AssessmentResult {
  const prodName = productData.name || 'Manufactured Product';
  const prodCat = productData.category || 'General Equipment';
  const nameLower = prodName.toLowerCase();
  const catLower = prodCat.toLowerCase();

  let standardId = selectedStandardId || 'IS 302 (Part 1)';
  let standardTitle = 'Indian Standard for Safety & Performance Requirements';
  let readinessScore = 88;
  let gaps: AssessmentResult['gaps'] = [];

  if (catLower.includes('cooker') || nameLower.includes('cooker')) {
    standardId = selectedStandardId || 'IS 2347 : 2017';
    standardTitle = 'Domestic Pressure Cookers — Specification (Fifth Revision)';
    readinessScore = 85;
    gaps = [
      {
        id: 'GAP-01',
        title: 'Gap 01 — Hydraulic Proof Pressure Test Certificate',
        parameter: 'Hydraulic Proof Pressure (Clause 6.3)',
        currentValue: 'Missing in submitted datasheet',
        referenceRequirement: '≥ 2.0 kgf/cm² (196 kPa) proof test without permanent deformation',
        status: 'Needs attention',
        priority: 'HIGH PRIORITY',
        recommendation: 'Provide hydrostatic pressure test log up to 2.0 kgf/cm².',
        detailedGuidance: 'IS 2347 Clause 6.3 requires that the cooker body and lid assembly withstand hydraulic proof pressure of not less than 2.0 kgf/cm² for 2 minutes without leakage. Recommendation: Attach NABL/in-house hydrostatic test pressure chart.',
        actionButtonText: 'View Guidance',
        actionType: 'guidance',
        isResolved: false,
      },
      {
        id: 'GAP-02',
        title: 'Gap 02 — Mandatory Bilingual Markings',
        parameter: 'Bilingual Safety Markings (Clause 9.2)',
        currentValue: 'Lacks Hindi operating instructions on outer carton',
        referenceRequirement: 'Clause 9.2: Nominal capacity, max pressure, ISI Standard Mark in English & Hindi',
        status: 'Review required',
        priority: 'REVIEW',
        recommendation: 'Update packaging artwork with bilingual markings.',
        detailedGuidance: 'Clause 9.2 specifies that instructions for operating safety, nominal capacity (L), and ISI Standard Mark placement must be printed in both Hindi and English.',
        actionButtonText: 'Review Packaging',
        actionType: 'review_packaging',
        isResolved: false,
      },
    ];
  } else if (nameLower.includes('iron') || nameLower.includes('steamer')) {
    standardId = selectedStandardId || 'IS 302 (Part 2/Sec 3) : 2007';
    standardTitle = 'Safety of Household Electrical Appliances — Particular Requirements for Electric Irons';
    readinessScore = 90;
    gaps = [
      {
        id: 'GAP-01',
        title: 'Gap 01 — Leakage Current & Thermal Cutout Test',
        parameter: 'Operating Leakage Current (Clause 13.2)',
        currentValue: '0.65 mA (pending high-humidity chamber test)',
        referenceRequirement: '≤ 0.75 mA for Class I appliances under 95% RH test',
        status: 'Needs attention',
        priority: 'MEDIUM PRIORITY',
        recommendation: 'Conduct high-humidity chamber leakage test.',
        detailedGuidance: 'IS 302-2-3 Clause 13.2 requires leakage current measurement immediately following moisture resistance pre-conditioning at 93-97% relative humidity.',
        actionButtonText: 'View Guidance',
        actionType: 'guidance',
        isResolved: false,
      },
    ];
  } else if (catLower.includes('fan') || nameLower.includes('fan')) {
    standardId = selectedStandardId || 'IS 374 : 2019';
    standardTitle = 'Electric Ceiling Type Fans and Regulators — Specification';
    readinessScore = 92;
    gaps = [
      {
        id: 'GAP-01',
        title: 'Gap 01 — Suspension Safety Wire 4x Load Test',
        parameter: 'Mechanical Suspension Test (Clause 14.3)',
        currentValue: 'Secondary safety wire fitted (Load test cert pending)',
        referenceRequirement: 'Clause 14.3: Withstand 4x total fan weight without failure',
        status: 'Review required',
        priority: 'REVIEW',
        recommendation: 'Attach tensile load certificate for the safety wire rope.',
        detailedGuidance: 'IS 374 mandates a secondary safety wire rope anchored to the building structure capable of holding 4x the total weight of the fan assembly.',
        actionButtonText: 'Upload Test Data',
        actionType: 'upload_test_data',
        isResolved: false,
      },
    ];
  } else if (catLower.includes('light') || nameLower.includes('lamp') || nameLower.includes('bulb')) {
    standardId = selectedStandardId || 'IS 16102 (Part 1) : 2012';
    standardTitle = 'Self-Ballasted LED Lamps for General Lighting Services — Safety Requirements';
    readinessScore = 87;
    gaps = [
      {
        id: 'GAP-01',
        title: 'Gap 01 — Luminous Efficacy Threshold',
        parameter: 'Luminous Efficacy',
        currentValue: '78 lm/W',
        referenceRequirement: '≥ 80 lm/W for general lighting (IS 14785)',
        status: 'Needs attention',
        priority: 'HIGH PRIORITY',
        recommendation: 'Optimize driver efficiency or upgrade LED chip package.',
        detailedGuidance: 'IS 14785 threshold for 9W self-ballasted lamps is 80 lm/W. Recommendation: Upgrade driver efficiency or switch to higher-bin SMD2835 LEDs.',
        actionButtonText: 'View Guidance',
        actionType: 'guidance',
        isResolved: false,
      },
      {
        id: 'GAP-02',
        title: 'Gap 02 — Thermal Junction Temperature Test',
        parameter: 'Thermal Stability (Clause 12)',
        currentValue: 'Missing in submitted datasheet',
        referenceRequirement: 'Thermal stability logs at 25°C & 45°C ambient',
        status: 'Missing',
        priority: 'MEDIUM PRIORITY',
        recommendation: 'Provide thermocouple probe test reports.',
        detailedGuidance: 'Attach preliminary heat sink stabilization logs and junction temperature measurement reports.',
        actionButtonText: 'Upload Test Data',
        actionType: 'upload_test_data',
        isResolved: false,
      },
    ];
  } else {
    standardId = selectedStandardId || 'IS 13252 (Part 1) : 2010';
    standardTitle = 'Information Technology Equipment — Safety — General Requirements';
    readinessScore = 86;
    gaps = [
      {
        id: 'GAP-01',
        title: 'Gap 01 — Bilingual Standard Label & Markings',
        parameter: 'Clause 1.7: Marking and Instructions',
        currentValue: 'Marking artwork pending BIS standard mark inclusion',
        referenceRequirement: 'Clause 1.7: Rated input, model no., trade mark, bilingual warnings',
        status: 'Review required',
        priority: 'REVIEW',
        recommendation: 'Finalize marking artwork with bilingual instructions.',
        detailedGuidance: 'Ensure rating plate displays voltage, current, manufacturer trade name, and Standard Mark.',
        actionButtonText: 'Review Packaging',
        actionType: 'review_packaging',
        isResolved: false,
      },
    ];
  }

  const specs: Record<string, any> = {};
  parameters.forEach((p) => {
    specs[p.parameter_key] = p.value + (p.unit ? ` ${p.unit}` : '');
  });

  return {
    id: 'ASMT-2026-' + Math.floor(1000 + Math.random() * 9000),
    productId: 'PRD-' + Math.floor(1000 + Math.random() * 9000),
    productName: prodName,
    category: prodCat,
    manufacturingLocation: productData.manufacturingLocation || 'Noida, Uttar Pradesh',
    specifications: specs,
    parameters: parameters,
    referenceStandard: standardId,
    standardTitle: standardTitle,
    readinessScore: readinessScore,
    statusText: 'Compliance assessment complete with recommendations',
    statusType: readinessScore >= 90 ? 'success' : 'warning',
    gaps: gaps,
    costEstimate: {
      testingFees: 45000,
      bisRelatedFees: 12000,
      documentationFees: 5000,
      totalFees: 62000,
      disclaimer: 'Illustrative demo estimate based on standard industry laboratory benchmarks.',
    },
    timelineEstimate: {
      range: '30–45 days',
      disclaimer: 'Illustrative estimate based on typical test turnaround times.',
      phases: [
        { phase: 'Documentation Review', duration: '5–7 days', description: 'Internal validation of technical files, BoM, and markings' },
        { phase: 'Accredited Laboratory Testing', duration: '20–30 days', description: 'Clause verification in NABL-accredited BIS recognized lab' },
        { phase: 'Manakonline Grant & Scrutiny', duration: '5–8 days', description: 'Final BIS scrutiny and standard mark grant' },
      ],
    },
    assessedAt: new Date().toISOString(),
  };
}

export const INITIAL_ASSESSMENT_RESULT: AssessmentResult = generateDynamicAssessmentResult(EMPTY_PRODUCT_FORM);

export const RECHECKED_ASSESSMENT_RESULT: AssessmentResult = {
  ...INITIAL_ASSESSMENT_RESULT,
  readinessScore: 96,
  statusText: 'High readiness — All identified gaps addressed',
  statusType: 'success',
  isPostRecheck: true,
  gaps: INITIAL_ASSESSMENT_RESULT.gaps.map((g) => ({ ...g, isResolved: true, status: 'Resolved' as const })),
  assessedAt: new Date().toISOString(),
};
