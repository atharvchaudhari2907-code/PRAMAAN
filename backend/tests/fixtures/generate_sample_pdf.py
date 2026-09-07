"""
Generates a valid, well-formed PDF file containing realistic 9W LED lamp technical specifications.
Can be parsed by pypdf without warnings.
"""
import os
from pathlib import Path


def generate_led_datasheet_pdf(output_path: str):
    content_lines = [
        "LUMENSTAR LIGHTING TECHNOLOGIES PVT LTD",
        "PRODUCT TECHNICAL SPECIFICATION FILE & COMPLIANCE DOSSIER",
        "",
        "PRODUCT: 9W Self-Ballasted LED Lamp for General Lighting",
        "MODEL DESIGNATION: LMN-LED-09W-B22",
        "MANUFACTURER: LumenStar Lighting Technologies Pvt Ltd",
        "FACILITY ADDRESS: Industrial Sector 62, Phase 3, Noida, Uttar Pradesh 201301",
        "",
        "ELECTRICAL & POWER CHARACTERISTICS:",
        "- Rated Wattage: 9W (Tolerance: 9.0 W nominal, 230 V AC)",
        "- Rated Voltage: 230 V AC (Operating Range: 100 - 300 V AC, 50 Hz)",
        "- Power Factor: 0.92 (Nominal active PF)",
        "- Total Harmonic Distortion (THD): 24.5% (Mains input current distortion)",
        "- Driver Efficiency: 88.5% Constant-Current isolated IC topology",
        "",
        "OPTICAL & PHOTOMETRIC PERFORMANCE:",
        "- Luminous Efficacy: 78 lm/W (Total initial luminous flux: 702 lumens)",
        "- Color Rendering Index (CRI): 82 Ra",
        "- Correlated Color Temperature (CCT): 6500 K (Cool Daylight)",
        "- Beam Angle: 220 Degrees Omni-directional",
        "",
        "MECHANICAL & SAFETY CHARACTERISTICS:",
        "- Lamp Cap Fitment: B22d Standard Bayonet Cap (conforming to IS 16102)",
        "- Torsion Resistance: 3.2 Nm axial torque withstand without cap loosening",
        "- Insulation Resistance: 5.2 M-Ohm tested at 500 V DC between live and accessible parts",
        "- Electric Shock Protection: IP20 Enclosure with ultrasonic polycarbonate welding",
        "- Marking: English product label artwork; bilingual Hindi carton marking pending",
        "",
        "END OF TECHNICAL SPECIFICATION SHEET"
    ]

    text_commands = ["BT", "/F1 11 Tf", "40 760 Td", "15 TL"]
    for line in content_lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if safe_line:
            text_commands.append(f"({safe_line}) '")
        else:
            text_commands.append("T*")
    text_commands.append("ET")

    stream_data = "\n".join(text_commands).encode("latin-1")
    stream_len = len(stream_data)

    parts = []
    parts.append(b"%PDF-1.4\n")
    
    offsets = []
    offsets.append(0)  # object 0 dummy

    # obj 1: Catalog
    offsets.append(sum(len(p) for p in parts))
    parts.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # obj 2: Pages
    offsets.append(sum(len(p) for p in parts))
    parts.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # obj 3: Page
    offsets.append(sum(len(p) for p in parts))
    parts.append(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\n"
        b"endobj\n"
    )

    # obj 4: Content stream
    offsets.append(sum(len(p) for p in parts))
    parts.append(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("ascii"))
    parts.append(stream_data)
    parts.append(b"\nendstream\nendobj\n")

    # xref
    xref_offset = sum(len(p) for p in parts)
    xref_lines = [b"xref\n0 5\n0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref_lines.append(f"{off:010d} 00000 n \n".encode("ascii"))
    parts.extend(xref_lines)

    trailer = f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    parts.append(trailer)

    full_pdf = b"".join(parts)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(full_pdf)
    print(f"Clean PDF generated at {output_path} ({len(full_pdf)} bytes)")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "sample_led_datasheet.pdf"
    generate_led_datasheet_pdf(str(out))
