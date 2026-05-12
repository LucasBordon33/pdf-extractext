import unittest
from fastapi.testclient import TestClient
from main import app


class TestPDFCrud(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_1_create_pdf(self):
        payload = {"name": "Guía de Ingeniería", "text": "Contenido de sucesiones..."}
        response = self.client.post("/api/v1/pdfs", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["msg"], "Creado exitosamente")

    def test_2_get_all_pdfs(self):
        response = self.client.get("/api/v1/pdfs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_3_update_pdf_not_found(self):
        payload = {"name": "Editado", "text": "Nuevo texto"}
        response = self.client.put(
            "/api/v1/pdfs/000000000000000000000000", json=payload
        )
        self.assertEqual(response.status_code, 404)

    def test_4_delete_pdf_success(self):
        new_pdf = self.client.post(
            "/api/v1/pdfs", json={"name": "Temp", "text": "Temp"}
        ).json()
        pdf_id = new_pdf["id"]

        response = self.client.delete(f"/api/v1/pdfs/{pdf_id}")
        self.assertEqual(response.status_code, 204)


if __name__ == "__main__":
    unittest.main()
