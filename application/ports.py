"""
Capa de APLICACIÓN — Puertos (interfaces).

Clean Architecture: la capa de aplicación define los contratos que necesita
del mundo exterior; la infraestructura los IMPLEMENTA. Las dependencias
apuntan siempre hacia adentro (infrastructure -> application -> domain).

Para reemplazar infraestructura (MongoDB -> SQL, pypdf -> otro motor) basta
con crear un nuevo adaptador que implemente el puerto correspondiente y
registrarlo en el composition root (`interfaces/dependencies.py`), sin tocar
ni servicios ni dominio.
"""
from abc import ABC, abstractmethod

from domain.entities import PDF
from domain.pdf_file import PDFFile


class PDFRepositoryPort(ABC):
    """
    Puerto de persistencia. SOLO acceso a datos: ninguna regla de negocio
    (duplicados, validación) vive aquí; pertenecen al servicio de dominio.
    """

    @abstractmethod
    def find_by_checksum(self, checksum: str) -> dict | None:
        """Consulta pura: devuelve el documento con ese checksum o None."""

    @abstractmethod
    def find_all(self) -> list[dict]: ...

    @abstractmethod
    def find_by_id(self, pdf_id: str) -> dict | None: ...

    @abstractmethod
    def save(self, pdf: PDF) -> str:
        """Persiste un nuevo PDF y devuelve su id."""

    @abstractmethod
    def update(self, pdf_id: str, pdf: PDF) -> dict | None: ...

    @abstractmethod
    def delete(self, pdf_id: str) -> bool:
        """True si se eliminó, False si no existía."""


class PDFValidatorPort(ABC):
    """Puerto de validación: opera sobre el value object de dominio `PDFFile`
    (nunca sobre tipos del framework). Lanza `InvalidPDFError` si no cumple."""

    @abstractmethod
    def validate(self, pdf_file: PDFFile) -> None: ...


class PDFTextExtractorPort(ABC):
    """Puerto de extracción de texto (detalle técnico intercambiable)."""

    @abstractmethod
    def extract_text(self, content: bytes) -> str: ...
