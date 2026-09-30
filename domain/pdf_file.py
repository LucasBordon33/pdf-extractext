"""
Capa de DOMINIO — Value Object `PDFFile`.

Este tipo AISLA al dominio del framework web. El adaptador HTTP
(controller) mapea `UploadFile` (FastAPI) a `PDFFile` antes de llamar al
servicio, de modo que la capa de aplicación nunca conoce tipos de Starlette.

Es inmutable: representa "un archivo tal como llegó", con sus bytes y
metadatos relevantes para las reglas de negocio (nombre, tamaño, magic bytes).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PDFFile:
    """Archivo PDF recibido, expresado en términos del dominio."""

    filename: str
    content: bytes

    @classmethod
    def from_upload(cls, filename: str, content: bytes) -> "PDFFile":
        """Factoría usada por los adaptadores para construir el value object
        a partir de los datos crudos del transporte (HTTP, CLI, cola, etc.)."""
        return cls(filename=filename or "", content=content)

    # --- Datos derivados que usan las reglas de negocio -----------------
    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def has_pdf_extension(self) -> bool:
        return self.filename.lower().endswith(".pdf")

    @property
    def has_pdf_magic_bytes(self) -> bool:
        return self.content.startswith(b"%PDF-")
