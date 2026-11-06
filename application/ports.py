from abc import ABC, abstractmethod
from domain.entities import PDF
from domain.pdf_file import PDFFile


class ReaderPort(ABC):
    """
    Puerto de LECTURA. Solo para los casos de uso que
    leen datos.
    """

    @abstractmethod
    def find_by_checksum(self, checksum: str) -> dict | None:
        """Consulta pura: devuelve el documento con ese checksum o None."""

    @abstractmethod
    def find_all(self) -> list[dict]: ...

    @abstractmethod
    def find_by_id(self, pdf_id: str) -> dict | None: ...


class WriterPort(ABC):
    """
    Puerto de ESCRITURA. Solo para los casos de uso que
    escriben datos.
    """

    @abstractmethod
    def save(self, pdf: PDF) -> str:
        """Persiste un nuevo PDF y devuelve su id."""

    @abstractmethod
    def update(self, pdf_id: str, pdf: PDF) -> dict | None: ...

    @abstractmethod
    def delete(self, pdf_id: str) -> bool:
        """True si se eliminó, False si no existía."""


class ValidatorPort(ABC):
    """Puerto de validación: opera sobre el value object de dominio `PDFFile`
    (nunca sobre tipos del framework). Lanza `InvalidPDFError` si no cumple."""

    @abstractmethod
    def validate(self, pdf_file: PDFFile) -> None: ...


class TextExtractorPort(ABC):
    """Puerto de extracción de texto (detalle técnico intercambiable)."""

    @abstractmethod
    def extract_text(self, content: bytes) -> str: ...
