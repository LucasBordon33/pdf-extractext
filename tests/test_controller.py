from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from controllers.pdf_controller import PDFController
from config.exceptions import PDFNotFoundException


@pytest.fixture()
def mock_service():
    service = MagicMock()
    service.repository.get_pdfs.return_value = [
        {"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}
    ]
    service.repository.delete_pdf.return_value = {
        "status": "success",
        "id": "123",
        "message": "PDF eliminado correctamente",
    }
    service.upload_pdf = AsyncMock(
        return_value={
            "status": "success",
            "id": "pdf_id_123",
            "filename": "test.pdf",
            "checksum": "abc123",
            "message": "PDF subido correctamente",
        }
    )
    service.update_pdf = AsyncMock(
        side_effect=PDFNotFoundException("PDF no encontrado")
    )
    return service


@pytest.fixture()
def mock_validator():
    validator = AsyncMock()
    validator.validate_is_pdf = AsyncMock()
    return validator


@pytest.fixture()
def controller(mock_service, mock_validator):
    return PDFController(pdf_service=mock_service, pdf_validator=mock_validator)


@pytest.fixture()
def mock_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test.pdf"
    file.read = AsyncMock(return_value=b"%PDF-1.4 test content")
    return file


async def test_upload_pdf(controller, mock_file):
    result = await controller.upload_pdf(mock_file)
    assert "id" in result
    assert result["filename"] == "test.pdf"


def test_get_all_pdfs(controller):
    result = controller.get_all_pdfs()
    assert isinstance(result, dict)
    assert result["count"] == 1
    assert result["data"][0]["filename"] == "test.pdf"


async def test_update_existing_pdf_not_found(controller, mock_file):
    with pytest.raises(HTTPException):
        await controller.update_existing_pdf("fake_id", mock_file)
