from typing import Dict, Any
from repositories.database import DatabaseRepository


class PDFService:
    def __init__(self):
        self.db_repository = DatabaseRepository()

    async def process_pdf(self, file) -> Dict[str, Any]:
        content = await file.read()

        extracted_text = self._extract_text(content)

        summary = self._generate_summary(extracted_text)

        document_data = {
            "filename": file.filename,
            "text": extracted_text,
            "summary": summary,
            "status": "processed",
        }

        saved_id = await self.db_repository.save_document(document_data)

        return {
            "document_id": saved_id,
            "filename": file.filename,
            "summary": summary,
            "text_length": len(extracted_text),
        }

    def _extract_text(self, pdf_content: bytes) -> str:
        return "Texto extraído del PDF (implementación pendiente)"

    def _generate_summary(self, text: str) -> str:
        return "Resumen generado por IA (implementación pendiente)"
