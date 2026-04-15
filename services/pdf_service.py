from pypdf import PdfReader
import io

class PDFService:
    def __init__(self):
        pass

    def extract_text(self, pdf_content: bytes) -> str:
        text = ""
        ## Buffer para los bytes y con PdfReader transformo las páginas a un string
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        for page in reader.pages:
                text += page.extract_text() or ""
        return text

    def export_text():
         pass

    def _generate_summary(self, text: str) -> str:
        return "Resumen generado por IA (implementación pendiente)"
