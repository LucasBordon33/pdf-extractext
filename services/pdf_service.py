from pypdf import PdfReader
from io import BytesIO
from typing import Dict, Any
from repositories.pdf_repository import PDFRepository
from models.pdf import PDF
import hashlib



"""

Servicio que maneja la lógica del negocio

"""

class PDFService:
    def __init__(self):
        self.repository = PDFRepository()

    async def process_pdf(self, file) -> Dict[str, Any]:
        content = await file.read()

        checksum = self.calculate_checksum(content)

        extracted_text = self._extract_text_from_pdf_stream(content)

        return {"filename": file.filename, "text": extracted_text, "checksum": checksum}

    def calculate_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _extract_text_from_pdf_stream(self, pdf_content: bytes) -> str:
        pdf_stream = BytesIO(pdf_content)
        pdf_reader = PdfReader(pdf_stream)
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text
        return extracted_text
