import importlib
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from controllers.pdf_controller import PDFController
from services.pdf_service import PDFService
from config.exceptions import PDFNotFoundException


class FakeRepository:
    """Repositorio en memoria que aísla los tests del router de MongoDB."""

    def __init__(self):
        self._pdfs = [
            {"id": "1", "name": "test.pdf", "checksum": "abc", "text": "hola"}
        ]

    def get_pdfs(self):
        return [dict(pdf) for pdf in self._pdfs]

    def find_by_checksum(self, checksum):
        for pdf in self._pdfs:
            if pdf["checksum"] == checksum:
                return dict(pdf)
        return None

    def delete_pdf(self, pdf_id):
        for pdf in self._pdfs:
            if pdf["id"] == pdf_id:
                self._pdfs.remove(pdf)
                return {
                    "status": "success",
                    "id": pdf_id,
                    "message": "PDF eliminado correctamente",
                }
        raise PDFNotFoundException(f"PDF con id {pdf_id} no encontrado")


class TestPDFRouter(unittest.TestCase):
    def setUp(self):
        self.fake_repository = FakeRepository()
        controller = PDFController(
            pdf_service=PDFService(repository=self.fake_repository)
        )

        # El router instancia PDFController() internamente; se inyecta el
        # controller cableado con el FakeRepository en su lugar.
        patcher = patch(
            "routers.pdf_router.PDFController", return_value=controller
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Recargar `main` reconstruye la app y el router con el controller
        # inyectado en este test (el import queda cacheado entre tests).
        import main

        importlib.reload(main)
        self.addCleanup(importlib.reload, main)

        self.client = TestClient(main.app)

    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_get_pdfs(self):
        response = self.client.get("/api/v1/pdfs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["data"][0]["filename"], "test.pdf")

    def test_delete_pdf(self):
        response = self.client.delete("/api/v1/pdfs/1")
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(PDFNotFoundException):
            self.fake_repository.delete_pdf("1")


if __name__ == "__main__":
    unittest.main()
