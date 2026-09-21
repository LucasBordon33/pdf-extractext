import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile, HTTPException 
from controllers.pdf_controller import PDFController
from config.exceptions import (
    PDFNotFoundException,
    PDFRejectedException,
    PDFNotValidException,
)



class TestPDFController(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_service = MagicMock()
        self.mock_service.repository.get_pdfs.return_value = [
            {"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}
        ]
        self.mock_service.repository.delete_pdf.return_value = {
            "status": "success",
            "id": "123",
            "message": "PDF eliminado correctamente",
        }
        self.mock_service.upload_pdf = AsyncMock(
            return_value={
                "status": "success",
                "id": "pdf_id_123",
                "filename": "test.pdf",
                "checksum": "abc123",
                "message": "PDF subido correctamente",
            }
        )
        self.mock_service.update_pdf = AsyncMock(
        side_effect=PDFNotFoundException("PDF no encontrado")
        )
        self.mock_validator = AsyncMock()
        self.mock_validator.validate_is_pdf = AsyncMock()
        self.controller = PDFController(
            pdf_service=self.mock_service,
            pdf_validator=self.mock_validator,
        )

    async def test_upload_pdf(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"%PDF-1.4 test content")

        result = await self.controller.upload_pdf(mock_file)
        self.assertIn("id", result)
        self.assertEqual(result["filename"], "test.pdf")

    def test_get_all_pdfs(self):
        result = self.controller.get_all_pdfs()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["data"][0]["filename"], "test.pdf")

    async def test_update_existing_pdf_not_found(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"%PDF-1.4 test content")
        with self.assertRaises(HTTPException):
            await self.controller.update_existing_pdf("fake_id", mock_file)


if __name__ == "__main__":
    unittest.main()
