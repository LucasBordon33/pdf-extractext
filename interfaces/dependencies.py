from application.use_cases import (
    DeletePDFUseCase,
    GetPDFByIdUseCase,
    ListPDFsUseCase,
    PDFUseCases,
    RegisterPDFUseCase,
    UpdatePDFUseCase,
)
from config.settings import get_db
from infrastructure.persistence.mongo_pdf_repository import MongoPDFRepository
from infrastructure.pdf.pdf_validator import FileFormatPDFValidator
from infrastructure.pdf.pypdf_text_extractor import PypdfTextExtractor
from interfaces.controllers.pdf_controller import PDFController


def get_pdf_repository() -> MongoPDFRepository:
    return MongoPDFRepository(get_db())  # conexión diferida, no al importar


def get_pdf_validator() -> FileFormatPDFValidator:
    return FileFormatPDFValidator()


def get_text_extractor() -> PypdfTextExtractor:
    return PypdfTextExtractor()


def get_pdf_use_cases() -> PDFUseCases:
    """Compone los casos de uso inyectando los adaptadores concretos.
    """
    repository = get_pdf_repository()
    validator = get_pdf_validator()
    extractor = get_text_extractor()
    return PDFUseCases(
        register=RegisterPDFUseCase(repository, repository, validator, extractor),
        update=UpdatePDFUseCase(repository, repository, validator, extractor),
        get_by_id=GetPDFByIdUseCase(repository),
        list_all=ListPDFsUseCase(repository),
        delete=DeletePDFUseCase(repository),
    )


def get_pdf_controller() -> PDFController:
    """Fábrica del controller, usada por FastAPI con Depends()."""
    return PDFController(use_cases=get_pdf_use_cases())
