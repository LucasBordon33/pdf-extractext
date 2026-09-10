import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, UploadFile

class TestPDFRouter(unittest.TestCase):
    def setUp(self):
        mock_controller = MagicMock()
        mock_controller.get_all_pdfs.return_value = {
            "status": "success",
            "count": 1,
            "data": [
                {
                    "id": "1",
                    "filename": "test.pdf",
                    "checksum": "abc",
                    "text_preview": "hola",
                }
            ],
            "message": "Lista de PDFs obtenida correctamente",
        }
        mock_controller.upload_pdf = MagicMock(
            return_value={
                "status": "success",
                "id": "123",
                "filename": "test.pdf",
                "checksum": "abc",
                "message": "PDF subido correctamente",
            }
        )
        mock_controller.delete_existing_pdf = MagicMock(
            return_value={
                "status": "success",
                "id": "123",
                "message": "PDF eliminado correctamente",
            }
        )

        patcher = patch(
            "routers.pdf_router.PDFController", return_value=mock_controller
        )
        self.mock_controller_class = patcher.start()
        self.addCleanup(patcher.stop)

        from main import app
        from fastapi.testclient import TestClient

        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_get_pdfs(self):
        response = self.client.get("/api/v1/pdfs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
