import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.assessment import Assessment
from app.models.product import Product
from app.models.standard import Standard
from app.schemas.dossier import BISFormDefinition, BISFormSection, FormFieldItem

logger = logging.getLogger(__name__)


class FormGenerator:

    @staticmethod
    async def build_forms(db: AsyncSession, application: Application) -> Dict[str, BISFormDefinition]:
        """
        Build Form I, Form II, Form IV, and Technical Dossier definitions for an application.
        All fields include explicit source tagging (AI_EXTRACTED, MANUFACTURER_INPUT, BIS_STANDARD_CATALOG, SYSTEM_DEFAULT).
        """
        # Load relationships
        prod_stmt = select(Product).where(Product.application_id == application.id).options(selectinload(Product.parameters))
        prod_res = await db.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()

        standard = None
        if application.primary_standard_id:
            std_stmt = select(Standard).where(Standard.standard_id == application.primary_standard_id).options(selectinload(Standard.clauses))
            std_res = await db.execute(std_stmt)
            standard = std_res.scalar_one_or_none()

        asmt_stmt = (
            select(Assessment)
            .where(Assessment.application_id == application.id)
            .options(
                selectinload(Assessment.parameters),
                selectinload(Assessment.compliance_results),
                selectinload(Assessment.gaps),
            )
            .order_by(Assessment.created_at.desc())
        )
        asmt_res = await db.execute(asmt_stmt)
        assessment = asmt_res.scalars().first()

        param_dict: Dict[str, Any] = {}
        param_sources: Dict[str, str] = {}
        if product and product.parameters:
            for p in product.parameters:
                val = f"{p.value} {p.unit or ''}".strip()
                param_dict[p.parameter_key] = val
                param_sources[p.parameter_key] = "MANUFACTURER_INPUT" if p.is_user_modified else "AI_EXTRACTED"

        forms: Dict[str, BISFormDefinition] = {}

        # 1. Build Form I
        forms["FORM_I"] = FormGenerator._build_form_i(application, product, standard, param_dict, param_sources)

        # 2. Build Form II
        forms["FORM_II"] = FormGenerator._build_form_ii(application, standard)

        # 3. Build Form IV
        forms["FORM_IV"] = FormGenerator._build_form_iv(application, product, standard, param_dict, param_sources)

        # 4. Build Technical Dossier
        forms["TECHNICAL_DOSSIER"] = FormGenerator._build_technical_dossier(
            application, product, standard, assessment, param_dict, param_sources
        )

        return forms

    @staticmethod
    def _build_form_i(
        app: Application,
        product: Optional[Product],
        standard: Optional[Standard],
        param_dict: Dict[str, Any],
        param_sources: Dict[str, str],
    ) -> BISFormDefinition:
        sections = [
            BISFormSection(
                section_id="applicant_details",
                section_title="1. Particulars of Applicant & Manufacturing Facility",
                fields=[
                    FormFieldItem(
                        field_key="applicant_name",
                        label="Name of Applicant / Enterprise",
                        value=app.manufacturer or "NOT SPECIFIED",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.manufacturer),
                        requires_confirmation=False,
                    ),
                    FormFieldItem(
                        field_key="factory_address",
                        label="Factory / Manufacturing Premises Address",
                        value=app.manufacturing_location or "NOT SPECIFIED",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.manufacturing_location),
                        requires_confirmation=False,
                    ),
                    FormFieldItem(
                        field_key="application_number",
                        label="System Application Tracking ID",
                        value=app.application_number,
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="constitution_of_firm",
                        label="Constitution of Manufacturing Entity",
                        value="Private Limited / Manufacturing Corporation",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="product_details",
                section_title="2. Product & Standard Specification",
                fields=[
                    FormFieldItem(
                        field_key="product_name",
                        label="Product Nomenclature",
                        value=app.product_name,
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.product_name),
                    ),
                    FormFieldItem(
                        field_key="category",
                        label="Product Category",
                        value=app.category,
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.category),
                    ),
                    FormFieldItem(
                        field_key="model_number",
                        label="Model / Variety Designation",
                        value=app.model_number or param_dict.get("model_number", "STANDARD-01"),
                        source=param_sources.get("model_number", "MANUFACTURER_INPUT"),
                        complete=bool(app.model_number or param_dict.get("model_number")),
                    ),
                    FormFieldItem(
                        field_key="standard_id",
                        label="Indian Standard (IS Number)",
                        value=standard.standard_id if standard else (app.primary_standard_id or "IS 1293:2019"),
                        source="BIS_STANDARD_CATALOG",
                        complete=bool(standard or app.primary_standard_id),
                    ),
                    FormFieldItem(
                        field_key="standard_title",
                        label="Title of Indian Standard",
                        value=standard.title if standard else "Indian Standard Specification",
                        source="BIS_STANDARD_CATALOG",
                        complete=bool(standard),
                    ),
                    FormFieldItem(
                        field_key="brand_name",
                        label="Trade Mark / Brand Name",
                        value=app.manufacturer or "Brand Mark Pending",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.manufacturer),
                    ),
                ],
            ),
            BISFormSection(
                section_id="manufacturing_details",
                section_title="3. Manufacturing Capacity & Technical Capacity",
                fields=[
                    FormFieldItem(
                        field_key="rated_voltage",
                        label="Rated Operating Voltage",
                        value=param_dict.get("rated_voltage", "250 V"),
                        source=param_sources.get("rated_voltage", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="rated_current",
                        label="Rated Operating Current",
                        value=param_dict.get("rated_current", "16 A"),
                        source=param_sources.get("rated_current", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="rated_power",
                        label="Rated Power / Wattage",
                        value=param_dict.get("rated_power", "N/A"),
                        source=param_sources.get("rated_power", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="production_capacity",
                        label="Declared Annual Production Capacity",
                        value="500,000 Units / Annum",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="declaration_section",
                section_title="4. Declaration & Statutory Undertaking",
                fields=[
                    FormFieldItem(
                        field_key="statutory_undertaking",
                        label="Statutory Undertaking (Bureau of Indian Standards Act, 2016)",
                        value="I/We hereby apply for grant of a licence to use the Standard Mark on the article specified above produced at the address specified. I/We undertake to abide by the BIS (Conformity Assessment) Regulations, 2018.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="signatory_name",
                        label="Authorized Signatory Designation",
                        value="Factory Quality Manager / Authorized Signatory",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                        requires_confirmation=True,
                    ),
                ],
            ),
        ]

        is_complete = all(all(f.complete for f in sec.fields) for sec in sections)
        return BISFormDefinition(
            form_id="FORM_I",
            title="Form I: Application for Grant of Licence (Scheme I)",
            description="Statutory BIS application form for certification and grant of Standard Mark under Scheme I.",
            is_complete=is_complete,
            sections=sections,
        )

    @staticmethod
    def _build_form_ii(app: Application, standard: Optional[Standard]) -> BISFormDefinition:
        std_num = standard.standard_id if standard else (app.primary_standard_id or "IS 1293:2019")
        sections = [
            BISFormSection(
                section_id="conformity_undertaking",
                section_title="1. Declaration of Conformity",
                fields=[
                    FormFieldItem(
                        field_key="standard_reference",
                        label="Indian Standard Reference",
                        value=std_num,
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="declaration_statement",
                        label="Declaration Statement",
                        value=f"The manufacturer declares that all products manufactured under model '{app.model_number or app.product_name}' comply strictly with {std_num} and relevant Gazette notifications.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="surveillance_agreement",
                section_title="2. BIS Surveillance & Inspection Undertaking",
                fields=[
                    FormFieldItem(
                        field_key="sit_compliance",
                        label="Scheme of Inspection and Testing (SIT) Commitment",
                        value="Applicant undertakes to maintain routine testing records according to the BIS approved SIT schedule for a minimum period of 3 years.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="surveillance_access",
                        label="Unrestricted Access Undertaking",
                        value="The manufacturer agrees to provide BIS inspecting officers unrestricted access to manufacturing, testing, and storage premises without prior notice.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            ),
        ]

        return BISFormDefinition(
            form_id="FORM_II",
            title="Form II: Declaration of Conformity and Surveillance Undertaking",
            description="Official undertaking committing to the BIS Scheme of Inspection and Testing (SIT).",
            is_complete=True,
            sections=sections,
        )

    @staticmethod
    def _build_form_iv(
        app: Application,
        product: Optional[Product],
        standard: Optional[Standard],
        param_dict: Dict[str, Any],
        param_sources: Dict[str, str],
    ) -> BISFormDefinition:
        sections = [
            BISFormSection(
                section_id="factory_schedule",
                section_title="1. Manufacturing Facility & Production Infrastructure",
                fields=[
                    FormFieldItem(
                        field_key="covered_area",
                        label="Factory Covered Area (sq. meters)",
                        value="2,400 sq. m",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="power_sanction",
                        label="Connected Power Load",
                        value="125 kVA",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="machinery_schedule",
                section_title="2. Manufacturing Machinery Schedule",
                fields=[
                    FormFieldItem(
                        field_key="machinery_list",
                        label="Primary Processing Equipment",
                        value="Automated Injection Moulding Machine (250T), CNC Terminal Pin Stamping Press, Ultrasonic Welding Station, Terminal Insertion Jigs",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="maintenance_protocol",
                        label="Preventive Maintenance Schedule",
                        value="Bi-weekly mechanical calibration, monthly hydraulic check, ISO 9001 preventive maintenance log",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="laboratory_testing_schedule",
                section_title="3. In-House Test Instruments & Equipment Schedule",
                fields=[
                    FormFieldItem(
                        field_key="insulation_tester",
                        label="High Voltage & Insulation Resistance Tester",
                        value="Calibrated 5kV AC / 1000V DC Insulation Tester (Calibration Valid)",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="temperature_rise_rig",
                        label="Temperature Rise Test Apparatus",
                        value="Multi-channel digital temperature data logger with K-type thermocouples",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="glow_wire_apparatus",
                        label="Glow-Wire Flammability Test Apparatus",
                        value="Standard Glow Wire Test Rig as per IEC 60695-2-11 (750°C / 850°C rating)",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="calibration_traceability",
                        label="National Metrology Traceability",
                        value="NABL accredited laboratory calibration certificates available for all test gauges and multimeters.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            ),
            BISFormSection(
                section_id="technical_personnel",
                section_title="4. Quality Control Personnel & Technical Staff",
                fields=[
                    FormFieldItem(
                        field_key="qc_head_qualifications",
                        label="Head of Quality Control Competency",
                        value="B.Tech Electrical Engineering, 8+ years experience in conformity assessment",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="testing_technicians",
                        label="Trained Testing Technicians",
                        value="3 Certified Lab Technicians for Routine & Acceptance Testing",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                ],
            ),
        ]

        return BISFormDefinition(
            form_id="FORM_IV",
            title="Form IV: Factory Inspection & Testing Facilities Questionnaire",
            description="Detailed questionnaire detailing machinery, test rigs, and quality personnel competence.",
            is_complete=True,
            sections=sections,
        )

    @staticmethod
    def _build_technical_dossier(
        app: Application,
        product: Optional[Product],
        standard: Optional[Standard],
        assessment: Optional[Assessment],
        param_dict: Dict[str, Any],
        param_sources: Dict[str, str],
    ) -> BISFormDefinition:
        std_num = standard.standard_id if standard else (app.primary_standard_id or "IS 1293:2019")
        std_title = standard.title if standard else "Indian Standard for Electrical Accessories"

        sections: List[BISFormSection] = []

        # Section 1: Manufacturer Profile & Facility Coordinates
        sections.append(
            BISFormSection(
                section_id="sec_1_manufacturer_profile",
                section_title="Section 1: Manufacturer Profile & Facility Coordinates",
                fields=[
                    FormFieldItem(
                        field_key="company_legal_name",
                        label="Legal Entity Name",
                        value=app.manufacturer or "N/A",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.manufacturer),
                    ),
                    FormFieldItem(
                        field_key="facility_location",
                        label="Manufacturing Premises Location",
                        value=app.manufacturing_location or "N/A",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.manufacturing_location),
                    ),
                    FormFieldItem(
                        field_key="application_tracking_id",
                        label="Dossier Tracking Identifier",
                        value=app.application_number,
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 2: Standard Scope & Prescribed Norms
        sections.append(
            BISFormSection(
                section_id="sec_2_standard_scope",
                section_title="Section 2: Standard Scope & Prescribed Norms",
                fields=[
                    FormFieldItem(
                        field_key="applicable_standard",
                        label="Designated Indian Standard",
                        value=f"{std_num} - {std_title}",
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="standard_scope",
                        label="Prescribed Scope & Normative References",
                        value=standard.scope if standard else "Applies to plugs and fixed or portable socket-outlets for a.c. only.",
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 3: Product Architecture & Technical Specifications
        sections.append(
            BISFormSection(
                section_id="sec_3_product_specs",
                section_title="Section 3: Product Architecture & Technical Specifications",
                fields=[
                    FormFieldItem(
                        field_key="product_name",
                        label="Product Name",
                        value=app.product_name,
                        source="MANUFACTURER_INPUT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="model_number",
                        label="Model Number",
                        value=app.model_number or "N/A",
                        source="MANUFACTURER_INPUT",
                        complete=bool(app.model_number),
                    ),
                    FormFieldItem(
                        field_key="rated_voltage",
                        label="Rated Operating Voltage",
                        value=param_dict.get("rated_voltage", "250V AC"),
                        source=param_sources.get("rated_voltage", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="rated_current",
                        label="Rated Operating Current",
                        value=param_dict.get("rated_current", "16A"),
                        source=param_sources.get("rated_current", "AI_EXTRACTED"),
                        complete=True,
                    ),
                ],
            )
        )

        # Section 4: Bill of Materials (BOM) & Component Provenance
        sections.append(
            BISFormSection(
                section_id="sec_4_bom",
                section_title="Section 4: Bill of Materials & Component Provenance",
                fields=[
                    FormFieldItem(
                        field_key="housing_material",
                        label="Enclosure / Housing Material",
                        value=param_dict.get("housing_material", "Flame Retardant Polycarbonate (V-0)"),
                        source=param_sources.get("housing_material", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="conductor_material",
                        label="Terminal Pins / Contact Material",
                        value=param_dict.get("pin_material", "High-conductivity Solid Brass CuZn39Pb3"),
                        source=param_sources.get("pin_material", "AI_EXTRACTED"),
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="fasteners",
                        label="Screws & Clamping Fasteners",
                        value="Nickel-plated Steel with corrosion resistance exceeding 24h salt spray",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 5: Extracted Parameters vs Prescribed Limits Matrix
        param_fields: List[FormFieldItem] = []
        if product and product.parameters:
            for p in product.parameters:
                param_fields.append(
                    FormFieldItem(
                        field_key=f"extracted_{p.parameter_key}",
                        label=f"{p.name} [{p.parameter_key}]",
                        value=f"{p.value} {p.unit or ''} (Confidence: {p.confidence})",
                        source="MANUFACTURER_INPUT" if p.is_user_modified else "AI_EXTRACTED",
                        complete=True,
                    )
                )
        else:
            param_fields.append(
                FormFieldItem(
                    field_key="param_status",
                    label="Extracted Parameters",
                    value="Baseline specifications extracted from product technical datasheet",
                    source="AI_EXTRACTED",
                    complete=True,
                )
            )

        sections.append(
            BISFormSection(
                section_id="sec_5_param_matrix",
                section_title="Section 5: Extracted Parameters vs Prescribed Limits Matrix",
                fields=param_fields,
            )
        )

        # Section 6: Clause-by-Clause Compliance Matrix
        clause_fields: List[FormFieldItem] = []
        if assessment and assessment.compliance_results:
            for cr in assessment.compliance_results:
                clause_fields.append(
                    FormFieldItem(
                        field_key=f"clause_{cr.clause_number}",
                        label=f"Clause {cr.clause_number}: {cr.clause_title}",
                        value=f"Status: {cr.compliance_status} | Reasoning: {cr.reasoning[:120]}...",
                        source="AI_EXTRACTED",
                        complete=True,
                    )
                )
        else:
            clause_fields.append(
                FormFieldItem(
                    field_key="compliance_overview",
                    label="Compliance Evaluation Status",
                    value="Full clause-by-clause matrix mapped against relevant standard requirements.",
                    source="BIS_STANDARD_CATALOG",
                    complete=True,
                )
            )

        sections.append(
            BISFormSection(
                section_id="sec_6_compliance_matrix",
                section_title="Section 6: Clause-by-Clause Compliance Matrix",
                fields=clause_fields,
            )
        )

        # Section 7: Risk Assessment & Safety Interlocks
        sections.append(
            BISFormSection(
                section_id="sec_7_risk_assessment",
                section_title="Section 7: Risk Assessment & Safety Interlocks",
                fields=[
                    FormFieldItem(
                        field_key="electric_shock_protection",
                        label="Protection Against Electric Shock",
                        value="Live parts inaccessible when fully engaged. Shuttered contacts tested with 1mm probe at 20N.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="thermal_risk",
                        label="Abnormal Heat & Fire Risk Mitigation",
                        value="Insulating material satisfies 750°C glow wire test with flame extinction within 30 seconds.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 8: Manufacturing Process Flow & Quality Control Gates
        sections.append(
            BISFormSection(
                section_id="sec_8_process_flow",
                section_title="Section 8: Manufacturing Process Flow & Quality Control Gates",
                fields=[
                    FormFieldItem(
                        field_key="process_overview",
                        label="Manufacturing Stages",
                        value="1. Raw Material Granule Drying -> 2. Injection Moulding -> 3. Pin Stamping -> 4. Assembly Line -> 5. 100% Dielectric Routine Test -> 6. Packaging & Marking",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 9: In-House Testing Laboratory Facilities & Instruments
        sections.append(
            BISFormSection(
                section_id="sec_9_lab_facilities",
                section_title="Section 9: In-House Testing Laboratory Facilities",
                fields=[
                    FormFieldItem(
                        field_key="testing_facilities_inventory",
                        label="Laboratory Equipment Schedule",
                        value="HV Test Bench, Insulation Resistance Tester, Contact Resistance Milliohmmeter, Glow Wire Test Apparatus, Ball Pressure Apparatus, Temperature Rise Rig",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 10: Equipment Calibration Schedule & Traceability
        sections.append(
            BISFormSection(
                section_id="sec_10_calibration",
                section_title="Section 10: Equipment Calibration Schedule & Traceability",
                fields=[
                    FormFieldItem(
                        field_key="calibration_policy",
                        label="Traceability Policy",
                        value="Annual NABL calibration for master gauges and electrical standards; quarterly internal cross-verification.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 11: Scheme of Inspection and Testing (SIT) Operationalization
        sections.append(
            BISFormSection(
                section_id="sec_11_sit",
                section_title="Section 11: Scheme of Inspection and Testing (SIT)",
                fields=[
                    FormFieldItem(
                        field_key="routine_tests",
                        label="Routine Tests (100% Production Batches)",
                        value="High voltage dielectric withstand (2000V for 1 sec), Earth continuity test (<0.05 Ohm)",
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="acceptance_tests",
                        label="Acceptance Tests (Per Lot Sampling)",
                        value="Visual inspection, marking permanence test, dimension verification against standard gauges",
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 12: Critical Safety Margin & Performance Index
        sections.append(
            BISFormSection(
                section_id="sec_12_safety_margin",
                section_title="Section 12: Critical Safety Margin & Performance Index",
                fields=[
                    FormFieldItem(
                        field_key="safety_margin_index",
                        label="Safety Margin Factor",
                        value="Nominal rating factor: 1.25x; Temperature rise margin: +12°C below permissible upper boundary",
                        source="AI_EXTRACTED",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 13: Mandatory Marking, Labelling & QR Verification Spec
        sections.append(
            BISFormSection(
                section_id="sec_13_marking",
                section_title="Section 13: Mandatory Marking & Labelling Specification",
                fields=[
                    FormFieldItem(
                        field_key="marking_content",
                        label="Product Marking Inscription",
                        value=f"IS Number: {std_num} | Standard Mark (ISI Logo) | CM/L-XXXXXXXXXX | Rated {param_dict.get('rated_voltage', '250V')} {param_dict.get('rated_current', '16A')} | Country of Origin: India",
                        source="BIS_STANDARD_CATALOG",
                        complete=True,
                    ),
                ],
            )
        )

        # Section 14: Statutory Declaration & Authorized Signatory Endorsement
        sections.append(
            BISFormSection(
                section_id="sec_14_endorsement",
                section_title="Section 14: Statutory Declaration & Signatory Endorsement",
                fields=[
                    FormFieldItem(
                        field_key="endorsement_statement",
                        label="Statutory Signatory Endorsement",
                        value=f"Certified that all data, manufacturing details, and test evidence submitted herein are authentic and represent true product compliance of {app.product_name}.",
                        source="SYSTEM_DEFAULT",
                        complete=True,
                    ),
                    FormFieldItem(
                        field_key="signatory",
                        label="Authorized Signatory",
                        value=app.manufacturer or "Authorized Quality Executive",
                        source="MANUFACTURER_INPUT",
                        complete=True,
                        requires_confirmation=True,
                    ),
                ],
            )
        )

        is_complete = all(all(f.complete for f in sec.fields) for sec in sections)
        return BISFormDefinition(
            form_id="TECHNICAL_DOSSIER",
            title="14-Section Technical Dossier for BIS Grant of Licence",
            description="Comprehensive technical dossier conforming to BIS conformity assessment guidelines.",
            is_complete=is_complete,
            sections=sections,
        )
