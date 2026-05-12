from pypdf import PdfReader
from io import BytesIO
from typing import Optional


class PDFService:

    def __init__(self):
        pass

    def _extract_text_from_pdf_stream(self, pdf_content: bytes) -> str:
        
        pdf_stream = BytesIO(pdf_content)
        pdf_reader = PdfReader(pdf_stream)

        extracted_text = self._process_all_pages(pdf_reader)
        return extracted_text

    def _process_all_pages(self, pdf_reader: PdfReader) -> str:
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text

        return extracted_text

    async def export_text_content(self, text: str, filename: str):
        ##todavia no se hace
        pass
