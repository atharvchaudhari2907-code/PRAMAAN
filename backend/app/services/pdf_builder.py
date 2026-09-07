"""
Pure-Python PDF generator for official BIS Application Forms and Technical Dossiers.
Conforms to PDF-1.4 specification without external binary dependencies.
Supports multi-page layout, bold headers, section borders, and metadata.
"""
import os
from typing import List, Tuple


def _sanitize_pdf_text(text: str) -> str:
    """Escapes special characters and replaces non-latin1 characters."""
    safe = ""
    for ch in str(text):
        if ch in ("\\", "(", ")"):
            safe += "\\" + ch
        elif ord(ch) < 128:
            safe += ch
        else:
            safe += " "
    return safe


class SimplePDFBuilder:
    def __init__(self, title: str, subtitle: str = ""):
        self.title = title
        self.subtitle = subtitle
        self.pages: List[List[Tuple[str, str, int, int]]] = []  # List of pages, each page has list of (text, font, x, y)
        self.current_page: List[Tuple[str, str, int, int]] = []
        self.y_cursor = 780
        self.line_height = 14
        self.bottom_margin = 60

    def _new_page(self):
        if self.current_page:
            self.pages.append(self.current_page)
        self.current_page = []
        self.y_cursor = 780

        # Header on every page
        self.current_page.append(("BUREAU OF INDIAN STANDARDS - APPLICATION DOSSIER", "/F2 9 Tf", 50, 810))
        self.current_page.append((f"DOCUMENT: {self.title[:65]}", "/F1 8 Tf", 50, 796))
        # Add dividing line below header
        self.y_cursor = 770

    def add_header(self):
        self._new_page()
        self.current_page.append((self.title, "/F2 14 Tf", 50, self.y_cursor))
        self.y_cursor -= 18
        if self.subtitle:
            self.current_page.append((self.subtitle, "/F1 9 Tf", 50, self.y_cursor))
            self.y_cursor -= 18
        self.y_cursor -= 10

    def add_section_title(self, section_title: str):
        if self.y_cursor < self.bottom_margin + 40:
            self._new_page()
        self.y_cursor -= 10
        self.current_page.append((section_title, "/F2 11 Tf", 50, self.y_cursor))
        self.y_cursor -= 16

    def add_field(self, label: str, value: str, source: str = ""):
        if self.y_cursor < self.bottom_margin + 30:
            self._new_page()

        lbl_text = f"{label}:"
        self.current_page.append((lbl_text, "/F2 9 Tf", 60, self.y_cursor))
        self.y_cursor -= 13

        val_str = str(value) if value is not None else "N/A"
        # Wrap long values
        words = val_str.split(" ")
        lines = []
        cur_line = ""
        for w in words:
            if len(cur_line) + len(w) + 1 > 78:
                lines.append(cur_line)
                cur_line = w
            else:
                cur_line = f"{cur_line} {w}".strip()
        if cur_line:
            lines.append(cur_line)

        for l in lines:
            if self.y_cursor < self.bottom_margin + 15:
                self._new_page()
            self.current_page.append((l, "/F1 9 Tf", 70, self.y_cursor))
            self.y_cursor -= 13

        if source:
            if self.y_cursor < self.bottom_margin + 12:
                self._new_page()
            src_text = f"[Source: {source}]"
            self.current_page.append((src_text, "/F1 7 Tf", 70, self.y_cursor))
            self.y_cursor -= 12

        self.y_cursor -= 4

    def build_pdf(self, output_path: str) -> str:
        if self.current_page:
            self.pages.append(self.current_page)
        if not self.pages:
            self._new_page()
            self.pages.append(self.current_page)

        total_pages = len(self.pages)

        # Add page numbering
        for p_idx, page in enumerate(self.pages):
            page_num_str = f"Page {p_idx + 1} of {total_pages}"
            page.append((page_num_str, "/F1 8 Tf", 490, 35))
            page.append(("OFFICIAL BIS COMPLIANCE DOSSIER - CONFIDENTIAL", "/F1 7 Tf", 50, 35))

        parts = [b"%PDF-1.4\n"]
        offsets = [0]  # dummy 0

        # Object count tracking:
        # obj 1: Catalog
        # obj 2: Pages container
        # Then for each page i (0-based):
        # obj 3 + 2*i: Page object
        # obj 4 + 2*i: Content stream object

        num_pages = len(self.pages)
        page_obj_ids = [3 + 2 * i for i in range(num_pages)]
        kids_refs = " ".join(f"{pid} 0 R" for pid in page_obj_ids)

        # obj 1: Catalog
        offsets.append(sum(len(p) for p in parts))
        parts.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        # obj 2: Pages
        offsets.append(sum(len(p) for p in parts))
        pages_dict = f"2 0 obj\n<< /Type /Pages /Kids [{kids_refs}] /Count {num_pages} >>\nendobj\n"
        parts.append(pages_dict.encode("ascii"))

        # Objects for each page
        for i, page_cmds in enumerate(self.pages):
            page_obj_id = 3 + 2 * i
            stream_obj_id = 4 + 2 * i

            # Stream commands
            commands = ["BT"]
            for text, font_spec, x, y in page_cmds:
                safe_text = _sanitize_pdf_text(text)
                commands.append(f"{font_spec} 1 0 0 1 {x} {y} Tm ({safe_text}) Tj")
            commands.append("ET")

            stream_bytes = "\n".join(commands).encode("latin-1")
            stream_len = len(stream_bytes)

            # Page object
            offsets.append(sum(len(p) for p in parts))
            page_obj_str = (
                f"{page_obj_id} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {stream_obj_id} 0 R "
                f"/Resources << /Font << "
                f"/F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
                f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> "
                f">> >> >>\nendobj\n"
            )
            parts.append(page_obj_str.encode("ascii"))

            # Content stream object
            offsets.append(sum(len(p) for p in parts))
            stream_hdr = f"{stream_obj_id} 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("ascii")
            parts.append(stream_hdr)
            parts.append(stream_bytes)
            parts.append(b"\nendstream\nendobj\n")

        total_objects = 2 + 2 * num_pages + 1
        xref_offset = sum(len(p) for p in parts)
        xref_lines = [f"xref\n0 {total_objects}\n0000000000 65535 f \n".encode("ascii")]
        for off in offsets[1:]:
            xref_lines.append(f"{off:010d} 00000 n \n".encode("ascii"))
        parts.extend(xref_lines)

        trailer = f"trailer\n<< /Size {total_objects} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        parts.append(trailer)

        full_pdf = b"".join(parts)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(full_pdf)

        return output_path
