import hashlib
from unittest.mock import MagicMock

import pytest

from application.ports import (
    ReaderPort,
    TextExtractorPort,
    ValidatorPort,
    WriterPort,
)
from application.use_cases import (
    DeletePDFUseCase,
    GetPDFByIdUseCase,
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
def mock_reader():
    return MagicMock(spec=ReaderPort)


@pytest.fixture()
def mock_writer():
    return MagicMock(spec=WriterPort)


@pytest.fixture()
def mock_validator():
    return MagicMock(spec=ValidatorPort)


@pytest.fixture()
def mock_extractor():
    extractor = MagicMock(spec=TextExtractorPort)
    extractor.extract_text.return_value = "texto extraido"
    return extractor


@pytest.fixture()
def pdf_file():
    return PDFFile.from_upload("doc.pdf", CONTENT)


# --- RegisterPDFUseCase ----------------------------------------------------

def test_register_camino_feliz_persiste_y_responde(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_reader.find_by_checksum.return_value = None
    mock_writer.save.return_value = "pdf-1"

    result = RegisterPDFUseCase(
        mock_reader, mock_writer, mock_validator, mock_extractor
    ).execute(pdf_file)

    mock_validator.validate.assert_called_once_with(pdf_file)
    mock_writer.save.assert_called_once()
    saved = mock_writer.save.call_args[0][0]
    assert isinstance(saved, PDF)
    assert saved.name == "doc.pdf"
    assert saved.text == "texto extraido"
    assert saved.checksum == CHECKSUM
    assert result == {"id": "pdf-1", "filename": "doc.pdf", "checksum": CHECKSUM}


def test_register_archivo_invalido_no_persiste(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_validator.validate.side_effect = InvalidPDFError("Solo se permiten archivos PDF")

    with pytest.raises(InvalidPDFError):
        RegisterPDFUseCase(
            mock_reader, mock_writer, mock_validator, mock_extractor
        ).execute(pdf_file)

    mock_writer.save.assert_not_called()


def test_register_duplicado_no_persiste(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_reader.find_by_checksum.return_value = {"id": "otro", "checksum": CHECKSUM}

    with pytest.raises(DuplicatePDFError):
        RegisterPDFUseCase(
            mock_reader, mock_writer, mock_validator, mock_extractor
        ).execute(pdf_file)

    mock_writer.save.assert_not_called()


# --- UpdatePDFUseCase --------------------------------------------------------

def test_update_camino_feliz_actualiza_y_responde(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_reader.find_by_checksum.return_value = None
    mock_writer.update.return_value = {
        "id": "pdf-1",
        "name": "doc.pdf",
        "text": "texto extraido",
        "checksum": CHECKSUM,
    }

    result = UpdatePDFUseCase(
        mock_reader, mock_writer, mock_validator, mock_extractor
    ).execute("pdf-1", pdf_file)

    pdf_id, saved = mock_writer.update.call_args[0]
    assert pdf_id == "pdf-1"
    assert isinstance(saved, PDF)
    assert saved.checksum == CHECKSUM
    assert result["id"] == "pdf-1"
    assert result["checksum"] == CHECKSUM


def test_update_inexistente_da_not_found(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    # El único chequeo de existencia surge del resultado de la mutación.
    mock_reader.find_by_checksum.return_value = None
    mock_writer.update.return_value = None

    with pytest.raises(PDFNotFoundError):
        UpdatePDFUseCase(
            mock_reader, mock_writer, mock_validator, mock_extractor
        ).execute("pdf-1", pdf_file)


def test_update_duplicado_no_actualiza(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_reader.find_by_checksum.return_value = {"id": "otro", "checksum": CHECKSUM}

    with pytest.raises(DuplicatePDFError):
        UpdatePDFUseCase(
            mock_reader, mock_writer, mock_validator, mock_extractor
        ).execute("pdf-1", pdf_file)

    mock_writer.update.assert_not_called()


def test_update_archivo_invalido_no_actualiza(
    mock_reader, mock_writer, mock_validator, mock_extractor, pdf_file
):
    mock_validator.validate.side_effect = InvalidPDFError("El archivo no es un PDF válido")

    with pytest.raises(InvalidPDFError):
        UpdatePDFUseCase(
            mock_reader, mock_writer, mock_validator, mock_extractor
        ).execute("pdf-1", pdf_file)

    mock_writer.update.assert_not_called()


# --- GetPDFByIdUseCase -----------------------------------------------------

def test_get_by_id_camino_feliz_devuelve_el_read_model(mock_reader):
    doc = {"id": "pdf-1", "name": "doc.pdf", "text": "contenido", "checksum": CHECKSUM}
    mock_reader.find_by_id.return_value = doc

    result = GetPDFByIdUseCase(mock_reader).execute("pdf-1")

    mock_reader.find_by_id.assert_called_once_with("pdf-1")
    assert result == doc


def test_get_by_id_inexistente_da_not_found(mock_reader):
    mock_reader.find_by_id.return_value = None

    with pytest.raises(PDFNotFoundError):
        GetPDFByIdUseCase(mock_reader).execute("pdf-no-existe")


# --- ListPDFsUseCase -------------------------------------------------------

def test_list_devuelve_los_read_models_del_puerto(mock_reader):
    docs = [{"id": "1", "name": "a.pdf", "text": "t", "checksum": "x"}]
    mock_reader.find_all.return_value = docs

    result = ListPDFsUseCase(mock_reader).execute()

    mock_reader.find_all.assert_called_once_with()
    assert result == docs


# --- DeletePDFUseCase ------------------------------------------------------

def test_delete_camino_feliz(mock_writer):
    mock_writer.delete.return_value = True

    DeletePDFUseCase(mock_writer).execute("pdf-1")

    mock_writer.delete.assert_called_once_with("pdf-1")


def test_delete_inexistente_da_not_found(mock_writer):
    mock_writer.delete.return_value = False

    with pytest.raises(PDFNotFoundError):
        DeletePDFUseCase(mock_writer).execute("pdf-1")
