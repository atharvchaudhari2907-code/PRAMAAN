import { AssessmentResult, ProductFormData, ExtractedParameter, StandardCandidate, ApplicationPreparationData, TrackingEvent, ChatMessage, VerificationResult } from '../types/assessment';
import { generateDynamicAssessmentResult } from '../data/demoData';
import { api } from './api';
import { trustLedgerService } from './trustLedgerService';

export const assessmentService = {
  /**
   * Initializes application and executes extraction pipeline.
   */
  async startAssessment(productData: ProductFormData): Promise<{
    applicationId: string;
    extractedParameters: ExtractedParameter[];
    standards: StandardCandidate[];
    missingInfo: string[];
    warnings: string[];
  }> {
    const isBackendAvailable = await api.checkHealth();

    if (isBackendAvailable) {
      try {
        // 1. Create Application
        const app = await api.createApplication({
          product_name: productData.name || 'Manufactured Product',
          category: productData.category || 'General',
          manufacturing_location: productData.manufacturingLocation || 'Noida, Uttar Pradesh',
          model_number: productData.modelNumber,
          manufacturer: productData.manufacturer,
        });

        const appId = app.id;

        // 2. Upload file if user selected a file
        if (productData.datasheetFile?.rawFile) {
          await api.uploadDocument(appId, productData.datasheetFile.rawFile);
        }

        // 3. Extract parameters
        const extraction = await api.extractParameters(appId);

        // 4. Identify standards
        const standards = await api.identifyStandards(appId);

        return {
          applicationId: appId,
          extractedParameters: extraction.parameters || [],
          standards: standards || [],
          missingInfo: extraction.missing_information || [],
          warnings: extraction.warnings || [],
        };
      } catch (err) {
        console.warn('Backend API error during startAssessment, falling back to local simulation:', err);
      }
    }

    // Local fallback for offline simulation
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    const prodName = productData.name || 'Manufactured Product';
    const prodCat = productData.category || 'General Equipment';
    const nameLower = prodName.toLowerCase();
    const catLower = prodCat.toLowerCase();

    let extractedParams: ExtractedParameter[] = [];
    let standardCandidates: StandardCandidate[] = [];

    if (catLower.includes('cooker') || nameLower.includes('cooker')) {
      extractedParams = [
        { parameter_key: 'operating_pressure', name: 'Nominal Operating Pressure', value: '1.0', unit: 'kgf/cm²', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'proof_pressure', name: 'Hydraulic Proof Pressure', value: '2.0', unit: 'kgf/cm²', source_page: 2, confidence: 'HIGH' },
        { parameter_key: 'material_grade', name: 'Body & Lid Material Grade', value: 'AISI 304 Food Grade Stainless Steel', unit: '', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'nominal_capacity', name: 'Nominal Cooking Capacity', value: '5.0', unit: 'Litres', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'safety_valve', name: 'Secondary Safety Release Pressure', value: '1.5', unit: 'kgf/cm²', source_page: 2, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 2347 : 2017',
          title: 'Domestic Pressure Cookers — Specification (Fifth Revision)',
          version: '2017',
          category: 'Kitchen & Pressure Cookers',
          confidence_score: 0.96,
          match_reason: `Product '${prodName}' matches scope for Domestic Pressure Cookers under IS 2347.`,
          is_primary: true,
        },
      ];
    } else if (nameLower.includes('iron') || nameLower.includes('steamer')) {
      extractedParams = [
        { parameter_key: 'rated_power', name: 'Rated Power Input', value: '1200', unit: 'W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'rated_voltage', name: 'Rated Voltage', value: '230', unit: 'V AC', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'supply_frequency', name: 'Supply Frequency', value: '50', unit: 'Hz', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'insulation_resistance', name: 'Insulation Resistance', value: '5.2', unit: 'MΩ', source_page: 2, confidence: 'HIGH' },
        { parameter_key: 'leakage_current', name: 'Protective Conductor Current', value: '0.35', unit: 'mA', source_page: 2, confidence: 'HIGH' },
        { parameter_key: 'thermal_cutout', name: 'Non-Self Resetting Thermal Fuse', value: 'Fitted (240°C Rating)', unit: '', source_page: 2, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 302 (Part 2/Sec 3) : 2007',
          title: 'Safety of Household Electrical Appliances — Particular Requirements for Electric Irons',
          version: '2007',
          category: 'Household Electrical Appliances',
          confidence_score: 0.95,
          match_reason: `Product '${prodName}' matches scope for electric irons under IS 302-2-3.`,
          is_primary: true,
        },
        {
          standard_id: 'IS 302 (Part 1) : 2008',
          title: 'Safety of Household and Similar Electrical Appliances — General Requirements',
          version: '2008',
          category: 'Household Electrical Appliances',
          confidence_score: 0.88,
          match_reason: 'Matches general electrical safety scope.',
          is_primary: false,
        },
      ];
    } else if (catLower.includes('fan') || nameLower.includes('fan')) {
      extractedParams = [
        { parameter_key: 'air_delivery', name: 'Air Delivery (1200mm Sweep)', value: '215', unit: 'm³/min', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'service_value', name: 'BEE Service Value (Air Delivery / Power)', value: '4.3', unit: 'm³/min/W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'rated_power', name: 'Rated Power Input', value: '50', unit: 'W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'rated_voltage', name: 'Rated Supply Voltage', value: '230', unit: 'V AC', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'insulation_resistance', name: 'Insulation Resistance', value: '4.8', unit: 'MΩ', source_page: 2, confidence: 'HIGH' },
        { parameter_key: 'safety_wire', name: 'Secondary Suspension Safety Wire', value: '4x Rated Weight Compliant', unit: '', source_page: 2, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 374 : 2019',
          title: 'Electric Ceiling Type Fans and Regulators — Specification',
          version: '2019',
          category: 'Household Electrical Appliances',
          confidence_score: 0.95,
          match_reason: `Product '${prodName}' matches scope for Electric Ceiling Fans under IS 374.`,
          is_primary: true,
        },
      ];
    } else if (catLower.includes('light') || nameLower.includes('lamp') || nameLower.includes('bulb')) {
      extractedParams = [
        { parameter_key: 'wattage', name: 'Rated Wattage', value: '9', unit: 'W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'voltage', name: 'Rated Voltage', value: '230', unit: 'V AC', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'luminous_efficacy', name: 'Luminous Efficacy', value: '78', unit: 'lm/W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'cri', name: 'Color Rendering Index (CRI)', value: '82', unit: 'Ra', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'power_factor', name: 'Power Factor', value: '0.92', unit: '', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'thd', name: 'Total Harmonic Distortion (THD)', value: '24.5', unit: '%', source_page: 1, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 16102 (Part 1) : 2012',
          title: 'Self-Ballasted LED Lamps for General Lighting Services — Safety Requirements',
          version: '2012',
          category: 'Lighting & Luminaires',
          confidence_score: 0.94,
          match_reason: `Product '${prodName}' matches scope for LED lighting under IS 16102.`,
          is_primary: true,
        },
        {
          standard_id: 'IS 14785 : 2021',
          title: 'Self-Ballasted LED Lamps — Performance Requirements',
          version: '2021',
          category: 'Lighting & Luminaires',
          confidence_score: 0.90,
          match_reason: 'Matches performance & luminous efficacy evaluation.',
          is_primary: false,
        },
      ];
    } else if (catLower.includes('audio') || catLower.includes('headphone') || nameLower.includes('headphone') || nameLower.includes('earphone') || nameLower.includes('bluetooth') || nameLower.includes('audio')) {
      extractedParams = [
        { parameter_key: 'bluetooth_version', name: 'Bluetooth Version', value: 'Bluetooth 5.3', unit: '', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'wireless_frequency', name: 'Wireless Frequency', value: '2.402 – 2.480 GHz', unit: 'GHz', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'rated_input', name: 'Rated Input', value: '5 V DC, 1 A', unit: 'V DC, A', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'battery_capacity', name: 'Battery Capacity', value: '500 mAh', unit: 'mAh', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'speaker_driver', name: 'Speaker Driver', value: '40 mm dynamic driver', unit: 'mm', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'speaker_impedance', name: 'Speaker Impedance', value: '32 Ω', unit: 'Ω', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'frequency_response', name: 'Frequency Response', value: '20 Hz – 20 kHz', unit: 'Hz - kHz', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'maximum_audio_power', name: 'Maximum Audio Power', value: '20 mW per channel', unit: 'mW', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'product_weight', name: 'Product Weight', value: '285 g', unit: 'g', source_page: 1, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 616 : 2017',
          title: 'Audio, Video and Similar Electronic Apparatus — Safety Requirements',
          version: '2017',
          category: 'Electronics & IT Goods',
          confidence_score: 0.95,
          match_reason: `Product '${prodName}' matches mandatory CRS scope for wireless audio devices under IS 616 : 2017.`,
          is_primary: true,
        },
        {
          standard_id: 'IS 16046 (Part 2) : 2018',
          title: 'Secondary Cells and Batteries (Lithium Systems) — Safety Requirements',
          version: '2018',
          category: 'Electronics & IT Goods',
          confidence_score: 0.88,
          match_reason: 'Matches rechargeable lithium-ion battery integration safety scope.',
          is_primary: false,
        },
      ];
    } else {
      extractedParams = [
        { parameter_key: 'rated_power', name: 'Rated Power', value: '100', unit: 'W', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'rated_voltage', name: 'Rated Supply Voltage', value: '230', unit: 'V AC', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'operating_frequency', name: 'Supply Frequency', value: '50', unit: 'Hz', source_page: 1, confidence: 'HIGH' },
        { parameter_key: 'insulation_resistance', name: 'Insulation Resistance', value: '5.0', unit: 'MΩ', source_page: 1, confidence: 'HIGH' },
      ];
      standardCandidates = [
        {
          standard_id: 'IS 13252 (Part 1) : 2010',
          title: 'Information Technology Equipment — Safety — General Requirements',
          version: '2010',
          category: 'Electronics & IT Goods',
          confidence_score: 0.90,
          match_reason: `Product '${prodName}' falls under general equipment safety assessment.`,
          is_primary: true,
        },
      ];
    }

    return {
      applicationId: 'ASMT-2026-DEMO',
      extractedParameters: extractedParams,
      standards: standardCandidates,
      missingInfo: ['Factory quality test logs (Scheme I)', 'Bilingual Clause markings specification'],
      warnings: ['Accredited laboratory test sample required for official Manakonline registration'],
    };
  },

  /**
   * Updates reviewed parameters & selected standard, then performs compliance analysis.
   */
  async runComplianceAnalysis(
    applicationId: string,
    selectedStandardId: string,
    parameters: ExtractedParameter[],
    productData: ProductFormData
  ): Promise<AssessmentResult> {
    const isBackendAvailable = await api.checkHealth();

    if (isBackendAvailable && applicationId !== 'ASMT-2026-DEMO') {
      try {
        await api.updateParameters(applicationId, parameters);
        await api.selectStandard(applicationId, selectedStandardId);
        await api.retrieveRequirements(applicationId);
        const result = await api.analyzeApplication(applicationId);
        return result;
      } catch (err) {
        console.warn('Backend error during analyzeApplication, using dynamic adapter:', err);
      }
    }

    // Dynamic offline simulation
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return generateDynamicAssessmentResult(productData, selectedStandardId, parameters);
  },

  /**
   * Performs analysis for the initial demo product without modal if user submits directly.
   */
  async analyzeProduct(productData: ProductFormData): Promise<AssessmentResult> {
    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable) {
      try {
        const app = await api.createApplication({
          product_name: productData.name || 'Manufactured Product',
          category: productData.category || 'General',
          manufacturing_location: productData.manufacturingLocation || 'Noida, Uttar Pradesh',
          model_number: productData.modelNumber,
          manufacturer: productData.manufacturer,
        });

        if (productData.datasheetFile?.rawFile) {
          await api.uploadDocument(app.id, productData.datasheetFile.rawFile);
        }

        const ext = await api.extractParameters(app.id);
        const stds = await api.identifyStandards(app.id);
        const chosenStd = stds[0]?.standard_id || 'IS 302 (Part 1)';
        await api.selectStandard(app.id, chosenStd);
        const res = await api.analyzeApplication(app.id);
        return res;
      } catch (e) {
        console.warn('Backend call failed, using fallback:', e);
      }
    }

    return generateDynamicAssessmentResult(productData);
  },

  /**
   * Rechecks product with simulated engineering fixes.
   */
  async recheckProduct(
    currentAssessment: AssessmentResult,
    customEfficacy: number = 84
  ): Promise<AssessmentResult> {
    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable && currentAssessment.id && !currentAssessment.id.includes('DEMO')) {
      const res = await api.recheckApplication(currentAssessment.id, customEfficacy);
      return res;
    }


    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      ...currentAssessment,
      readinessScore: 96,
      statusText: 'High readiness — All identified gaps addressed',
      statusType: 'success',
      isPostRecheck: true,
      gaps: currentAssessment.gaps.map((gap) => ({
        ...gap,
        isResolved: true,
        status: 'Resolved' as const,
      })),
      assessedAt: new Date().toISOString(),
    };
  },

  /**
   * Fetches prepared BIS application dossier.
   */
  async getPreparedApplication(applicationId: string): Promise<ApplicationPreparationData> {
    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable && applicationId && !applicationId.includes('DEMO')) {
      try {
        return await api.prepareApplication(applicationId);
      } catch (e) {
        console.warn('Error fetching preparation dossier:', e);
      }
    }

    return {
      application_id: applicationId,
      product_name: 'Evaluated Product',
      category: 'Electronics',
      model_number: 'Model-01',
      manufacturer: 'Manufacturer Enterprise',
      manufacturing_location: 'Noida, Uttar Pradesh',
      applicable_standard: 'IS 302 (Part 1)',
      standard_title: 'Safety of Household and Similar Electrical Appliances',
      readiness_score: 92.0,
      validation_status: 'READY_FOR_MANAKONLINE',
      fields: [
        { label: 'Applicant Enterprise', value: 'Manufacturer Enterprise', is_complete: true, section: 'Manufacturer Profile' },
        { label: 'Manufacturing Facility Address', value: 'Industrial Area, Phase 2', is_complete: true, section: 'Manufacturer Profile' },
        { label: 'Product Nomenclature', value: 'Electrical Appliance', is_complete: true, section: 'Product Details' },
        { label: 'Model Designation', value: 'Model-01', is_complete: true, section: 'Product Details' },
        { label: 'Applicable Standard', value: 'IS 302 (Part 1)', is_complete: true, section: 'Standard & Scheme' },
      ],
      required_documents: [
        { document_name: 'Technical Datasheet / Product Specification', is_attached: true, status: 'ATTACHED', description: 'Product engineering drawing, BOM, and electrical rating sheet.' },
        { document_name: 'Factory Process Flowchart & Quality Plan', is_attached: true, status: 'ATTACHED', description: 'Assembly flow and QC test station checkpoints.' },
        { document_name: 'In-house Test Equipment Calibration Certificates', is_attached: true, status: 'ATTACHED', description: 'Calibration records for test equipment.' },
      ],
      missing_information: [],
      official_portal_url: 'https://www.manakonline.in',
      disclaimer: 'This pre-filled dossier is generated for preparation. Formal submission must be completed on official BIS Manakonline portal (manakonline.in).',
    };
  },

  /**
   * Fetches tracking events for the application.
   */
  async getTrackingEvents(applicationId: string): Promise<TrackingEvent[]> {
    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable && applicationId && !applicationId.includes('DEMO')) {
      try {
        return await api.getTrackingEvents(applicationId);
      } catch (e) {
        console.warn('Error fetching tracking events:', e);
      }
    }

    return [
      { id: 'EVT-01', stage: 'SUBMITTED', title: 'Product Assessment Initiated', description: 'Technical datasheet and specifications uploaded.', status: 'COMPLETED', timestamp: new Date(Date.now() - 86400000 * 4).toISOString(), is_simulated: true },
      { id: 'EVT-02', stage: 'DOCUMENTS_VERIFIED', title: 'Parameter Gap Analysis Completed', description: 'Technical parameters benchmarked against applicable Indian Standard specifications.', status: 'IN_PROGRESS', timestamp: new Date(Date.now() - 86400000 * 2).toISOString(), is_simulated: true },
      { id: 'EVT-03', stage: 'TESTING', title: 'Accredited Lab Sample Testing', description: 'Safety and performance testing verification.', status: 'PENDING', timestamp: new Date(Date.now() + 86400000 * 15).toISOString(), is_simulated: true },
      { id: 'EVT-04', stage: 'BIS_REVIEW', title: 'Factory Quality Audit', description: 'Technical audit of production line.', status: 'PENDING', timestamp: new Date(Date.now() + 86400000 * 35).toISOString(), is_simulated: true },
      { id: 'EVT-05', stage: 'CERTIFICATE_ISSUED', title: 'Standard Mark License Grant', description: 'Official standard mark grant issuance.', status: 'PENDING', timestamp: new Date(Date.now() + 86400000 * 50).toISOString(), is_simulated: true },
    ];
  },

  /**
   * Sends grounded message to contextual AI assistant.
   */
  async sendChatMessage(applicationId: string, message: string): Promise<ChatMessage> {
    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable && applicationId && !applicationId.includes('DEMO')) {
      try {
        return await api.sendChatMessage(applicationId, message);
      } catch (e) {
        console.warn('Chat API error:', e);
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 600));
    const qLower = message.toLowerCase();
    let content = 'Regarding your product assessment: Ensure all mandatory parameters satisfy configured reference thresholds before submitting test samples to an accredited laboratory.';
    let citations = [{ standard_id: 'IS 302 (Part 1)', clause: 'Scope', title: 'General Safety Requirements' }];

    if (qLower.includes('is 302') || qLower.includes('standard')) {
      content = 'IS 302 (Part 1):2024 is the general safety standard for household and similar electrical appliances. It governs electrical insulation, protection against electric shock, construction safety, and marking requirements.';
      citations = [{ standard_id: 'IS 302 (Part 1)', clause: 'Clause 1', title: 'Scope and General Safety' }];
    } else if (qLower.includes('gap') || qLower.includes('fail')) {
      content = 'Based on the available specifications, all evaluated parameters satisfy reference thresholds with 0 critical non-conformities.';
      citations = [{ standard_id: 'IS 302 (Part 1)', clause: 'Clause 7', title: 'Marking & Performance' }];
    }

    return {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content,
      citations,
      created_at: new Date().toISOString(),
    };
  },

  /**
   * Verifies certificate / document integrity via SHA-256 hash.
   */
  async verifyIntegrity(sha256Hash: string, documentName?: string): Promise<VerificationResult> {
    const normalizedHash = sha256Hash.trim();

    const isBackendAvailable = await api.checkHealth();
    if (isBackendAvailable) {
      try {
        return await api.verifyHash(normalizedHash, documentName);
      } catch (e) {
        console.warn('Verify API error:', e);
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 500));

    const cleanHash = normalizedHash.toLowerCase();
    const is64Hex = /^[a-f0-9]{64}$/.test(cleanHash);
    const records = await trustLedgerService.listProducts();
    const matchedRecord = records.find((record) => record.record_hash.toLowerCase() === cleanHash);

    const isVerified = is64Hex && !!matchedRecord;

    return {
      sha256_hash: normalizedHash,
      is_verified: isVerified,
      matched_application_id: isVerified ? matchedRecord!.certificate_id : undefined,
      matched_document_name: isVerified ? (documentName || matchedRecord!.product_name) : undefined,
      timestamp: new Date().toISOString(),
      integrity_status: isVerified ? 'VALID_RECORD' : 'UNKNOWN_RECORD',
      blockchain_network: 'Tamper-Evident Integrity Ledger (SHA-256 Verified)',
      message: isVerified
        ? `Cryptographic integrity verified. Document matches authentic pre-certification record ${matchedRecord!.certificate_id}.`
        : 'SHA-256 hash computed. No registered record found in the local integrity ledger.',
    };
  },
};
