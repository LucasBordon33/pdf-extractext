"""
INFRAESTRUCTURA — Adaptador de extracción de texto con pypdf.

Implementa `PDFTextExtractorPort`. Detalle técnico reemplazable
(pdfminer, OCR, etc.) sin tocar la capa de aplicación.
"""
from io import BytesIO

from pypdf import PdfReader

from application.ports import PDFTextExtractorPort


class PypdfTextExtractor(PDFTextExtractorPort):
    def extract_text(self, content: bytes) -> str:
        pdf_reader = PdfReader(BytesIO(content))
        return "".join(
            page_text
            for page in pdf_reader.pages
            if (page_text := page.extract_text())
        )
