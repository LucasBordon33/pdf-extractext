from io import BytesIO

from pypdf import PdfReader

from application.ports import TextExtractorPort


class PypdfTextExtractor(TextExtractorPort):
    def extract_text(self, content: bytes) -> str:
        pdf_reader = PdfReader(BytesIO(content))
        return "".join(
            page_text
            for page in pdf_reader.pages
            if (page_text := page.extract_text())
        )
