"""
Capa de APLICACIÓN — Casos de uso explícitos.

Cada clase representa UNA operación del negocio (Register, Update, List,
Delete), en lugar de un servicio genérico. Esto hace explícito qué puede
hacer el sistema y dónde vive cada regla.

Reglas de negocio (centralizadas aquí, única fuente de verdad):
- El archivo debe ser un PDF válido (puerto `PDFValidatorPort`).
- No puede haber dos PDFs con el mismo checksum (`_ensure_not_duplicate`,
  compartida por Register y Update sin duplicar código).

Independencias: ningún caso de uso importa FastAPI ni MongoDB; reciben
puertos por constructor (Inversión de Dependencias) y trabajan con el
value object de dominio `PDFFile` (los tipos del framework los mapea el
controller).
"""
import hashlib
from dataclasses import dataclass

from application.ports import PDFRepositoryPort, PDFTextExtractorPort, PDFValidatorPort
from domain.entities import PDF
from domain.exceptions import DuplicatePDFError, PDFNotFoundError
from domain.pdf_file import PDFFile


# ----------------------------------------------------------------------
# Reglas de negocio compartidas (únicas fuentes de verdad)
# ----------------------------------------------------------------------
def _ensure_not_duplicate(repository: PDFRepositoryPort, checksum: str) -> None:
    """Regla: no puede existir más de un PDF con el mismo checksum."""
    if repository.find_by_checksum(checksum) is not None:
        raise DuplicatePDFError("El PDF ya se encuentra registrado en la base de datos.")


def _calculate_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ----------------------------------------------------------------------
# Casos de uso
# ----------------------------------------------------------------------
class RegisterPDFUseCase:
    """Caso de uso: registrar un nuevo PDF (validar, verificar duplicado,
    extraer texto y persistir)."""

    def __init__(
        self,
        repository: PDFRepositoryPort,
        validator: PDFValidatorPort,
        text_extractor: PDFTextExtractorPort,
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._text_extractor = text_extractor

    def execute(self, pdf_file: PDFFile) -> dict:
        self._validator.validate(pdf_file)

        checksum = _calculate_checksum(pdf_file.content)
        _ensure_not_duplicate(self._repository, checksum)

        pdf = PDF(
            name=pdf_file.filename,
            text=self._text_extractor.extract_text(pdf_file.content),
            checksum=checksum,
        )
        pdf_id = self._repository.save(pdf)
        return {"id": pdf_id, "filename": pdf.name, "checksum": checksum}


class UpdatePDFUseCase:
    """Caso de uso: actualizar un PDF existente con un nuevo archivo."""

    def __init__(
        self,
        repository: PDFRepositoryPort,
        validator: PDFValidatorPort,
        text_extractor: PDFTextExtractorPort,
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._text_extractor = text_extractor

    def execute(self, pdf_id: str, pdf_file: PDFFile) -> dict:
        # Único chequeo de existencia (antes estaba duplicado controller/repo).
        if self._repository.find_by_id(pdf_id) is None:
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")

        self._validator.validate(pdf_file)

        checksum = _calculate_checksum(pdf_file.content)
        _ensure_not_duplicate(self._repository, checksum)

        pdf = PDF(
            name=pdf_file.filename,
            text=self._text_extractor.extract_text(pdf_file.content),
            checksum=checksum,
        )
        updated = self._repository.update(pdf_id, pdf)
        if updated is None:
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")
        return updated


class ListPDFsUseCase:
    """Caso de uso: listar todos los PDFs registrados."""

    def __init__(self, repository: PDFRepositoryPort) -> None:
        self._repository = repository

    def execute(self) -> list[dict]:
        return self._repository.find_all()


class DeletePDFUseCase:
    """Caso de uso: eliminar un PDF por id."""

    def __init__(self, repository: PDFRepositoryPort) -> None:
        self._repository = repository

    def execute(self, pdf_id: str) -> None:
        if not self._repository.delete(pdf_id):
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")


@dataclass(frozen=True)
class PDFUseCases:
    """Bundle de casos de uso: permite inyectar UNA sola dependencia en el
    controller y añadir casos de uso futuros sin cambiar firmas."""
    register: RegisterPDFUseCase
    update: UpdatePDFUseCase
    list_all: ListPDFsUseCase
    delete: DeletePDFUseCase
