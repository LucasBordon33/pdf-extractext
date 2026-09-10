import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile
from controllers.pdf_controller import PDFController


class TestPDFController(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_service = MagicMock()
        self.mock_service.pdf_repository.get_pdfs.return_value = [
            {"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}
        ]
        self.mock_service.pdf_repository.get_pdf_by_id.return_value = None
        self.mock_service.pdf_repository.delete_pdf.return_value = {
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
            return_value={
                "status": "success",
                "id": "123",
                "filename": "nuevo.pdf",
                "checksum": "def",
                "message": "PDF actualizado correctamente",
            }
        )
        self.mock_validator = MagicMock()
        self.mock_validator._validate_is_pdf = AsyncMock(return_value="")
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
        self.mock_service.pdf_repository.get_pdf_by_id.return_value = None
        mock_file = MagicMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=b"%PDF-1.4 test content")
        with self.assertRaises(Exception):
            await self.controller.update_existing_pdf("fake_id", mock_file)


if __name__ == "__main__":
    unittest.main()
