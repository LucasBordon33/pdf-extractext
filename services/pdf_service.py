from pypdf import PdfReader
from io import BytesIO
from typing import Dict, Any
from models.pdf import PDF
from repositories.pdf_repository import PDFRepository
from config.settings import get_db
from config.constants import (
    PDF_REPEATED,
    PDF_UPLOADED,
    PDF_UPDATED,
    PDF_NOT_FOUND,
    PDF_PROCESS_ERROR,
)
from config.exceptions import PDFRejectedException, PDFNotFoundException
import hashlib


class PDFService:
    def __init__(self, repository=None):
        self.repository = repository or PDFRepository(get_db())

    async def upload_pdf(self, file) -> dict:
        content = await file.read()
        checksum = self.calculate_checksum(content)
        extracted_text = self._extract_text_from_pdf_stream(content)
        pdf_data = PDF(name=file.filename, text=extracted_text, checksum=checksum)

        if self.is_duplicate(pdf_data.checksum):
            raise PDFRejectedException(PDF_REPEATED)

        pdf_id = self.repository.create_pdf(pdf_data)
        return {
            "status": "success",
            "id": pdf_id,
            "filename": file.filename,
            "checksum": checksum,
            "message": PDF_UPLOADED,
        }

    async def update_pdf(self, pdf_id: str, file) -> dict:
        content = await file.read()
        checksum = self.calculate_checksum(content)
        extracted_text = self._extract_text_from_pdf_stream(content)
        pdf_data = PDF(name=file.filename, text=extracted_text, checksum=checksum)

        if self.is_duplicate(pdf_data.checksum):
            raise PDFRejectedException(PDF_REPEATED)

        updated = self.repository.update_pdf(pdf_id, pdf_data)
        return {
            "status": "success",
            "id": pdf_id,
            "filename": file.filename,
            "checksum": checksum,
            "message": PDF_UPDATED,
        }

    def is_duplicate(self, checksum: str) -> bool:
        return self.repository.find_by_checksum(checksum) is not None

    def calculate_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _extract_text_from_pdf_stream(self, pdf_content: bytes) -> str:
        try:
            pdf_stream = BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_stream)
            extracted_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text
            return extracted_text
        except Exception:
            raise ValueError("No se pudo leer el archivo como PDF")
