from unittest.mock import MagicMock, patch

import pytest

from services.pdf_service import PDFService


@pytest.fixture()
def mock_repo():
    return MagicMock()


@pytest.fixture()
def service(mock_repo):
    return PDFService(repository=mock_repo)


def test_pdf_simple(service):
    mock_reader_instance = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Hola mundo"
    mock_reader_instance.pages = [mock_page]

    with patch("services.pdf_service.PdfReader", return_value=mock_reader_instance):
        texto = service._extract_text_from_pdf_stream(b"%PDF-1.4 fake pdf content")

    assert "Hola mundo" in texto


def test_pdf_vacio(service):
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = []

    with patch("services.pdf_service.PdfReader", return_value=mock_reader_instance):
        texto = service._extract_text_from_pdf_stream(b"%PDF-1.4 fake pdf content")

    assert texto == ""


def test_pdf_invalido(service):
    with patch("services.pdf_service.PdfReader", side_effect=Exception("Invalid PDF")):
        with pytest.raises(ValueError, match="No se pudo leer el archivo como PDF"):
            service._extract_text_from_pdf_stream(b"Este es un texto plano, no un PDF")


def test_is_duplicate(service, mock_repo):
    mock_repo.find_by_checksum.return_value = {"checksum": "abc123"}
    assert service.is_duplicate("abc123") is True

    mock_repo.find_by_checksum.return_value = None
    assert service.is_duplicate("xyz") is False
