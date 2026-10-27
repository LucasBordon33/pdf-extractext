"""
Tests unitarios del seam CASOS DE USO / DOMINIO (ver CONTEXT.md §1, seam 2).

Reglas de negocio de la capa de aplicación con dobles que respetan los
puertos (`MagicMock(spec=...)`): persistencia, validación y extracción
quedan sustituidas. Nunca se toca MongoDB real.

El checksum esperado se calcula en el test a partir de un contenido
conocido: aserción contra un oráculo independiente, no contra el
propio código bajo prueba.
"""
import hashlib
from unittest.mock import MagicMock

import pytest

from application.ports import (
    PDFRepositoryPort,
    PDFTextExtractorPort,
    PDFValidatorPort,
)
from application.use_cases import (
    DeletePDFUseCase,
    ListPDFsUseCase,
    RegisterPDFUseCase,
    UpdatePDFUseCase,
)
from domain.entities import PDF
from domain.exceptions import DuplicatePDFError, InvalidPDFError, PDFNotFoundError
from domain.pdf_file import PDFFile

CONTENT = b"%PDF-1.4 contenido conocido del test"
CHECKSUM = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture()
def mock_repo():
    return MagicMock(spec=PDFRepositoryPort)


@pytest.fixture()
def mock_validator():
    return MagicMock(spec=PDFValidatorPort)


@pytest.fixture()
def mock_extractor():
    extractor = MagicMock(spec=PDFTextExtractorPort)
    extractor.extract_text.return_value = "texto extraido"
    return extractor


@pytest.fixture()
def pdf_file():
    return PDFFile.from_upload("doc.pdf", CONTENT)


# --- RegisterPDFUseCase ----------------------------------------------------

def test_register_camino_feliz_persiste_y_responde(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_repo.find_by_checksum.return_value = None
    mock_repo.save.return_value = "pdf-1"

    result = RegisterPDFUseCase(mock_repo, mock_validator, mock_extractor).execute(
        pdf_file
    )

    mock_validator.validate.assert_called_once_with(pdf_file)
    mock_repo.save.assert_called_once()
    saved = mock_repo.save.call_args[0][0]
    assert isinstance(saved, PDF)
    assert saved.name == "doc.pdf"
    assert saved.text == "texto extraido"
    assert saved.checksum == CHECKSUM
    assert result == {"id": "pdf-1", "filename": "doc.pdf", "checksum": CHECKSUM}


def test_register_archivo_invalido_no_persiste(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_validator.validate.side_effect = InvalidPDFError("Solo se permiten archivos PDF")

    with pytest.raises(InvalidPDFError):
        RegisterPDFUseCase(mock_repo, mock_validator, mock_extractor).execute(pdf_file)

    mock_repo.save.assert_not_called()


def test_register_duplicado_no_persiste(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_repo.find_by_checksum.return_value = {"id": "otro", "checksum": CHECKSUM}

    with pytest.raises(DuplicatePDFError):
        RegisterPDFUseCase(mock_repo, mock_validator, mock_extractor).execute(pdf_file)

    mock_repo.save.assert_not_called()


# --- UpdatePDFUseCase --------------------------------------------------------

def test_update_camino_feliz_actualiza_y_responde(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_repo.find_by_checksum.return_value = None
    mock_repo.update.return_value = {
        "id": "pdf-1",
        "name": "doc.pdf",
        "text": "texto extraido",
        "checksum": CHECKSUM,
    }

    result = UpdatePDFUseCase(mock_repo, mock_validator, mock_extractor).execute(
        "pdf-1", pdf_file
    )

    pdf_id, saved = mock_repo.update.call_args[0]
    assert pdf_id == "pdf-1"
    assert isinstance(saved, PDF)
    assert saved.checksum == CHECKSUM
    assert result["id"] == "pdf-1"
    assert result["checksum"] == CHECKSUM


def test_update_inexistente_da_not_found(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    # El único chequeo de existencia surge del resultado de la mutación.
    mock_repo.find_by_checksum.return_value = None
    mock_repo.update.return_value = None

    with pytest.raises(PDFNotFoundError):
        UpdatePDFUseCase(mock_repo, mock_validator, mock_extractor).execute(
            "pdf-1", pdf_file
        )


def test_update_duplicado_no_actualiza(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_repo.find_by_checksum.return_value = {"id": "otro", "checksum": CHECKSUM}

    with pytest.raises(DuplicatePDFError):
        UpdatePDFUseCase(mock_repo, mock_validator, mock_extractor).execute(
            "pdf-1", pdf_file
        )

    mock_repo.update.assert_not_called()


def test_update_archivo_invalido_no_actualiza(
    mock_repo, mock_validator, mock_extractor, pdf_file
):
    mock_validator.validate.side_effect = InvalidPDFError("El archivo no es un PDF válido")

    with pytest.raises(InvalidPDFError):
        UpdatePDFUseCase(mock_repo, mock_validator, mock_extractor).execute(
            "pdf-1", pdf_file
        )

    mock_repo.update.assert_not_called()


# --- ListPDFsUseCase -------------------------------------------------------

def test_list_devuelve_los_read_models_del_puerto(mock_repo):
    docs = [{"id": "1", "name": "a.pdf", "text": "t", "checksum": "x"}]
    mock_repo.find_all.return_value = docs

    result = ListPDFsUseCase(mock_repo).execute()

    mock_repo.find_all.assert_called_once_with()
    assert result == docs


# --- DeletePDFUseCase ------------------------------------------------------

def test_delete_camino_feliz(mock_repo):
    mock_repo.delete.return_value = True

    DeletePDFUseCase(mock_repo).execute("pdf-1")

    mock_repo.delete.assert_called_once_with("pdf-1")


def test_delete_inexistente_da_not_found(mock_repo):
    mock_repo.delete.return_value = False

    with pytest.raises(PDFNotFoundError):
        DeletePDFUseCase(mock_repo).execute("pdf-1")
