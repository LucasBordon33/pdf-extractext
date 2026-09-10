import os

from config.exceptions import PDFNotValidException


class PDFValidator:
    def __init__(self):
        self.valid_size = int(os.getenv("MX_FILE_SIZE", "10")) * 1024 * 1024

    async def validate_is_pdf(self, file):
        if not file.filename.lower().endswith(".pdf"):
            raise PDFNotValidException("Solo se permiten archivos PDF")

        file_header = await file.read(5)
        await file.seek(0)

        if not file_header.startswith(b"%PDF-"):
            raise PDFNotValidException("El archivo no es un PDF válido")

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > self.valid_size:
            raise PDFNotValidException("El archivo excede el tamaño permitido")
