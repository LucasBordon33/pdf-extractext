import hashlib
from dataclasses import dataclass

from application.ports import (
    ReaderPort,
    TextExtractorPort,
    ValidatorPort,
    WriterPort,
)
from domain.entities import PDF
from domain.exceptions import DuplicatePDFError, PDFNotFoundError
from domain.pdf_file import PDFFile


# ----------------------------------------------------------------------
# Reglas de negocio compartidas (únicas fuentes de verdad)
# ----------------------------------------------------------------------
def _ensure_not_duplicate(reader: ReaderPort, checksum: str) -> None:
    """Regla: no puede existir más de un PDF con el mismo checksum."""
    if reader.find_by_checksum(checksum) is not None:
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
        reader: ReaderPort,
        writer: WriterPort,
        validator: ValidatorPort,
        text_extractor: TextExtractorPort,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._validator = validator
        self._text_extractor = text_extractor

    def execute(self, pdf_file: PDFFile) -> dict:
        self._validator.validate(pdf_file)

        checksum = _calculate_checksum(pdf_file.content)
        _ensure_not_duplicate(self._reader, checksum)

        pdf = PDF(
            name=pdf_file.filename,
            text=self._text_extractor.extract_text(pdf_file.content),
            checksum=checksum,
        )
        pdf_id = self._writer.save(pdf)
        return {"id": pdf_id, "filename": pdf.name, "checksum": checksum}


class UpdatePDFUseCase:
    """Caso de uso: actualizar un PDF existente con un nuevo archivo."""

    def __init__(
        self,
        reader: ReaderPort,
        writer: WriterPort,
        validator: ValidatorPort,
        text_extractor: TextExtractorPort,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._validator = validator
        self._text_extractor = text_extractor

    def execute(self, pdf_id: str, pdf_file: PDFFile) -> dict:
        self._validator.validate(pdf_file)

        checksum = _calculate_checksum(pdf_file.content)
        _ensure_not_duplicate(self._reader, checksum)

        pdf = PDF(
            name=pdf_file.filename,
            text=self._text_extractor.extract_text(pdf_file.content),
            checksum=checksum,
        )
        # Único chequeo de existencia: surge del resultado de la actualización,
        # lo que evita duplicar la regla y es seguro ante carreras.
        updated = self._writer.update(pdf_id, pdf)
        if updated is None:
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")
        return updated


class GetPDFByIdUseCase:
    """Caso de uso: obtener un PDF por su id (solo lectura)."""

    def __init__(self, reader: ReaderPort) -> None:
        self._reader = reader

    def execute(self, pdf_id: str) -> dict:
        pdf = self._reader.find_by_id(pdf_id)
        if pdf is None:
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")
        return pdf


class ListPDFsUseCase:
    """Caso de uso: listar todos los PDFs registrados (solo lectura)."""

    def __init__(self, reader: ReaderPort) -> None:
        self._reader = reader

    def execute(self) -> list[dict]:
        return self._reader.find_all()


class DeletePDFUseCase:
    """Caso de uso: eliminar un PDF por id (solo escritura)."""

    def __init__(self, writer: WriterPort) -> None:
        self._writer = writer

    def execute(self, pdf_id: str) -> None:
        if not self._writer.delete(pdf_id):
            raise PDFNotFoundError(f"El PDF con id '{pdf_id}' no existe")


@dataclass(frozen=True)
class PDFUseCases:
    """Bundle de casos de uso: permite inyectar UNA sola dependencia en el
    controller y añadir casos de uso futuros sin cambiar firmas."""
    register: RegisterPDFUseCase
    update: UpdatePDFUseCase
    get_by_id: GetPDFByIdUseCase
    list_all: ListPDFsUseCase
    delete: DeletePDFUseCase
