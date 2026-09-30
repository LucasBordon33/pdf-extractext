"""
INFRAESTRUCTURA — Adaptador de validación de PDFs.

Implementa `PDFValidatorPort` operando sobre el value object de dominio
`PDFFile` (no sobre `UploadFile`): el framework queda completamente fuera.
Comunica los fallos con la excepción de dominio `InvalidPDFError`.
"""
import os

from application.ports import PDFValidatorPort
from domain.exceptions import InvalidPDFError
from domain.pdf_file import PDFFile


class FileFormatPDFValidator(PDFValidatorPort):
    def __init__(self, max_size_mb: int | None = None) -> None:
        mb = max_size_mb or int(os.getenv("MX_FILE_SIZE", "10"))
        self._max_size = mb * 1024 * 1024

    def validate(self, pdf_file: PDFFile) -> None:
        if not pdf_file.has_pdf_extension:
            raise InvalidPDFError("Solo se permiten archivos PDF")
        if not pdf_file.has_pdf_magic_bytes:
            raise InvalidPDFError("El archivo no es un PDF válido")
        if pdf_file.size > self._max_size:
            raise InvalidPDFError("El archivo excede el tamaño permitido")
