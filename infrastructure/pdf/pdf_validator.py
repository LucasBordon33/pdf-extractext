"""
INFRAESTRUCTURA — Adaptador de validación de PDFs (patrón Estrategia).

Implementa `PDFValidatorPort` operando sobre el value object de dominio
`PDFFile` (no sobre `UploadFile`): el framework queda completamente fuera.
Comunica los fallos con la excepción de dominio `InvalidPDFError`.

OCP: cada regla de formato es una estrategia atómica e inyectable (clase
`PDFValidationRule`). `validate` es CERRADO a modificación: agregar una
regla nueva = escribir una clase de regla y sumarla a la lista por
defecto, o inyectar la lista por constructor, sin tocar el método
principal.
"""
import os
from abc import ABC, abstractmethod

from application.ports import PDFValidatorPort
from domain.exceptions import InvalidPDFError
from domain.pdf_file import PDFFile


class PDFValidationRule(ABC):
    """Regla de validación atómica sobre un `PDFFile` de dominio."""

    @abstractmethod
    def check(self, pdf_file: PDFFile) -> None:
        """Lanza `InvalidPDFError` si la regla se viola."""


class HasPDFExtension(PDFValidationRule):
    """Regla: el nombre del archivo debe terminar en `.pdf`."""

    def check(self, pdf_file: PDFFile) -> None:
        if not pdf_file.has_pdf_extension:
            raise InvalidPDFError("Solo se permiten archivos PDF")


class HasPDFMagicBytes(PDFValidationRule):
    """Regla: el contenido debe comenzar con la firma `%PDF-`."""

    def check(self, pdf_file: PDFFile) -> None:
        if not pdf_file.has_pdf_magic_bytes:
            raise InvalidPDFError("El archivo no es un PDF válido")


class MaxFileSize(PDFValidationRule):
    """Regla: el contenido no puede superar el tamaño máximo configurado."""

    def __init__(self, max_size_mb: int | None = None) -> None:
        mb = max_size_mb or int(os.getenv("MX_FILE_SIZE", "10"))
        self._max_size = mb * 1024 * 1024

    def check(self, pdf_file: PDFFile) -> None:
        if pdf_file.size > self._max_size:
            raise InvalidPDFError("El archivo excede el tamaño permitido")


class FileFormatPDFValidator(PDFValidatorPort):
    """Validador compuesto: recorre las reglas inyectadas en orden y lanza
    `InvalidPDFError` en la primera que no se cumpla."""

    def __init__(self, rules: list[PDFValidationRule] | None = None) -> None:
        self._rules = rules if rules is not None else [
            HasPDFExtension(),
            HasPDFMagicBytes(),
            MaxFileSize(),
        ]

    def validate(self, pdf_file: PDFFile) -> None:
        for rule in self._rules:
            rule.check(pdf_file)
