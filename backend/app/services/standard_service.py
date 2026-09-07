from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standard import Standard, StandardClause
from app.repositories.standard_repository import StandardRepository


VERIFIED_STANDARDS_SEED = [
    {
        "standard_id": "IS 16102 (Part 1) : 2012",
        "title": "Self-Ballasted LED Lamps for General Lighting Services — Safety Requirements",
        "version": "2012",
        "category": "Lighting & Luminaires",
        "scope": "Specifies the safety and interchangeability requirements, together with the test methods and conditions required to show compliance of LED lamps with integrated means for controlling, intended for domestic and similar general lighting purposes.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2012-05-15",
        "active": True,
        "clauses": [
            {
                "clause_number": "6",
                "title": "Marking Requirements",
                "text": "Lamps shall be clearly and durably marked with mandatory parameters: Mark of origin, rated wattage (W), rated voltage or voltage range (V), rated frequency (Hz), and BIS Standard Mark license details.",
                "page": 4,
            },
            {
                "clause_number": "7",
                "title": "Interchangeability & Dimensions",
                "text": "Cap fitment shall conform to standard gauge dimensions (B22d or E27). Dimensional deviations that affect safety or fitment are not permissible.",
                "page": 5,
            },
            {
                "clause_number": "8",
                "title": "Protection Against Electric Shock",
                "text": "Lamps shall be so constructed that, without additional enclosure, no internal live parts or parts accessible after insertion into a lampholder are reachable by standard test finger.",
                "page": 6,
            },
            {
                "clause_number": "9",
                "title": "Insulation Resistance & Electric Strength",
                "text": "Insulation resistance between current-carrying parts and accessible conductive parts shall be not less than 4.0 MΩ tested at 500 V DC. High voltage dielectric strength test must withstand 2U + 1000 V.",
                "page": 7,
            },
            {
                "clause_number": "10",
                "title": "Mechanical Strength & Torsion Resistance",
                "text": "The cap shall remain firmly attached to the lamp when subjected to axial torque test: 3.0 Nm for B22d and E27 caps without loosening.",
                "page": 8,
            },
            {
                "clause_number": "11",
                "title": "Resistance to Heat and Fire",
                "text": "External parts of insulating material providing protection against electric shock shall be resistant to heat and fire, tested via glow-wire test at 650°C.",
                "page": 9,
            },
        ],
    },
    {
        "standard_id": "IS 302 (Part 2/Sec 3) : 2007",
        "title": "Safety of Household and Similar Electrical Appliances — Particular Requirements for Electric Irons",
        "version": "2007",
        "category": "Household Electrical Appliances",
        "scope": "Deals with the safety of electric dry irons and steam irons for household and similar use, rated voltage not exceeding 250 V.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2007-09-20",
        "active": True,
        "clauses": [
            {
                "clause_number": "7",
                "title": "Marking and Instructions",
                "text": "Appliance shall be marked with rated input in Watts or rated current in Amperes, rated voltage, symbol for nature of supply, and manufacturer model designation.",
                "page": 5,
            },
            {
                "clause_number": "8",
                "title": "Protection Against Access to Live Parts",
                "text": "Appliance shall be constructed so that there is adequate protection against accidental contact with live parts when tested with test probe B of IS 1401.",
                "page": 6,
            },
            {
                "clause_number": "10",
                "title": "Power Input and Current Tolerance",
                "text": "Power input at normal operating temperature shall not deviate from rated power input by more than +5% or -10% for appliances > 300 W.",
                "page": 7,
            },
            {
                "clause_number": "11",
                "title": "Heating & Temperature Rise",
                "text": "Temperature rises of handles and components shall not exceed limits: handles of rubber or wood ≤ 50 K; handles of plastic ≤ 60 K.",
                "page": 8,
            },
            {
                "clause_number": "13",
                "title": "Leakage Current and Electric Strength",
                "text": "Protective conductor current / leakage current shall not exceed 0.75 mA for Class I portable appliances.",
                "page": 10,
            },
        ],
    },
    {
        "standard_id": "IS 2347 : 2017",
        "title": "Domestic Pressure Cookers — Specification (Fifth Revision)",
        "version": "2017",
        "category": "Kitchen & Pressure Cookers",
        "scope": "Specifies requirements for domestic pressure cookers of capacities up to and including 20 litres, operated with internal steam pressure.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2017-08-10",
        "active": True,
        "clauses": [
            {
                "clause_number": "4",
                "title": "Material Quality Requirements",
                "text": "Body and lid shall be manufactured from food-grade stainless steel AISI 304 (conforming to IS 6911) or wrought aluminium alloy (conforming to IS 21).",
                "page": 3,
            },
            {
                "clause_number": "6.1",
                "title": "Nominal Operating Pressure",
                "text": "The pressure regulating weight/valve shall regulate pressure at 1.0 ± 0.1 kgf/cm² (98 ± 9.8 kPa) during cooking operation.",
                "page": 4,
            },
            {
                "clause_number": "6.3",
                "title": "Hydraulic Proof Pressure Test",
                "text": "Every pressure cooker body and lid assembly shall withstand internal hydraulic proof pressure of not less than 2.0 kgf/cm² (196 kPa) without leakage or permanent plastic deformation.",
                "page": 5,
            },
            {
                "clause_number": "6.4",
                "title": "Secondary Safety Release Device",
                "text": "Cookers shall have a secondary safety relief device (fusible plug or gasket release) that releases pressure between 1.5 to 2.5 kgf/cm² if the primary vent pipe is clogged.",
                "page": 6,
            },
            {
                "clause_number": "8",
                "title": "Marking and Instructions",
                "text": "Each cooker shall be permanently marked with manufacturer name or registered trade mark, nominal cooking capacity in litres, model number, and Standard Mark license number.",
                "page": 7,
            },
        ],
    },
    {
        "standard_id": "IS 374 : 2019",
        "title": "Electric Ceiling Type Fans and Regulators — Specification",
        "version": "2019",
        "category": "Household Electrical Appliances",
        "scope": "Applies to ceiling fans and regulators for AC supply at voltages not exceeding 250 V single-phase, blade sweep sizes 600 mm to 1500 mm.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2019-11-25",
        "active": True,
        "clauses": [
            {
                "clause_number": "8",
                "title": "Marking Requirements",
                "text": "Marked with rated voltage, frequency, blade sweep in mm, power input in Watts, air delivery in m³/min, and BIS license.",
                "page": 4,
            },
            {
                "clause_number": "10",
                "title": "Air Delivery Requirements",
                "text": "Minimum air delivery for 1200 mm sweep fans shall be not less than 210 m³/min at rated voltage.",
                "page": 6,
            },
            {
                "clause_number": "11",
                "title": "BEE Service Value (Efficiency)",
                "text": "Service value (ratio of air delivery in m³/min to power consumption in Watts) shall be not less than 4.0 m³/min/W for Star 1 rating.",
                "page": 7,
            },
            {
                "clause_number": "14",
                "title": "Mechanical Suspension & Safety Wire",
                "text": "Every ceiling fan downrod and motor assembly shall incorporate an independent secondary suspension safety wire capable of supporting at least 4 times the fan weight.",
                "page": 9,
            },
        ],
    },
    {
        "standard_id": "IS 16102 (Part 2) : 2012",
        "title": "Self-Ballasted LED Lamps for General Lighting Services — Performance Requirements",
        "version": "2012",
        "category": "Lighting & Luminaires",
        "scope": "Specifies performance requirements for self-ballasted LED lamps for general lighting services, including luminous efficacy, power factor, harmonic distortion, and wattage tolerance.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2012-08-20",
        "active": True,
        "clauses": [
            {
                "clause_number": "6",
                "title": "Marking & Product Labeling",
                "text": "Lamps shall be marked with rated wattage, rated voltage range, lumen output, luminous efficacy, power factor, and manufacturer identity.",
                "page": 4,
            },
            {
                "clause_number": "7",
                "title": "Luminous Efficacy",
                "text": "The initial luminous efficacy of self-ballasted LED lamps shall be not less than 80.0 lm/W for 9W rating under normal test conditions at rated voltage.",
                "page": 5,
            },
            {
                "clause_number": "8",
                "title": "Lamp Wattage Tolerance",
                "text": "The power consumed by the lamp at rated supply voltage shall not exceed the rated wattage by more than +10% or be less by more than -10%.",
                "page": 6,
            },
            {
                "clause_number": "9",
                "title": "Operating Voltage & Stability",
                "text": "The lamp shall operate stably across the full rated operating voltage range of 100 V to 300 V AC, 50 Hz without visible flicker or premature driver shutdown.",
                "page": 7,
            },
            {
                "clause_number": "10",
                "title": "Power Factor",
                "text": "The power factor of self-ballasted LED lamps having rated wattage exceeding 5 W shall be not less than 0.90.",
                "page": 8,
            },
            {
                "clause_number": "11",
                "title": "Total Harmonic Distortion (THD)",
                "text": "The total harmonic distortion (THD) of the input mains current for LED lamps shall not exceed 25% for compliance with power quality limits.",
                "page": 9,
            },
            {
                "clause_number": "12",
                "title": "Color Rendering Index (CRI)",
                "text": "The initial color rendering index (Ra) of general service LED lamps shall be not less than 80.",
                "page": 10,
            },
        ],
    },
    {
        "standard_id": "IS 616 : 2017",
        "title": "Audio, Video and Similar Electronic Apparatus — Safety Requirements",
        "version": "2017",
        "category": "Electronics & IT Goods",
        "scope": "Applies to electronic apparatus designed to be fed from the mains, battery, or supply apparatus, for reception, generation, recording or reproduction of audio, video and associated signals.",
        "source": "Bureau of Indian Standards",
        "publication_date": "2017-06-15",
        "active": True,
        "clauses": [
            {
                "clause_number": "5",
                "title": "Marking and Operating Instructions",
                "text": "Apparatus shall bear rated voltage, nature of supply, rated power or current, trade name/mark, model identifier, and BIS CRS registration symbol.",
                "page": 5,
            },
            {
                "clause_number": "9",
                "title": "Electric Shock Hazard Under Normal Operating Conditions",
                "text": "Accessible parts shall not be hazardous live. Contact with live conductors through enclosure apertures must be prevented when probed with standard test finger.",
                "page": 9,
            },
            {
                "clause_number": "10",
                "title": "Insulation Requirements",
                "text": "Insulation between mains circuits and accessible conductive parts shall possess dielectric withstand capability not less than 2000 V AC / 50 Hz for 1 minute.",
                "page": 12,
            },
            {
                "clause_number": "14",
                "title": "Components & Battery Safety",
                "text": "Integrated rechargeable lithium-ion battery packs shall comply with IS 16046 (Part 2) / IEC 62133-2 under CRS mandatory scope.",
                "page": 18,
            },
        ],
    },
]


class StandardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.standard_repo = StandardRepository(db)

    async def seed_default_standards(self) -> None:
        """Seeds the database with verified Indian Standards if not already present."""
        for item in VERIFIED_STANDARDS_SEED:
            existing = await self.standard_repo.get_by_id(item["standard_id"], load_clauses=True)
            if not existing:
                clauses_data = item.get("clauses", [])
                standard = Standard(
                    standard_id=item["standard_id"],
                    title=item["title"],
                    version=item["version"],
                    category=item["category"],
                    scope=item["scope"],
                    source=item.get("source"),
                    publication_date=item.get("publication_date"),
                    active=item.get("active", True),
                )
                await self.standard_repo.create_standard(standard)

                for c in clauses_data:
                    clause = StandardClause(
                        standard_id=standard.standard_id,
                        clause_number=c["clause_number"],
                        title=c["title"],
                        text=c["text"],
                        page=c.get("page"),
                    )
                    await self.standard_repo.create_clause(clause)

    async def list_standards(self) -> List[Standard]:
        return await self.standard_repo.get_all(active_only=True)

    async def get_standard(self, standard_id: str) -> Optional[Standard]:
        return await self.standard_repo.get_by_id(standard_id, load_clauses=True)

