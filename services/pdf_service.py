from pypdf import PdfReader
from io import BytesIO

class PDFService:
    def __init__(self):
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB por ejemplo

    def _extract_text_from_pdf_stream(self, pdf_content: bytes) -> str:
        # 1. Comprobación de tamaño
        if len(pdf_content) > self.MAX_FILE_SIZE:
            raise ValueError("El archivo excede el tamaño máximo permitido (10MB)")

        try:
            pdf_stream = BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_stream)
            
            if len(pdf_reader.pages) == 0:
                raise ValueError("El PDF parece estar vacío o corrupto")
                
            if pdf_reader.is_encrypted:
                raise ValueError("El PDF está protegido con contraseña y no se puede procesar")

            extracted_text = self._process_all_pages(pdf_reader)
            return extracted_text

        except Exception as e:
            if not isinstance(e, ValueError):
                raise ValueError(f"No se pudo leer el archivo como PDF: {str(e)}")
            raise e

    def _process_all_pages(self, pdf_reader: PdfReader) -> str:
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text
        return extracted_text